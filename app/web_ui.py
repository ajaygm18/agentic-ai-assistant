from __future__ import annotations


def render_chat_ui() -> str:
    return r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Agentic AI Assistant</title>
  <style>
    :root {
      --ink: #18211d;
      --muted: #66736b;
      --paper: #f6f0e3;
      --panel: rgba(255, 251, 241, 0.82);
      --panel-strong: #fffaf0;
      --line: rgba(24, 33, 29, 0.14);
      --accent: #ca5b2f;
      --accent-dark: #87391f;
      --sage: #7d947c;
      --sky: #d6e8e2;
      --shadow: 0 24px 70px rgba(38, 30, 18, 0.18);
      --radius: 28px;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Aptos", "Gill Sans", "Trebuchet MS", sans-serif;
      background:
        radial-gradient(circle at 8% 10%, rgba(202, 91, 47, 0.22), transparent 34%),
        radial-gradient(circle at 86% 4%, rgba(125, 148, 124, 0.30), transparent 30%),
        linear-gradient(135deg, #f4e8cf 0%, #e7efe8 48%, #f8f1df 100%);
      overflow: hidden;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(24, 33, 29, 0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(24, 33, 29, 0.045) 1px, transparent 1px);
      background-size: 42px 42px;
      mask-image: linear-gradient(to bottom, black, transparent 82%);
    }

    .shell {
      height: 100vh;
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      gap: 18px;
      padding: 18px;
    }

    .sidebar,
    .workspace {
      border: 1px solid var(--line);
      background: var(--panel);
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    .sidebar {
      border-radius: var(--radius);
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      overflow: auto;
    }

    .brand {
      display: grid;
      gap: 8px;
    }

    .eyebrow {
      color: var(--accent-dark);
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      font-weight: 800;
    }

    h1 {
      margin: 0;
      font-family: "Georgia", "Times New Roman", serif;
      font-size: clamp(34px, 4vw, 52px);
      line-height: 0.94;
      letter-spacing: -0.055em;
    }

    .subtitle {
      color: var(--muted);
      line-height: 1.45;
      margin: 0;
    }

    .status-card,
    .tool-card,
    .session-card {
      background: rgba(255, 255, 255, 0.42);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 14px;
    }

    .status-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid rgba(24, 33, 29, 0.09);
      font-size: 13px;
    }

    .status-row:last-child {
      border-bottom: 0;
    }

    .label {
      color: var(--muted);
    }

    .value {
      font-weight: 800;
      text-align: right;
    }

    .session-input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 12px;
      background: rgba(255, 255, 255, 0.55);
      color: var(--ink);
      font: inherit;
      outline: none;
    }

    .session-input:focus {
      border-color: rgba(202, 91, 47, 0.62);
      box-shadow: 0 0 0 4px rgba(202, 91, 47, 0.11);
    }

    .button-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 14px;
      font-weight: 850;
      cursor: pointer;
      color: var(--ink);
      background: var(--sky);
      transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }

    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 12px 24px rgba(24, 33, 29, 0.12);
    }

    button.primary {
      color: #fffaf2;
      background: linear-gradient(135deg, var(--accent), var(--accent-dark));
    }

    button.ghost {
      background: rgba(255, 255, 255, 0.48);
      border: 1px solid var(--line);
    }

    .quick-list {
      display: grid;
      gap: 8px;
    }

    .quick {
      text-align: left;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.46);
      border: 1px solid rgba(24, 33, 29, 0.11);
      color: var(--ink);
      font-weight: 700;
    }

    .workspace {
      border-radius: var(--radius);
      min-width: 0;
      display: grid;
      grid-template-rows: auto 1fr auto;
      overflow: hidden;
    }

    .topbar {
      padding: 18px 22px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      background: rgba(255, 250, 240, 0.56);
    }

    .topbar-title {
      font-weight: 900;
      letter-spacing: -0.02em;
    }

    .pill {
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(125, 148, 124, 0.18);
      color: #334339;
      font-size: 12px;
      font-weight: 800;
      border: 1px solid rgba(125, 148, 124, 0.28);
    }

    .messages {
      overflow: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .empty {
      margin: auto;
      max-width: 620px;
      text-align: center;
      display: grid;
      gap: 12px;
      animation: rise 480ms ease both;
    }

    .empty h2 {
      margin: 0;
      font-family: "Georgia", "Times New Roman", serif;
      font-size: clamp(34px, 5vw, 72px);
      line-height: 0.92;
      letter-spacing: -0.06em;
    }

    .empty p {
      margin: 0;
      color: var(--muted);
      font-size: 17px;
      line-height: 1.5;
    }

    .message {
      max-width: min(860px, 88%);
      border-radius: 24px;
      padding: 16px 18px;
      line-height: 1.55;
      animation: rise 260ms ease both;
      white-space: pre-wrap;
    }

    .message.user {
      align-self: flex-end;
      background: linear-gradient(135deg, #21382f, #436353);
      color: #fffaf0;
      border-bottom-right-radius: 8px;
    }

    .message.assistant {
      align-self: flex-start;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-bottom-left-radius: 8px;
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .chip {
      font-size: 12px;
      font-weight: 800;
      border-radius: 999px;
      padding: 6px 9px;
      background: rgba(202, 91, 47, 0.12);
      color: var(--accent-dark);
    }

    details {
      margin-top: 12px;
      padding: 10px 12px;
      background: rgba(246, 240, 227, 0.64);
      border-radius: 16px;
      border: 1px solid rgba(24, 33, 29, 0.09);
    }

    summary {
      cursor: pointer;
      font-weight: 900;
      color: var(--accent-dark);
    }

    .source {
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid rgba(24, 33, 29, 0.09);
      font-size: 13px;
      color: var(--muted);
    }

    .composer {
      padding: 16px;
      border-top: 1px solid var(--line);
      background: rgba(255, 250, 240, 0.70);
    }

    .composer-form {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: end;
    }

    textarea {
      width: 100%;
      min-height: 58px;
      max-height: 170px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 16px 18px;
      background: rgba(255, 255, 255, 0.62);
      color: var(--ink);
      font: inherit;
      outline: none;
    }

    textarea:focus {
      border-color: rgba(202, 91, 47, 0.62);
      box-shadow: 0 0 0 4px rgba(202, 91, 47, 0.10);
    }

    .send {
      min-height: 58px;
      min-width: 120px;
    }

    .toast {
      position: fixed;
      right: 24px;
      bottom: 24px;
      max-width: 360px;
      background: #18211d;
      color: #fffaf0;
      padding: 14px 16px;
      border-radius: 18px;
      box-shadow: var(--shadow);
      transform: translateY(20px);
      opacity: 0;
      pointer-events: none;
      transition: opacity 180ms ease, transform 180ms ease;
      z-index: 10;
    }

    .toast.show {
      transform: translateY(0);
      opacity: 1;
    }

    .loading {
      opacity: 0.7;
      pointer-events: none;
    }

    @keyframes rise {
      from {
        opacity: 0;
        transform: translateY(12px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @media (max-width: 920px) {
      body {
        overflow: auto;
      }

      .shell {
        min-height: 100vh;
        height: auto;
        grid-template-columns: 1fr;
      }

      .workspace {
        min-height: 72vh;
      }

      .message {
        max-width: 96%;
      }
    }

    @media (max-width: 560px) {
      .shell {
        padding: 10px;
      }

      .sidebar,
      .workspace {
        border-radius: 22px;
      }

      .composer-form {
        grid-template-columns: 1fr;
      }

      .send {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <aside class="sidebar">
      <section class="brand">
        <div class="eyebrow">Agentic RAG Workspace</div>
        <h1>Atlas Assistant</h1>
        <p class="subtitle">Talk to your local knowledge base, run tools, inspect sources, and keep session memory without touching raw API docs.</p>
      </section>

      <section class="status-card">
        <div class="status-row"><span class="label">API</span><span class="value" id="apiStatus">Checking</span></div>
        <div class="status-row"><span class="label">Model</span><span class="value" id="modelStatus">-</span></div>
        <div class="status-row"><span class="label">Vector DB</span><span class="value" id="vectorStatus">-</span></div>
        <div class="status-row"><span class="label">Chunks</span><span class="value" id="chunkStatus">-</span></div>
      </section>

      <section class="session-card">
        <div class="eyebrow">Session</div>
        <input id="sessionId" class="session-input" />
        <div class="button-row" style="margin-top: 10px;">
          <button class="ghost" id="newSessionBtn" type="button">New</button>
          <button class="ghost" id="loadSessionBtn" type="button">Load</button>
        </div>
      </section>

      <section class="tool-card">
        <div class="eyebrow">Actions</div>
        <div class="button-row" style="margin-top: 10px;">
          <button class="primary" id="ingestBtn" type="button">Ingest Docs</button>
          <button class="ghost" id="clearBtn" type="button">Clear UI</button>
        </div>
      </section>

      <section class="tool-card">
        <div class="eyebrow">Try these</div>
        <div class="quick-list" style="margin-top: 10px;">
          <button class="quick" data-prompt="Summarize the Sev-1 support policy and cite the source.">Summarize Sev-1 policy</button>
          <button class="quick" data-prompt="What changed in release 3.5.0 and what should support teams retrain on?">Ask a RAG question</button>
          <button class="quick" data-prompt="Calculate (42 / 6) + 7 and answer in one sentence.">Run calculator tool</button>
          <button class="quick" data-prompt="What is the current timestamp in UTC?">Use timestamp tool</button>
        </div>
      </section>
    </aside>

    <section class="workspace">
      <header class="topbar">
        <div>
          <div class="topbar-title">Interactive Assistant</div>
          <div class="label">RAG + MCP + tools + memory</div>
        </div>
        <div class="pill" id="turnPill">0 turns</div>
      </header>

      <section class="messages" id="messages">
        <div class="empty" id="emptyState">
          <h2>Ask like a user. Inspect like an engineer.</h2>
          <p>Use the chat normally. The assistant will route, retrieve, call MCP-backed tools, cite sources, and preserve memory for this session.</p>
        </div>
      </section>

      <footer class="composer">
        <form class="composer-form" id="chatForm">
          <textarea id="messageInput" placeholder="Ask a question about docs, ask for a calculation, or continue the session..." required></textarea>
          <button class="primary send" id="sendBtn" type="submit">Send</button>
        </form>
      </footer>
    </section>
  </main>

  <div class="toast" id="toast"></div>

  <script>
    const messagesEl = document.getElementById("messages");
    const emptyState = document.getElementById("emptyState");
    const form = document.getElementById("chatForm");
    const input = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const sessionInput = document.getElementById("sessionId");
    const turnPill = document.getElementById("turnPill");
    const toast = document.getElementById("toast");

    const state = {
      turns: 0,
      busy: false,
    };

    function makeSessionId() {
      return `session-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
    }

    function showToast(message) {
      toast.textContent = message;
      toast.classList.add("show");
      window.setTimeout(() => toast.classList.remove("show"), 3200);
    }

    function setBusy(value) {
      state.busy = value;
      sendBtn.disabled = value;
      sendBtn.textContent = value ? "Thinking" : "Send";
      document.body.classList.toggle("loading", value);
    }

    function updateTurns(count) {
      state.turns = count;
      turnPill.textContent = `${count} turn${count === 1 ? "" : "s"}`;
    }

    function removeEmptyState() {
      if (emptyState) {
        emptyState.remove();
      }
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function addMessage(role, content, meta = {}) {
      removeEmptyState();
      const wrapper = document.createElement("article");
      wrapper.className = `message ${role}`;
      wrapper.innerHTML = `<div>${escapeHtml(content)}</div>`;

      if (role === "assistant") {
        const chips = [];
        if (meta.route) chips.push(`<span class="chip">route: ${escapeHtml(meta.route)}</span>`);
        if (meta.tools?.length) chips.push(`<span class="chip">tools: ${escapeHtml(meta.tools.join(", "))}</span>`);
        if (meta.sources?.length) chips.push(`<span class="chip">${meta.sources.length} source${meta.sources.length === 1 ? "" : "s"}</span>`);
        if (chips.length) {
          wrapper.insertAdjacentHTML("beforeend", `<div class="meta">${chips.join("")}</div>`);
        }

        if (meta.sources?.length) {
          const sources = meta.sources.map((source) => `
            <div class="source">
              <strong>${escapeHtml(source.source_id)}</strong><br />
              ${escapeHtml(source.title || "Untitled")}<br />
              <span>${escapeHtml(source.source_path || "")}</span><br />
              <span>${escapeHtml(source.excerpt || "")}</span>
            </div>
          `).join("");
          wrapper.insertAdjacentHTML("beforeend", `<details><summary>Sources</summary>${sources}</details>`);
        }

        if (meta.trace?.length) {
          const trace = meta.trace.map((item) => `
            <div class="source">
              <strong>${escapeHtml(item.stage)}</strong><br />
              ${escapeHtml(item.message)}
            </div>
          `).join("");
          wrapper.insertAdjacentHTML("beforeend", `<details><summary>Execution trace</summary>${trace}</details>`);
        }
      }

      messagesEl.appendChild(wrapper);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    async function fetchJson(url, options = {}) {
      const response = await fetch(url, options);
      const text = await response.text();
      let payload;
      try {
        payload = text ? JSON.parse(text) : {};
      } catch {
        payload = { detail: text };
      }
      if (!response.ok) {
        throw new Error(payload.detail || payload.error?.message || `Request failed: ${response.status}`);
      }
      return payload;
    }

    async function refreshHealth() {
      try {
        const health = await fetchJson("/health");
        document.getElementById("apiStatus").textContent = health.status;
        document.getElementById("modelStatus").textContent = health.llm_model;
        document.getElementById("vectorStatus").textContent = health.vector_store_ready ? "Ready" : "Not ready";
        document.getElementById("chunkStatus").textContent = health.indexed_chunks;
      } catch (error) {
        document.getElementById("apiStatus").textContent = "Offline";
        showToast(error.message);
      }
    }

    async function sendMessage(message) {
      if (!message.trim() || state.busy) return;
      const session_id = sessionInput.value.trim() || makeSessionId();
      sessionInput.value = session_id;
      addMessage("user", message);
      input.value = "";
      setBusy(true);
      try {
        const response = await fetchJson("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id, user_message: message }),
        });
        addMessage("assistant", response.answer, {
          route: response.route,
          tools: response.tools_used,
          sources: response.sources,
          trace: response.execution_summary,
        });
        updateTurns(response.memory_turn_count || state.turns + 2);
      } catch (error) {
        addMessage("assistant", `Error: ${error.message}`);
      } finally {
        setBusy(false);
      }
    }

    async function loadSession() {
      const session_id = sessionInput.value.trim();
      if (!session_id) return showToast("Enter a session id first.");
      try {
        const response = await fetchJson(`/sessions/${encodeURIComponent(session_id)}`);
        messagesEl.innerHTML = "";
        response.turns.forEach((turn) => addMessage(turn.role, turn.content));
        updateTurns(response.turn_count || response.turns.length);
        showToast("Session loaded.");
      } catch (error) {
        showToast(error.message);
      }
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      sendMessage(input.value);
    });

    document.getElementById("ingestBtn").addEventListener("click", async () => {
      setBusy(true);
      try {
        const response = await fetchJson("/ingest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        showToast(`Ingested ${response.documents_loaded} docs into ${response.chunks_created} chunks.`);
        await refreshHealth();
      } catch (error) {
        showToast(error.message);
      } finally {
        setBusy(false);
      }
    });

    document.getElementById("clearBtn").addEventListener("click", () => {
      messagesEl.innerHTML = "";
      messagesEl.appendChild(emptyState);
      updateTurns(0);
    });

    document.getElementById("newSessionBtn").addEventListener("click", () => {
      sessionInput.value = makeSessionId();
      messagesEl.innerHTML = "";
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.id = "emptyState";
      empty.innerHTML = "<h2>Fresh session.</h2><p>Start a new conversation with isolated memory.</p>";
      messagesEl.appendChild(empty);
      updateTurns(0);
    });

    document.getElementById("loadSessionBtn").addEventListener("click", loadSession);

    document.querySelectorAll(".quick").forEach((button) => {
      button.addEventListener("click", () => {
        input.value = button.dataset.prompt;
        input.focus();
      });
    });

    sessionInput.value = localStorage.getItem("agentic-session-id") || makeSessionId();
    sessionInput.addEventListener("change", () => localStorage.setItem("agentic-session-id", sessionInput.value));
    refreshHealth();
  </script>
</body>
</html>"""
