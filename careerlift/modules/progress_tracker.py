"""
CareerLift AI — Progress Tracker Module
Manages session-based interview progress and statistics.
"""

from datetime import datetime
from typing import Dict, Any, List


def init_session(session: dict):
    """Initialise all session keys for a new user."""
    if "careerlift_init" not in session:
        session["careerlift_init"] = True
        session["chat_history"]    = []
        session["mock_state"]      = {"active": False, "q_index": 0, "questions": [], "answers": [], "scores": []}
        session["profile"]         = {"role": "", "experience": "mid", "company": "", "resume_text": ""}
        session["progress"]        = {
            "sessions_completed": 0,
            "questions_practiced": 0,
            "mock_interviews": 0,
            "avg_score": 0,
            "total_score_sum": 0,
            "badges": [],
            "activity_log": [],
        }


def get_profile(session: dict) -> Dict[str, str]:
    return session.get("profile", {"role": "", "experience": "mid", "company": "", "resume_text": ""})


def update_profile(session: dict, role: str = "", experience: str = "", company: str = "", resume_text: str = ""):
    if "profile" not in session:
        session["profile"] = {}
    if role:        session["profile"]["role"]        = role
    if experience:  session["profile"]["experience"]  = experience
    if company:     session["profile"]["company"]     = company
    if resume_text: session["profile"]["resume_text"] = resume_text


def add_chat_message(session: dict, role: str, content: str):
    """Append a message to the chat history (max 50 messages kept)."""
    if "chat_history" not in session:
        session["chat_history"] = []
    session["chat_history"].append({
        "role":      role,
        "content":   content,
        "timestamp": datetime.now().strftime("%H:%M"),
    })
    if len(session["chat_history"]) > 50:
        session["chat_history"] = session["chat_history"][-50:]


def get_chat_history(session: dict) -> List[Dict]:
    return session.get("chat_history", [])


def clear_chat(session: dict):
    session["chat_history"] = []


def record_activity(session: dict, activity_type: str, detail: str = "", score: int = 0):
    """Log a user activity for the dashboard."""
    if "progress" not in session:
        init_session(session)
    progress = session["progress"]
    progress["activity_log"].append({
        "type":      activity_type,
        "detail":    detail,
        "score":     score,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    progress["activity_log"] = progress["activity_log"][-20:]  # keep last 20

    if activity_type == "question_practiced":
        progress["questions_practiced"] += 1
    elif activity_type == "mock_completed":
        progress["mock_interviews"] += 1
        progress["sessions_completed"] += 1
        if score > 0:
            progress["total_score_sum"] += score
            total_scored = sum(1 for a in progress["activity_log"] if a.get("score", 0) > 0)
            progress["avg_score"] = round(progress["total_score_sum"] / max(total_scored, 1))
    elif activity_type == "session_started":
        progress["sessions_completed"] += 1

    _award_badges(session)


def _award_badges(session: dict):
    progress = session["progress"]
    badges   = set(progress.get("badges", []))
    q = progress["questions_practiced"]
    m = progress["mock_interviews"]
    s = progress["avg_score"]

    if q >= 1:   badges.add("🚀 First Question")
    if q >= 10:  badges.add("📚 Consistent Learner")
    if q >= 50:  badges.add("🏆 Question Master")
    if m >= 1:   badges.add("🎤 Mock Debut")
    if m >= 5:   badges.add("🎯 Mock Pro")
    if s >= 80:  badges.add("⭐ High Scorer")
    if s >= 90:  badges.add("💎 Elite Candidate")

    progress["badges"] = list(badges)


def get_dashboard_data(session: dict) -> Dict[str, Any]:
    """Return all data needed to render the dashboard."""
    progress = session.get("progress", {})
    profile  = session.get("profile", {})
    history  = session.get("chat_history", [])
    return {
        "profile":  profile,
        "stats": {
            "sessions":  progress.get("sessions_completed", 0),
            "questions": progress.get("questions_practiced", 0),
            "mocks":     progress.get("mock_interviews", 0),
            "avg_score": progress.get("avg_score", 0),
        },
        "badges":       progress.get("badges", []),
        "activity_log": progress.get("activity_log", [])[-10:],
        "chat_count":   len(history),
        "readiness_score": _compute_readiness(progress),
    }


def _compute_readiness(progress: dict) -> int:
    """Simple readiness heuristic (0-100)."""
    score = 0
    score += min(progress.get("questions_practiced", 0) * 2, 40)
    score += min(progress.get("mock_interviews", 0)     * 10, 30)
    score += min(progress.get("avg_score", 0) // 3,          30)
    return min(score, 100)
