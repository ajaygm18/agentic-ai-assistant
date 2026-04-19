# Agentic AI Assistant with RAG, MCP, Tool Calling, LangChain, Memory, and FastAPI

This project is a portfolio-quality Python service that implements a realistic agentic assistant with:

- Multi-step routing and execution
- Retrieval-Augmented Generation with Chroma
- LangChain-based LLM orchestration
- Tool calling with deterministic local tools
- Session memory with pluggable storage
- MCP-style structured context models
- FastAPI endpoints for chat, ingestion, health, and session inspection

The chat model and embeddings client are configured to use the local `anti-api-main` project as an OpenAI-compatible gateway by default. That means the assistant talks to `http://localhost:8964/v1` for chat completions and embeddings. The default execution model is `gpt-5.4` through Codex, and the planner model is `claude-opus-4-6` through Antigravity. Anti-API's embeddings route is backed by Copilot/GitHub Models and maps `text-embedding-3-small` to GitHub's `openai/text-embedding-3-small` upstream format.

The project now also uses the real Model Context Protocol through the official Python SDK. A local MCP server exposes tools, resources, and prompts. The FastAPI app connects to it as an MCP client over stdio, and the same MCP server is also mounted over streamable HTTP at `/mcp` for external MCP clients.

## Folder structure

```text
agentic_ai_assistant/
├── app/
│   ├── api/routes.py
│   ├── agents/
│   │   ├── executor.py
│   │   ├── planner.py
│   │   ├── prompts.py
│   │   ├── router.py
│   │   └── service.py
│   ├── core/
│   │   ├── config.py
│   │   ├── container.py
│   │   └── logging.py
│   ├── mcp/
│   │   ├── client.py
│   │   ├── contexts.py
│   │   └── server.py
│   ├── memory/
│   │   ├── base.py
│   │   └── store.py
│   ├── models/api.py
│   ├── rag/
│   │   ├── ingestion.py
│   │   ├── retriever.py
│   │   └── vectorstore.py
│   ├── services/llm.py
│   ├── tools/
│   │   ├── implementations.py
│   │   └── registry.py
│   └── main.py
├── data/docs/
│   ├── platform_overview.md
│   ├── release_notes_q1_2026.md
│   └── support_handbook.md
├── data/sessions/
├── scripts/ingest.py
├── scripts/bootstrap_antiapi_routing.py
├── .env.example
├── requirements.txt
└── README.md
```

## Architecture

### High-level modules

- `app/agents/router.py`: explicit workflow routing for direct, RAG, tool, and hybrid requests.
- `app/agents/planner.py`: generates an execution plan with a dedicated planner model.
- `app/agents/executor.py`: runs the execution model, using native tool binding where supported and a deterministic manual tool path where needed.
- `app/mcp/server.py`: real MCP server exposing tools, resources, and prompts.
- `app/mcp/client.py`: MCP client used by the FastAPI app over stdio transport.
- `app/rag/`: handles document ingestion, vector indexing, and retrieval.
- `app/tools/`: provides deterministic tools such as calculator, timestamp lookup, internal knowledge lookup, and session summarization.
- `app/memory/`: stores per-session turns behind a swappable memory interface.
- `app/mcp/contexts.py`: defines structured Pydantic objects used to pass user context, retrieved knowledge, tool outputs, memory, and execution state across the system.

### Real MCP integration

The project now uses the actual Model Context Protocol, not just an MCP-inspired shape:

- MCP server: [app/mcp/server.py](/C:/Users/ajaya/OneDrive/Documents/projectxd/agentic_ai_assistant/app/mcp/server.py)
- MCP client: [app/mcp/client.py](/C:/Users/ajaya/OneDrive/Documents/projectxd/agentic_ai_assistant/app/mcp/client.py)
- transports:
  - local stdio transport for the app's internal MCP client
  - streamable HTTP mounted at `/mcp` for external MCP clients

What is exposed through MCP:

- Tools: `calculator`, `current_timestamp`, `knowledge_lookup`, `session_summary`
- Resources: `session://{session_id}`, `knowledge://catalog`
- Prompts: `planning_prompt`

How the FastAPI app uses MCP:

- planning pulls a reusable prompt from the MCP server
- retrieval calls the `knowledge_lookup` MCP tool
- deterministic tool execution goes through MCP tools
- session inspection can read the `session://{session_id}` MCP resource

### MCP-style structured context exchange

The project uses explicit Pydantic context objects to move information between components:

- `UserQueryContext`
- `MemoryContext`
- `RetrievedKnowledgeContext`
- `ToolResultContext`
- `RoutingDecision`
- `AgentExecutionState`

That design makes it fair to say:

> Integrated structured context exchange between agents, retrieval, tools, and memory systems using MCP-style context objects.

## Sequence flow

1. `POST /chat` receives `session_id` and `user_message`.
2. Recent session turns are loaded from memory.
3. The router chooses one of four workflows: `direct`, `rag`, `tool`, or `hybrid`.
4. The planner model builds a visible execution plan using a reusable prompt fetched from the MCP server.
5. If needed, the app calls the MCP `knowledge_lookup` tool, which retrieves top-k chunks from Chroma.
6. The executor calls the main chat model through Anti-API and applies deterministic tools through the MCP server when the workflow requires them.
7. Tool outputs and retrieved citations are added back into the structured execution state.
8. The final grounded answer is returned and the new turns are written to memory.

## Setup instructions

### 1. Create a Python environment

