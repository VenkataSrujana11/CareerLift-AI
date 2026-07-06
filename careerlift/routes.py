"""
CareerLift AI — Flask Routes
"""

import os
import uuid
from flask import Blueprint, render_template, request, jsonify, session, current_app
from werkzeug.utils import secure_filename

from .modules.agent_instructions import AGENT_INSTRUCTIONS
from .modules.watsonx_client import generate_response
from .modules.rag_retrieval import augmented_prompt
from .modules.resume_parser import allowed_file, parse_resume
from .modules.prompt_builder import (
    build_question_prompt,
    build_resume_analysis_prompt,
    build_mock_question_prompt,
    build_evaluation_prompt,
    build_roadmap_prompt,
    build_tip_prompt,
    build_chat_prompt,
)
from .modules.progress_tracker import (
    init_session,
    get_profile,
    update_profile,
    add_chat_message,
    get_chat_history,
    clear_chat,
    record_activity,
    get_dashboard_data,
)

main_bp = Blueprint("main", __name__)


@main_bp.before_request
def ensure_session():
    init_session(session)


# ============================================================
# HOME PAGE
# ============================================================

@main_bp.route("/")
def index():
    return render_template("index.html", 
                           app_name=current_app.config["APP_NAME"],
                           tagline=current_app.config["APP_TAGLINE"])


# ============================================================
# CHAT INTERFACE
# ============================================================

@main_bp.route("/chat")
def chat():
    profile = get_profile(session)
    welcome = AGENT_INSTRUCTIONS["welcome_message"]
    return render_template("chat.html", profile=profile, app_name=current_app.config["APP_NAME"],
                           welcome_message=welcome)


@main_bp.route("/api/chat", methods=["POST"])
def api_chat():
    data    = request.get_json()
    message = data.get("message", "").strip()
    
    if not message:
        return jsonify({"error": "Empty message"}), 400
    
    profile = get_profile(session)
    add_chat_message(session, "user", message)
    
    # Build context from last 5 messages
    history = get_chat_history(session)[-6:-1]
    history_ctx = "\n".join([f"{h['role']}: {h['content']}" for h in history])
    
    # Use RAG + prompt builder
    user_prompt = build_chat_prompt(message, profile, history_ctx)
    sys_prompt  = AGENT_INSTRUCTIONS["system_prompt"]
    aug_sys, aug_user = augmented_prompt(user_prompt, sys_prompt, top_k=5)
    
    response = generate_response(aug_user, aug_sys, max_tokens=1500)
    add_chat_message(session, "assistant", response)
    record_activity(session, "chat_interaction")
    
    return jsonify({"response": response})


# ============================================================
# GENERATE QUESTIONS
# ============================================================

@main_bp.route("/generate")
def generate():
    profile = get_profile(session)
    return render_template("generate.html", 
                           profile=profile,
                           roles=AGENT_INSTRUCTIONS["supported_roles"],
                           companies=AGENT_INSTRUCTIONS["supported_companies"],
                           types=list(AGENT_INSTRUCTIONS["interview_types"].keys()),
                           app_name=current_app.config["APP_NAME"])


@main_bp.route("/api/generate-questions", methods=["POST"])
def api_generate_questions():
    data = request.get_json()
    role       = data.get("role", "Software Engineer")
    experience = data.get("experience", "mid")
    company    = data.get("company", "General (Any Company)")
    q_type     = data.get("type", "technical")
    count      = int(data.get("count", 5))
    
    update_profile(session, role=role, experience=experience, company=company)
    
    prompt     = build_question_prompt(role, experience, company, q_type, count)
    sys_prompt = AGENT_INSTRUCTIONS["system_prompt"]
    aug_sys, aug_user = augmented_prompt(prompt, sys_prompt, top_k=5)
    
    response = generate_response(aug_user, aug_sys, max_tokens=2000)
    record_activity(session, "question_practiced", detail=f"{q_type} questions for {role}")
    
    return jsonify({"questions": response})


