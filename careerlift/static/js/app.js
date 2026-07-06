/**
 * CareerLift AI — Main Application JavaScript
 * Organised as a module namespace: window.CareerLift
 */

(function (CL) {
  "use strict";

  /* ----------------------------------------------------------
     MARKED.JS CONFIG (Markdown rendering)
  ---------------------------------------------------------- */
  if (typeof marked !== "undefined") {
    marked.setOptions({
      breaks: true,
      gfm: true,
      highlight: function (code, lang) {
        if (typeof hljs !== "undefined" && lang && hljs.getLanguage(lang)) {
          return hljs.highlight(code, { language: lang }).value;
        }
        return typeof hljs !== "undefined" ? hljs.highlightAuto(code).value : code;
      },
    });
  }

  function renderMarkdown(text) {
    if (typeof marked === "undefined") return text;
    try { return marked.parse(text); } catch (e) { return text; }
  }

  /* ----------------------------------------------------------
     THEME MANAGER
  ---------------------------------------------------------- */
  CL.theme = {
    KEY: "cl-theme",
    init() {
      const saved = localStorage.getItem(this.KEY) || "dark";
      this.apply(saved);
      const btn = document.getElementById("themeToggle");
      if (btn) btn.addEventListener("click", () => this.toggle());
    },
    apply(theme) {
      document.documentElement.setAttribute("data-theme", theme);
      localStorage.setItem(this.KEY, theme);
      const icon = document.getElementById("themeIcon");
      if (icon) {
        icon.className = theme === "dark" ? "bi bi-moon-fill" : "bi bi-sun-fill";
      }
      // Highlight.js theme swap
      const hlTheme = document.getElementById("hljs-theme");
      if (hlTheme) {
        hlTheme.href = theme === "dark"
          ? "https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github-dark.min.css"
          : "https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github.min.css";
      }
    },
    toggle() {
      const cur = document.documentElement.getAttribute("data-theme") || "dark";
      this.apply(cur === "dark" ? "light" : "dark");
    },
  };

  /* ----------------------------------------------------------
     TOAST NOTIFICATIONS
  ---------------------------------------------------------- */
  CL.toast = {
    show(msg, type = "info", duration = 3000) {
      const colours = { info: "#3b82f6", success: "#3fb950", error: "#f85149", warn: "#e3b341" };
      let container = document.getElementById("cl-toast-container");
      if (!container) {
        container = document.createElement("div");
        container.id = "cl-toast-container";
        Object.assign(container.style, {
          position: "fixed", bottom: "24px", right: "24px", zIndex: "9999",
          display: "flex", flexDirection: "column", gap: "8px",
        });
        document.body.appendChild(container);
      }
      const toast = document.createElement("div");
      toast.style.cssText = `
        background: var(--cl-bg-surface);
        border: 1px solid ${colours[type] || colours.info};
        border-left: 3px solid ${colours[type] || colours.info};
        border-radius: 8px; padding: 12px 16px;
        font-size: 13.5px; color: var(--cl-text);
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        min-width: 240px; max-width: 340px;
        animation: fadeInUp 0.2s ease;
      `;
      toast.textContent = msg;
      container.appendChild(toast);
      setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.3s";
        setTimeout(() => toast.remove(), 300);
      }, duration);
    },
  };

  /* ----------------------------------------------------------
     API HELPERS
  ---------------------------------------------------------- */
  CL.api = {
    async post(url, data) {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || res.statusText);
      }
      return res.json();
    },
    async get(url) {
      const res = await fetch(url);
      if (!res.ok) throw new Error(res.statusText);
      return res.json();
    },
  };

  /* ----------------------------------------------------------
     CHAT MODULE
  ---------------------------------------------------------- */
  CL.chat = {
    messages: [],
    isThinking: false,

    init(welcomeMsg) {
      this.messagesEl   = document.getElementById("chatMessages");
      this.inputEl      = document.getElementById("chatInput");
      this.sendBtn      = document.getElementById("sendBtn");
      this.typingEl     = document.getElementById("typingIndicator");
      this.charCountEl  = document.getElementById("charCount");
      this.clearBtn     = document.getElementById("clearChatBtn");

      if (!this.messagesEl) return;

      // Show welcome message
      const welcome = welcomeMsg || "👋 Welcome! I'm your CareerLift AI Coach. How can I help you prepare for your interview today?";
      this.addMessage("assistant", welcome, false);

      // Send button
      this.sendBtn.addEventListener("click", () => this.send());

      // Textarea: auto-resize + Enter to send
      this.inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.send();
        }
      });
      this.inputEl.addEventListener("input", () => {
        this.autoResize();
        this.charCountEl.textContent = `${this.inputEl.value.length} / 2000`;
      });

      // Quick action buttons
      document.querySelectorAll(".cl-quick-btn[data-prompt]").forEach((btn) => {
        btn.addEventListener("click", () => {
          this.inputEl.value = btn.dataset.prompt;
          this.autoResize();
          this.send();
        });
      });

      // Clear chat
      if (this.clearBtn) {
        this.clearBtn.addEventListener("click", async () => {
          await CL.api.post("/api/clear-chat", {});
          this.messagesEl.innerHTML = "";
          this.addMessage("assistant", welcome, false);
          CL.toast.show("Chat cleared", "info");
        });
      }

      // Profile modal save
      const saveProfileBtn = document.getElementById("saveProfileBtn");
      if (saveProfileBtn) {
        saveProfileBtn.addEventListener("click", async () => {
          const role = document.getElementById("profileRole")?.value.trim();
          const exp  = document.getElementById("profileExp")?.value;
          const company = document.getElementById("profileCompany")?.value.trim();
          await CL.api.post("/api/profile", { role, experience: exp, company });
          document.getElementById("profileDisplay").innerHTML =
            `${exp}-level ${role}${company ? " · " + company : ""}`;
          const modal = bootstrap.Modal.getInstance(document.getElementById("profileModal"));
          if (modal) modal.hide();
          CL.toast.show("Profile updated!", "success");
        });
      }
    },

    autoResize() {
      this.inputEl.style.height = "auto";
      this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 160) + "px";
    },

    addMessage(role, content, save = true) {
      const isUser = role === "user";
      const wrapper = document.createElement("div");
      wrapper.className = `cl-msg-wrapper ${isUser ? "user-msg" : ""}`;

      const avatar = document.createElement("div");
      avatar.className = `cl-msg-avatar ${isUser ? "user" : "bot"}`;
      avatar.innerHTML = isUser ? '<i class="bi bi-person-fill"></i>' : '<i class="bi bi-lightning-charge-fill"></i>';

      const msgContent = document.createElement("div");
      msgContent.className = "cl-msg-content";

      const bubble = document.createElement("div");
      bubble.className = "cl-msg-bubble";
      bubble.innerHTML = renderMarkdown(content);

      // Syntax highlighting
      if (typeof hljs !== "undefined") {
        bubble.querySelectorAll("pre code").forEach((el) => hljs.highlightElement(el));
      }

      const time = document.createElement("div");
      time.className = "cl-msg-time";
      time.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      msgContent.appendChild(bubble);
      msgContent.appendChild(time);
      wrapper.appendChild(avatar);
      wrapper.appendChild(msgContent);

      this.messagesEl.appendChild(wrapper);
      this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    },

    setThinking(active) {
      this.isThinking = active;
      const typingEl = document.getElementById("typingIndicator");
      if (typingEl) typingEl.classList.toggle("d-none", !active);
      this.sendBtn.disabled = active;
      this.inputEl.disabled = active;
      if (active) this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    },

    async send() {
      const msg = this.inputEl.value.trim();
      if (!msg || this.isThinking) return;

      this.addMessage("user", msg);
      this.inputEl.value = "";
      this.autoResize();
      this.charCountEl.textContent = "0 / 2000";
      this.setThinking(true);

      try {
        const data = await CL.api.post("/api/chat", { message: msg });
        this.addMessage("assistant", data.response);
      } catch (err) {
        this.addMessage("assistant", `⚠️ Error: ${err.message}. Please try again.`);
        CL.toast.show(err.message, "error");
      } finally {
        this.setThinking(false);
      }
    },
  };

  /* ----------------------------------------------------------
     GENERATE QUESTIONS MODULE
  ---------------------------------------------------------- */
  CL.generate = {
    selectedType: "technical",

    init() {
      const generateBtn   = document.getElementById("generateBtn");
      const questionsOut  = document.getElementById("questionsOutput");
      const genLoading    = document.getElementById("genLoading");
      const placeholder   = document.getElementById("placeholder");
      const countSlider   = document.getElementById("genCount");
      const countDisplay  = document.getElementById("countDisplay");
      const copyBtn       = document.getElementById("copyQBtn");

      if (!generateBtn) return;

      // Type button selection
      document.querySelectorAll(".cl-type-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          document.querySelectorAll(".cl-type-btn").forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          this.selectedType = btn.dataset.type;
        });
      });

      // Count slider
      if (countSlider) {
        countSlider.addEventListener("input", () => {
          countDisplay.textContent = countSlider.value;
        });
      }

      // Copy button
      if (copyBtn) {
        copyBtn.addEventListener("click", () => {
          const content = document.getElementById("questionsContent")?.innerText || "";
          navigator.clipboard.writeText(content).then(() => CL.toast.show("Copied!", "success"));
        });
      }

      generateBtn.addEventListener("click", () => this.generate());
    },

    async generate() {
      const role    = document.getElementById("genRole")?.value.trim() || "Software Engineer";
      const exp     = document.getElementById("genExp")?.value || "mid";
      const company = document.getElementById("genCompany")?.value.trim() || "";
      const count   = document.getElementById("genCount")?.value || "5";

      document.getElementById("placeholder")?.classList.add("d-none");
      document.getElementById("questionsOutput")?.classList.add("d-none");
      document.getElementById("genLoading")?.classList.remove("d-none");

      try {
        const data = await CL.api.post("/api/generate-questions", {
          role, experience: exp, company, type: this.selectedType, count: parseInt(count),
        });

        document.getElementById("genLoading")?.classList.add("d-none");
        const output = document.getElementById("questionsOutput");
        const content = document.getElementById("questionsContent");
        if (output && content) {
          content.innerHTML = renderMarkdown(data.questions);
          if (typeof hljs !== "undefined") {
            content.querySelectorAll("pre code").forEach((el) => hljs.highlightElement(el));
          }
          document.getElementById("questionsTitle").textContent =
            `${this.selectedType.replace("_", " ")} Questions — ${role}`;
          output.classList.remove("d-none");
          output.classList.add("fade-in");
        }
        CL.toast.show("Questions generated!", "success");
      } catch (err) {
        document.getElementById("genLoading")?.classList.add("d-none");
        document.getElementById("placeholder")?.classList.remove("d-none");
        CL.toast.show(err.message, "error");
      }
    },
  };

  /* ----------------------------------------------------------
     MOCK INTERVIEW MODULE
  ---------------------------------------------------------- */
  CL.mock = {
    state: { active: false, qIndex: 0, total: 0, scores: [] },

    init() {
      const startBtn = document.getElementById("startMockBtn");
      if (!startBtn) return;

      startBtn.addEventListener("click", () => this.start());
      document.getElementById("submitAnswerBtn")?.addEventListener("click", () => this.submitAnswer());
      document.getElementById("skipBtn")?.addEventListener("click", () => this.skip());
      document.getElementById("nextQuestionBtn")?.addEventListener("click", () => this.nextQuestion());
      document.getElementById("retryBtn")?.addEventListener("click", () => this.retry());
    },

    async start() {
      const role    = document.getElementById("mockRole")?.value.trim() || "Software Engineer";
      const exp     = document.getElementById("mockExp")?.value || "mid";
      const type    = document.getElementById("mockType")?.value || "technical";
      const company = document.getElementById("mockCompany")?.value.trim() || "";
      const count   = parseInt(document.getElementById("mockCount")?.value || "5");

      try {
        await CL.api.post("/api/mock/start", { role, experience: exp, type, company, count });
        this.state = { active: true, qIndex: 0, total: count, scores: [], type };

        document.getElementById("setupPanel")?.classList.add("d-none");
        document.getElementById("interviewPanel")?.classList.remove("d-none");
        document.getElementById("totalQNum").textContent = count;
        document.getElementById("mockTypeLabel").textContent = type.replace("_", " ") + " Interview";
        document.getElementById("qTypeBadge").textContent = type.replace("_", " ");

        await this.nextQuestion();
      } catch (err) {
        CL.toast.show(err.message, "error");
      }
    },

    async nextQuestion() {
      document.getElementById("evalCard")?.classList.add("d-none");
      document.getElementById("answerCard")?.classList.remove("d-none");
      document.getElementById("mockAnswer").value = "";
      document.getElementById("questionLoading")?.classList.remove("d-none");
      document.getElementById("questionText").textContent = "";

      const pct = (this.state.qIndex / this.state.total) * 100;
      document.getElementById("mockProgress").style.width = pct + "%";
      document.getElementById("currentQNum").textContent = this.state.qIndex + 1;

      try {
        const data = await CL.api.get("/api/mock/next-question");
        document.getElementById("questionLoading")?.classList.add("d-none");

        if (data.done) {
          this.showResults();
          return;
        }
        document.getElementById("questionText").innerHTML = renderMarkdown(data.question);
      } catch (err) {
        document.getElementById("questionLoading")?.classList.add("d-none");
        CL.toast.show(err.message, "error");
      }
    },

    async submitAnswer() {
      const answer = document.getElementById("mockAnswer")?.value.trim();
      if (!answer || answer.length < 5) {
        CL.toast.show("Please write at least a brief answer.", "warn");
        return;
      }

      document.getElementById("answerCard")?.classList.add("d-none");
      document.getElementById("evalCard")?.classList.remove("d-none");
      document.getElementById("evaluationLoading")?.classList.remove("d-none");
      document.getElementById("evaluationText").innerHTML = "";
      document.getElementById("scoreDisplay").innerHTML = "";

      try {
        const data = await CL.api.post("/api/mock/submit-answer", { answer });
        document.getElementById("evaluationLoading")?.classList.add("d-none");
        document.getElementById("evaluationText").innerHTML = renderMarkdown(data.evaluation);
        if (typeof hljs !== "undefined") {
          document.getElementById("evaluationText").querySelectorAll("pre code").forEach((el) => hljs.highlightElement(el));
        }

        // Score display
        const scoreEl = document.getElementById("scoreDisplay");
        const scoreColor = data.score >= 70 ? "var(--cl-green)" : data.score >= 50 ? "var(--cl-yellow)" : "var(--cl-red)";
        scoreEl.innerHTML = `<span style="font-size:1.4rem;font-weight:900;color:${scoreColor}">${data.score}</span><span style="color:var(--cl-text-muted);font-size:13px">/100</span>`;

        this.state.scores.push(data.score);
        this.state.qIndex++;

        const nextBtn = document.getElementById("nextQuestionBtn");
        if (data.done) {
          nextBtn.innerHTML = '<i class="bi bi-trophy me-2"></i>View Results';
          nextBtn.onclick = () => this.showResults(data.avg_score);
        } else {
          nextBtn.innerHTML = '<i class="bi bi-arrow-right me-2"></i>Next Question';
          nextBtn.onclick = () => this.nextQuestion();
        }
      } catch (err) {
        document.getElementById("evaluationLoading")?.classList.add("d-none");
        CL.toast.show(err.message, "error");
      }
    },

    async skip() {
      this.state.scores.push(0);
      this.state.qIndex++;
      // Force API to advance
      await CL.api.post("/api/mock/submit-answer", { answer: "[Skipped]" }).catch(() => {});
      await this.nextQuestion();
    },

    showResults(avgScore) {
      document.getElementById("interviewPanel")?.classList.add("d-none");
      document.getElementById("resultsPanel")?.classList.remove("d-none");

      const scores = this.state.scores.filter((s) => s > 0);
      const avg = avgScore || (scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0);

      document.getElementById("finalScore").textContent = avg;

      const color = avg >= 80 ? "var(--cl-green)" : avg >= 60 ? "var(--cl-yellow)" : "var(--cl-red)";
      document.getElementById("finalScoreCircle").style.borderColor = color;
      document.querySelector("#finalScoreCircle span").style.color = color;

      const messages = {
        excellent: "🎉 Outstanding! You're interview-ready. Keep it up!",
        good: "👍 Good performance! A bit more practice and you'll ace it.",
        fair: "💪 Decent start. Focus on the areas marked for improvement.",
        low: "📚 Keep practising! Review the AI feedback for each question.",
      };
      const msg = avg >= 80 ? messages.excellent : avg >= 65 ? messages.good : avg >= 50 ? messages.fair : messages.low;
      document.getElementById("scoreMessage").textContent = msg;

      const scoresEl = document.getElementById("questionScores");
      this.state.scores.forEach((score, i) => {
        const col = document.createElement("div");
        col.className = "col-6 col-md-3";
        const clr = score >= 70 ? "var(--cl-green)" : score >= 50 ? "var(--cl-yellow)" : "var(--cl-red)";
        col.innerHTML = `
          <div style="text-align:center;padding:16px;background:var(--cl-bg-elevated);border:1px solid var(--cl-border);border-radius:var(--cl-radius);">
            <div style="font-size:1.5rem;font-weight:800;color:${clr}">${score || "–"}</div>
            <div style="font-size:11.5px;color:var(--cl-text-muted)">Q${i + 1}</div>
          </div>`;
        scoresEl.appendChild(col);
      });
    },

    retry() {
      document.getElementById("resultsPanel")?.classList.add("d-none");
      document.getElementById("setupPanel")?.classList.remove("d-none");
      document.getElementById("questionScores").innerHTML = "";
      this.state = { active: false, qIndex: 0, total: 0, scores: [] };
    },
  };

  /* ----------------------------------------------------------
     RESUME MODULE
  ---------------------------------------------------------- */
  CL.resume = {
    resumeText: "",

    init() {
      const dropzone    = document.getElementById("dropzone");
      const fileInput   = document.getElementById("resumeFile");
      const analyseBtn  = document.getElementById("analyseBtn");
      const resumeTextEl = document.getElementById("resumeText");
      const removeBtn   = document.getElementById("removeFile");

      if (!dropzone) return;

      // Drag & drop
      dropzone.addEventListener("click", () => fileInput.click());
      dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
      dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length) this.uploadFile(e.dataTransfer.files[0]);
      });
      fileInput.addEventListener("change", () => {
        if (fileInput.files.length) this.uploadFile(fileInput.files[0]);
      });

      // Manual text input
      if (resumeTextEl) {
        resumeTextEl.addEventListener("input", () => {
          this.resumeText = resumeTextEl.value.trim();
          if (analyseBtn) analyseBtn.disabled = !this.resumeText;
        });
      }

      // Remove file
      if (removeBtn) {
        removeBtn.addEventListener("click", () => {
          this.resumeText = "";
          document.getElementById("uploadInfo")?.classList.add("d-none");
          document.getElementById("parseResults")?.classList.add("d-none");
          if (analyseBtn) analyseBtn.disabled = true;
          fileInput.value = "";
        });
      }

      // Analyse
      if (analyseBtn) analyseBtn.addEventListener("click", () => this.analyse());
    },

    async uploadFile(file) {
      const analyseBtn = document.getElementById("analyseBtn");
      const formData = new FormData();
      formData.append("resume", file);

      document.getElementById("fileName").textContent = file.name;
      document.getElementById("uploadInfo")?.classList.remove("d-none");

      try {
        const res = await fetch("/api/upload-resume", { method: "POST", body: formData });
        if (!res.ok) throw new Error((await res.json()).error || "Upload failed");
        const data = await res.json();
        this.resumeText = data.parsed.raw_text;

        // Show parse stats
        document.getElementById("wordCount").textContent = data.parsed.word_count;
        document.getElementById("sectionsCount").textContent = data.parsed.sections_present;
        document.getElementById("skillsCount").textContent = data.parsed.skills?.length || 0;
        document.getElementById("parseResults")?.classList.remove("d-none");

        // Quality flags
        const flagsEl = document.getElementById("qualityFlags");
        if (flagsEl && data.parsed.quality_flags?.length) {
          flagsEl.innerHTML = data.parsed.quality_flags.map(
            (f) => `<div style="color:var(--cl-orange);font-size:12px;margin:2px 0;">⚠️ ${f}</div>`
          ).join("");
        }

        if (analyseBtn) analyseBtn.disabled = false;
        CL.toast.show("Resume uploaded and parsed!", "success");
      } catch (err) {
        CL.toast.show(err.message, "error");
      }
    },

    async analyse() {
      const role = document.getElementById("resumeRole")?.value.trim() || "Software Engineer";
      const exp  = document.getElementById("resumeExp")?.value || "mid";
      const textEl = document.getElementById("resumeText");

      const text = this.resumeText || textEl?.value.trim() || "";
      if (!text) { CL.toast.show("No resume content to analyse.", "warn"); return; }

      document.getElementById("resumePlaceholder")?.classList.add("d-none");
      document.getElementById("resumeResults")?.classList.add("d-none");
      document.getElementById("resumeLoading")?.classList.remove("d-none");

      try {
        const data = await CL.api.post("/api/analyze-resume", { resume_text: text, role, experience: exp });
        document.getElementById("resumeLoading")?.classList.add("d-none");
        document.getElementById("resumeAnalysisContent").innerHTML = renderMarkdown(data.analysis);
        document.getElementById("resumeResults")?.classList.remove("d-none");
        CL.toast.show("Resume analysed!", "success");
      } catch (err) {
        document.getElementById("resumeLoading")?.classList.add("d-none");
        document.getElementById("resumePlaceholder")?.classList.remove("d-none");
        CL.toast.show(err.message, "error");
      }
    },
  };

  /* ----------------------------------------------------------
     INIT ON DOM READY
  ---------------------------------------------------------- */
  document.addEventListener("DOMContentLoaded", () => {
    CL.theme.init();
  });

})(window.CareerLift = window.CareerLift || {});
