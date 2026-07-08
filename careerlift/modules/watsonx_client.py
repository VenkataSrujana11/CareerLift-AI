"""
CareerLift AI — watsonx.ai Integration Module
Handles all IBM Granite model interactions via ibm-watsonx-ai SDK.
"""

import os
from dotenv import load_dotenv

# Optional IBM watsonx.ai — import lazily so the app runs without it
try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False

load_dotenv()

class WatsonXClient:
    """Singleton wrapper for IBM watsonx.ai ModelInference."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialised = False
        return cls._instance

    def __init__(self):
        if self._initialised:
            return
        self.api_key    = os.getenv("WATSONX_API_KEY", "")
        self.project_id = os.getenv("WATSONX_PROJECT_ID", "")
        self.url        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.model_id   = os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-chat-v2")
        self.model      = None
        self._demo_mode = not (self.api_key and self.api_key != "your_ibm_cloud_api_key_here") or not WATSONX_AVAILABLE
        if not self._demo_mode:
            self._connect()
        self._initialised = True

    def _connect(self):
        try:
            credentials = Credentials(url=self.url, api_key=self.api_key)
            self.model = ModelInference(
                model_id=self.model_id,
                credentials=credentials,
                project_id=self.project_id,
                params={
                    GenParams.MAX_NEW_TOKENS: 1500,
                    GenParams.MIN_NEW_TOKENS: 10,
                    GenParams.TEMPERATURE:    0.7,
                    GenParams.TOP_P:          0.9,
                    GenParams.TOP_K:          50,
                    GenParams.REPETITION_PENALTY: 1.1,
                    GenParams.STOP_SEQUENCES: ["<|endoftext|>", "Human:", "User:"],
                },
            )
            print("[WatsonX] Connected to IBM Granite successfully.")
        except Exception as exc:
            print(f"[WatsonX] Connection error: {exc}. Running in demo mode.")
            self._demo_mode = True

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 1500) -> str:
        """Generate a response from IBM Granite."""
        if self._demo_mode:
            return self._demo_response(prompt)
        try:
            full_prompt = f"{system_prompt}\n\nHuman: {prompt}\n\nAssistant:" if system_prompt else f"Human: {prompt}\n\nAssistant:"
            response = self.model.generate_text(prompt=full_prompt)
            return response.strip() if response else "I apologise, I couldn't generate a response. Please try again."
        except Exception as exc:
            print(f"[WatsonX] Generation error: {exc}")
            return self._demo_response(prompt)

    def _demo_response(self, prompt: str) -> str:
        """Fallback demo response when credentials are not configured."""
        prompt_lower = prompt.lower()

        if any(w in prompt_lower for w in ["mock", "evaluate", "score my", "assess"]):
            return (
                "## Mock Interview Evaluation\n\n"
                "**Score: 78/100** *(Demo Mode)*\n\n"
                "### Breakdown\n"
                "| Criterion | Score |\n|---|---|\n"
                "| Clarity | 16/20 |\n| Correctness | 23/30 |\n"
                "| Depth | 16/20 |\n| Communication | 12/15 |\n| Examples | 11/15 |\n\n"
                "### ✅ Strengths\n- Clear problem decomposition\n- Good use of examples\n\n"
                "### 🔧 Improvements\n- Mention time/space complexity explicitly\n- Use the STAR format more rigorously\n\n"
                "*📌 Demo mode — connect IBM watsonx.ai credentials for real AI evaluation.*"
            )
        if any(w in prompt_lower for w in ["resume", "cv", "ats"]):
            return (
                "## Resume Analysis *(Demo Mode)*\n\n"
                "### ATS Score: 72/100\n\n"
                "**✅ Strengths**\n- Clear work experience section\n- Good use of action verbs\n\n"
                "**🔧 Recommendations**\n"
                "- Add quantified achievements (e.g., 'Improved performance by 30%')\n"
                "- Include relevant keywords: Python, REST API, CI/CD\n"
                "- Strengthen professional summary\n\n"
                "*📌 Demo mode — connect IBM watsonx.ai credentials for full AI analysis.*"
            )
        if any(w in prompt_lower for w in ["roadmap", "plan", "prepare", "week"]):
            return (
                "## 4-Week Interview Preparation Roadmap *(Demo Mode)*\n\n"
                "**Week 1 — Foundations**\n- Review core data structures\n- Practice 15 LeetCode Easy problems\n- Update your resume\n\n"
                "**Week 2 — Intermediate Practice**\n- System design basics\n- 15 LeetCode Medium problems\n- Behavioural question bank\n\n"
                "**Week 3 — Mock Interviews**\n- Full mock interviews daily\n- Company-specific research\n- Refine answers with STAR method\n\n"
                "**Week 4 — Final Polish**\n- Timed practice sessions\n- Research company culture\n- Prepare smart questions to ask\n\n"
                "*📌 Demo mode — connect IBM watsonx.ai credentials for personalised roadmaps.*"
            )
        return (
            "## CareerLift AI *(Demo Mode)*\n\n"
            "I'm your AI interview coach powered by IBM Granite! 🚀\n\n"
            "**Demo mode is active** — add your IBM watsonx.ai credentials to `.env` to unlock full AI capabilities.\n\n"
            "In full mode, I can:\n"
            "- Generate personalised interview questions\n"
            "- Evaluate your answers with detailed scoring\n"
            "- Analyse your resume for ATS optimisation\n"
            "- Create custom preparation roadmaps\n"
            "- Conduct interactive mock interviews\n\n"
            "*Tell me your target role and I'll prepare relevant practice questions!*"
        )


# Module-level singleton
_client = None


def get_watsonx_client() -> WatsonXClient:
    global _client
    if _client is None:
        _client = WatsonXClient()
    return _client

def generate_response(prompt: str, system_prompt: str = "", max_tokens: int = 1500) -> str:
    return get_watsonx_client().generate(prompt, system_prompt, max_tokens)