# ============================================================
# RESUME UPLOAD & ANALYSIS
# ============================================================

@main_bp.route("/resume")
def resume():
    return render_template("resume.html", app_name=current_app.config["APP_NAME"])


@main_bp.route("/api/upload-resume", methods=["POST"])
def api_upload_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported format. Use PDF or DOCX."}), 400
    
    filename  = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    filepath  = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    
    parsed = parse_resume(filepath)
    if "error" in parsed:
        return jsonify({"error": parsed["error"]}), 500
    
    update_profile(session, resume_text=parsed["raw_text"])
    
    return jsonify({
        "message": "Resume uploaded successfully",
        "parsed":  parsed,
    })


@main_bp.route("/api/analyze-resume", methods=["POST"])
def api_analyze_resume():
    data = request.get_json()
    resume_text = data.get("resume_text", session.get("profile", {}).get("resume_text", ""))
    role        = data.get("role", get_profile(session).get("role", "Software Engineer"))
    experience  = data.get("experience", get_profile(session).get("experience", "mid"))
    
    if not resume_text or len(resume_text) < 50:
        return jsonify({"error": "No resume content available. Upload a resume first."}), 400
    
    prompt     = build_resume_analysis_prompt(resume_text, role, experience)
    sys_prompt = AGENT_INSTRUCTIONS["system_prompt"]
    aug_sys, aug_user = augmented_prompt(prompt, sys_prompt, top_k=3)
    
    analysis = generate_response(aug_user, aug_sys, max_tokens=2000)
    record_activity(session, "resume_analyzed", detail=f"Resume for {role}")
    
    return jsonify({"analysis": analysis})


# ============================================================
# MOCK INTERVIEW
# ============================================================

@main_bp.route("/mock")
def mock():
    profile = get_profile(session)
    return render_template("mock.html", 
                           profile=profile,
                           roles=AGENT_INSTRUCTIONS["supported_roles"],
                           companies=AGENT_INSTRUCTIONS["supported_companies"],
                           types=list(AGENT_INSTRUCTIONS["interview_types"].keys()),
                           app_name=current_app.config["APP_NAME"])


@main_bp.route("/api/mock/start", methods=["POST"])
def api_mock_start():
    data = request.get_json()
    role       = data.get("role", "Software Engineer")
    experience = data.get("experience", "mid")
    company    = data.get("company", "General (Any Company)")
    q_type     = data.get("type", "technical")
    count      = int(data.get("count", 5))
    
    update_profile(session, role=role, experience=experience, company=company)
    
    session["mock_state"] = {
        "active":    True,
        "q_index":   0,
        "q_type":    q_type,
        "questions": [],
        "answers":   [],
        "scores":    [],
        "count":     count,
    }
    
    record_activity(session, "session_started", detail=f"Mock {q_type} interview")
    return jsonify({"message": "Mock interview started", "total_questions": count})


@main_bp.route("/api/mock/next-question", methods=["GET"])
def api_mock_next_question():
    mock = session.get("mock_state", {})
    if not mock.get("active"):
        return jsonify({"error": "No active mock interview"}), 400
    
    q_idx  = mock["q_index"]
    total  = mock["count"]
    
    if q_idx >= total:
        return jsonify({"done": True, "message": "Mock interview complete!"})
    
    profile    = get_profile(session)
    q_type     = mock["q_type"]
    prompt     = build_mock_question_prompt(profile["role"], profile["experience"], profile["company"], q_type, q_idx + 1)
    sys_prompt = AGENT_INSTRUCTIONS["system_prompt"]
    
    question = generate_response(prompt, sys_prompt, max_tokens=300)
    mock["questions"].append(question)
    session["mock_state"] = mock
    
    return jsonify({"question": question, "number": q_idx + 1, "total": total})


