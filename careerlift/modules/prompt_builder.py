"""
CareerLift AI — Prompt Builder Module
Constructs optimised prompts for each interview prep scenario.
"""

from typing import Dict, Any
from .agent_instructions import AGENT_INSTRUCTIONS


def _difficulty_context(experience: str) -> str:
    levels = AGENT_INSTRUCTIONS["difficulty_levels"]
    return levels.get(experience.lower(), levels["mid"])


def build_question_prompt(role: str, experience: str, company: str, q_type: str, count: int = 5) -> str:
    difficulty = _difficulty_context(experience)
    company_ctx = f" specifically for {company}" if company and company != "General (Any Company)" else ""
    return (
        f"Generate {count} {q_type} interview questions for a {experience}-level {role} candidate{company_ctx}.\n\n"
        f"Difficulty guidance: {difficulty}\n\n"
        f"For each question provide:\n"
        f"1. The question\n"
        f"2. A comprehensive model answer\n"
        f"3. Key interview tips\n\n"
        f"Format each as:\n"
        f"### Question [N]\n**Q:** [question]\n\n**Model Answer:** [answer]\n\n**💡 Tips:** [tips]\n\n---\n"
    )


def build_resume_analysis_prompt(resume_text: str, role: str, experience: str) -> str:
    resume_snippet = resume_text[:3000] if len(resume_text) > 3000 else resume_text
    return (
        f"Analyse the following resume for a {experience}-level {role} candidate.\n\n"
        f"Provide:\n"
        f"1. **ATS Score** (0-100) with justification\n"
        f"2. **Strengths** — what the resume does well\n"
        f"3. **Weaknesses** — specific gaps or issues\n"
        f"4. **Recommended Improvements** — concrete rewrites or additions\n"
        f"5. **Missing Keywords** — important {role} keywords for ATS\n"
        f"6. **Top 3 Action Items** — highest priority fixes\n\n"
        f"Resume Content:\n---\n{resume_snippet}\n---"
    )


def build_mock_question_prompt(role: str, experience: str, company: str, q_type: str, q_number: int) -> str:
    difficulty = _difficulty_context(experience)
    company_ctx = f" at {company}" if company and company != "General (Any Company)" else ""
    return (
        f"You are conducting a {q_type} interview{company_ctx} for a {experience}-level {role} position.\n"
        f"Generate interview question #{q_number}.\n"
        f"Difficulty: {difficulty}\n\n"
        f"Respond with ONLY the question itself — no preamble, no answer.\n"
        f"Make it specific, realistic, and appropriately challenging."
    )


def build_evaluation_prompt(question: str, answer: str, role: str, experience: str, q_type: str) -> str:
    rubric = AGENT_INSTRUCTIONS["mock_interview"]["scoring_rubric"]
    rubric_text = "\n".join([f"- **{k.title()}**: {v}" for k, v in rubric.items()])
    return (
        f"Evaluate the following interview answer for a {experience}-level {role} candidate.\n\n"
        f"**Interview Type:** {q_type}\n\n"
        f"**Question:** {question}\n\n"
        f"**Candidate's Answer:** {answer}\n\n"
        f"**Scoring Rubric:**\n{rubric_text}\n\n"
        f"Provide:\n"
        f"1. **Overall Score: X/100** (strictly follow rubric)\n"
        f"2. **Score Breakdown** (table with each criterion and score)\n"
        f"3. **✅ Strengths** (2-3 specific positives)\n"
        f"4. **🔧 Areas for Improvement** (2-3 specific, actionable suggestions)\n"
        f"5. **💡 Model Answer Hint** (brief outline of an ideal answer)\n"
        f"6. **Encouragement** (one motivating sentence)\n"
    )


def build_roadmap_prompt(role: str, experience: str, company: str, weeks: int = 4) -> str:
    difficulty = _difficulty_context(experience)
    company_ctx = f" targeting {company}" if company and company != "General (Any Company)" else ""
    return (
        f"Create a detailed {weeks}-week interview preparation roadmap for a {experience}-level {role} candidate{company_ctx}.\n\n"
        f"Level guidance: {difficulty}\n\n"
        f"For each week include:\n"
        f"- **Focus Area** (what to study)\n"
        f"- **Daily Tasks** (specific actionable tasks)\n"
        f"- **Resources** (books, websites, practice platforms)\n"
        f"- **Milestone** (what to have achieved by week end)\n\n"
        f"End with a **Pre-Interview Checklist** and **Day-of-Interview Tips**."
    )


def build_tip_prompt(role: str, experience: str, tip_type: str) -> str:
    return (
        f"Provide 10 expert {tip_type} tips for a {experience}-level {role} candidate.\n\n"
        f"Format each tip as:\n"
        f"**Tip [N]: [Title]**\n[Detailed explanation with example]\n\n"
        f"Make tips specific, actionable, and relevant to the {role} role."
    )


def build_chat_prompt(user_message: str, profile: Dict[str, Any], history_context: str) -> str:
    role       = profile.get("role", "Software Engineer")
    experience = profile.get("experience", "mid")
    company    = profile.get("company", "")
    company_ctx = f" targeting {company}" if company else ""

    context_block = f"\n\nConversation context:\n{history_context}\n" if history_context else ""

    return (
        f"User profile: {experience}-level {role} candidate{company_ctx}.\n"
        f"{context_block}\n"
        f"User message: {user_message}\n\n"
        f"Respond helpfully as CareerLift Coach. Stay focused on interview preparation."
    )