```powershell
cd ..\agentic_ai_assistant
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Important notes:

- `LLM_BASE_URL` already points to Anti-API locally.
- `OPENAI_API_KEY` can be any non-empty token for Anti-API chat.
- `EMBEDDING_API_KEY` can also be the same local token because embeddings now default to Anti-API.
- Anti-API must have a working Copilot account configured because `/v1/embeddings` is routed through Copilot/GitHub Models.
- If you want a different embeddings provider later, set `EMBEDDING_BASE_URL` to another OpenAI-compatible endpoint.
- Session storage is file-backed under `data/sessions` so both the FastAPI app and the MCP server can read the same conversation state.

### 3. Start the full local stack

The repo now includes a launcher that starts the sibling `anti-api-main` project, waits for its `/health` endpoint, runs ingestion, and then boots FastAPI:

```powershell
.\start_stack.bat
```

PowerShell variant:

```powershell
.\scripts\start_stack.ps1
```

Optional flags:

```powershell
.\scripts\start_stack.ps1 -SkipIngest
.\scripts\start_stack.ps1 -AntiApiDir "C:\path\to\anti-api-main" -AppPort 8010
```

Anti-API exposes OpenAI-compatible chat and embeddings endpoints at `http://localhost:8964/v1/chat/completions` and `http://localhost:8964/v1/embeddings`.
The launcher also bootstraps Anti-API routing so `gpt-5.4` maps to your first Codex account and `claude-opus-4-6-thinking` maps to your first Antigravity account. The app still requests `claude-opus-4-6`; Anti-API normalizes that to the `thinking` route internally.
The MCP server does not need a separate manual startup step during normal app usage because the app mounts it directly at `/mcp`, and the internal MCP client can also launch it on demand over stdio.

### 4. Ingest documents manually if needed

```powershell
python scripts/ingest.py
```

### 5. Run the FastAPI service

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open the docs UI at `http://localhost:8000/docs`.
The MCP HTTP endpoint is available at `http://localhost:8000/mcp`.

## How ingestion works

1. The ingestion service reads files from `data/docs`.
2. Files are chunked with `RecursiveCharacterTextSplitter`.
3. Each chunk receives source metadata and a stable chunk id.
4. Embeddings are generated with `text-embedding-3-small` through Anti-API's OpenAI-compatible `/v1/embeddings` route.
5. Chunks are written into a persistent Chroma collection under `data/chroma`.

`POST /ingest` and `python scripts/ingest.py` both call the same ingestion service.

Supported document types:

- `.md`
- `.txt`
- `.rst`
- `.pdf`

PDF behavior:

- PDFs are parsed page by page with `pypdf`
- each extracted page becomes a LangChain `Document`
- page number metadata is preserved for retrieval and citations
- scanned/image-only PDFs are not OCR'd; if a PDF has no extractable text, ingestion raises a clear error

## How chat works

### Routing logic

- Internal documentation questions route to `rag`.
- Calculation and timestamp requests route to `tool`.
- Pure conversational requests route to `direct`.
- Multi-step questions that mix retrieval and precise actions route to `hybrid`.

### Tool calling

The agent has four useful tools:

- `calculator`
- `current_timestamp`
- `knowledge_lookup`
- `session_summary`

For models that support native tool calling cleanly, LangChain can bind these tools directly. In the current default setup, `gpt-5.4` is executed through Codex, so the app uses a deterministic manual tool path instead: it selects the needed operations in code, calls the MCP server tools, records the returned results in the execution state, and then asks the model to synthesize the final answer.

### Memory

- Memory is stored per `session_id`.
- The default store is file-backed under `data/sessions` so the main app and the MCP server share the same state.
- The interface is intentionally isolated so it can later be replaced with Redis or a database-backed implementation.

## API endpoints

### `GET /health`

Returns service status plus vector-store readiness.

### `POST /ingest`

Indexes the documents folder into Chroma.

### `POST /chat`

Request:

```json
{
  "session_id": "demo-session",
  "user_message": "What changed in release 3.5 and what should support teams retrain on?"
}
```

Response shape:

```json
{
  "session_id": "demo-session",
  "route": "hybrid",
  "answer": "Release 3.5.0 added semantic knowledge search, session-aware memory, and audit metadata. Teams should retrain on the workflow composer because the legacy macro sidebar was deprecated [release_notes_q1_2026-chunk-3].",
  "sources": [
    {
      "source_id": "release_notes_q1_2026-chunk-3",
      "title": "Release Notes Q1 2026",
      "source_path": "data/docs/release_notes_q1_2026.md",
      "relevance_score": 0.78,
      "excerpt": "Added semantic knowledge search backed by Chroma and OpenAI embeddings..."
    }
  ],
  "tools_used": [],
  "execution_summary": [
    {
      "stage": "routing",
      "message": "Selected 'hybrid' workflow.",
      "timestamp": "2026-04-19T12:00:00Z",
      "data": {
        "rationale": [
          "query references internal knowledge and has multi-step phrasing"
        ]
      }
    }
  ],
  "memory_turn_count": 2,
  "session_updated_at": "2026-04-19T12:00:01Z"
}
```

### `GET /sessions/{session_id}`

Returns the stored turns for a session.

## Example curl commands

### Health

```bash
curl http://localhost:8000/health
```

### Ingest default docs

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Chat with retrieval

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "portfolio-demo",
    "user_message": "Summarize the Sev-1 policy and cite the source."
  }'
```

### Chat with tools

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "portfolio-demo",
    "user_message": "What is (42 / 6) + 7 and what is the current timestamp in UTC?"
  }'
```

## Possible future improvements

- Replace the file-backed session store with Redis or Postgres-backed memory.
- Add async background ingestion jobs and document upload endpoints.
- Add reranking, query rewriting, and hybrid search for better retrieval quality.
- Add OpenTelemetry tracing and structured request logging.
- Add unit tests for routing, tools, and retrieval behavior.
- Add streaming responses over Server-Sent Events or WebSockets.
- Add authentication, rate limiting, and per-tenant vector collections.