@main_bp.route("/api/mock/submit-answer", methods=["POST"])
def api_mock_submit_answer():
    data   = request.get_json()
    answer = data.get("answer", "").strip()
    
    mock = session.get("mock_state", {})
    if not mock.get("active"):
        return jsonify({"error": "No active mock interview"}), 400
    
    q_idx    = mock["q_index"]
    question = mock["questions"][q_idx] if q_idx < len(mock["questions"]) else "N/A"
    profile  = get_profile(session)
    
    prompt     = build_evaluation_prompt(question, answer, profile["role"], profile["experience"], mock["q_type"])
    sys_prompt = AGENT_INSTRUCTIONS["system_prompt"]
    
    evaluation = generate_response(prompt, sys_prompt, max_tokens=1500)
    
    # Extract score (naive regex)
    import re
    score_match = re.search(r"(\d+)\s*/\s*100", evaluation)
    score = int(score_match.group(1)) if score_match else 0
    
    mock["answers"].append(answer)
    mock["scores"].append(score)
    mock["q_index"] += 1
    session["mock_state"] = mock
    
    record_activity(session, "question_practiced", detail=f"Mock Q{q_idx+1}", score=score)
    
    if mock["q_index"] >= mock["count"]:
        mock["active"] = False
        avg = sum(mock["scores"]) / len(mock["scores"]) if mock["scores"] else 0
        record_activity(session, "mock_completed", score=int(avg))
        session["mock_state"] = mock
        return jsonify({"evaluation": evaluation, "score": score, "done": True, "avg_score": round(avg, 1)})
    
    return jsonify({"evaluation": evaluation, "score": score, "done": False})


# ============================================================
# ROADMAP & TIPS
# ============================================================

@main_bp.route("/api/roadmap", methods=["POST"])
def api_roadmap():
    data       = request.get_json()
    role       = data.get("role", get_profile(session).get("role", "Software Engineer"))
    experience = data.get("experience", get_profile(session).get("experience", "mid"))
    company    = data.get("company", get_profile(session).get("company", "General (Any Company)"))
    weeks      = int(data.get("weeks", 4))
    
    prompt     = build_roadmap_prompt(role, experience, company, weeks)
    sys_prompt = AGENT_INSTRUCTIONS["system_prompt"]
    aug_sys, aug_user = augmented_prompt(prompt, sys_prompt, top_k=3)
    
    roadmap = generate_response(aug_user, aug_sys, max_tokens=2000)
    return jsonify({"roadmap": roadmap})


@main_bp.route("/api/tips", methods=["POST"])
def api_tips():
    data       = request.get_json()
    role       = data.get("role", get_profile(session).get("role", "Software Engineer"))
    experience = data.get("experience", get_profile(session).get("experience", "mid"))
    tip_type   = data.get("type", "interview")
    
    prompt     = build_tip_prompt(role, experience, tip_type)
    sys_prompt = AGENT_INSTRUCTIONS["system_prompt"]
    aug_sys, aug_user = augmented_prompt(prompt, sys_prompt, top_k=3)
    
    tips = generate_response(aug_user, aug_sys, max_tokens=1500)
    return jsonify({"tips": tips})


# ============================================================
# DASHBOARD
# ============================================================

@main_bp.route("/dashboard")
def dashboard():
    data = get_dashboard_data(session)
    return render_template("dashboard.html", data=data, app_name=current_app.config["APP_NAME"])


@main_bp.route("/api/profile", methods=["GET", "POST"])
def api_profile():
    if request.method == "POST":
        data = request.get_json()
        update_profile(
            session,
            role       = data.get("role", ""),
            experience = data.get("experience", ""),
            company    = data.get("company", ""),
        )
        return jsonify({"message": "Profile updated"})
    return jsonify(get_profile(session))


@main_bp.route("/api/clear-chat", methods=["POST"])
def api_clear_chat():
    clear_chat(session)
    return jsonify({"message": "Chat cleared"})
