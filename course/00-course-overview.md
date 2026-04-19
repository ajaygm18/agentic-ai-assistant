# Course Overview

## Who This Course Is For

This course is for Python developers who already know the basics of building APIs and want to understand how to build a realistic GenAI backend. It assumes you can read Python, understand HTTP APIs, and are comfortable with project structure, virtual environments, and environment variables.

You do not need to be an expert in LangChain, MCP, vector databases, or FastAPI internals. The course explains how those pieces fit together in this project.

## What You Will Build

The project is an agentic AI assistant backend with:

- FastAPI APIs
- a browser chat interface
- LangChain model clients
- a planner/executor agent workflow
- RAG over local documents
- Chroma as the vector store
- PDF, Markdown, text, and RST ingestion
- real MCP server/client integration
- MCP tools, prompts, and resources
- deterministic tool execution
- file-backed session memory
- source citations
- execution traces

The assistant can receive a user message, decide what workflow to use, retrieve relevant knowledge, call tools, use conversation memory, and return a grounded answer.

## What The Project Does

At runtime, a user can open the app in a browser, type a question, and get a response from the assistant. The assistant can:

- answer simple conversational messages
- search the local knowledge base
- cite retrieved sources
- calculate arithmetic expressions
- return current timestamps
- summarize session history
- list live MCP tools, prompts, and resources
- preserve memory across turns by `session_id`

For example:

```text
User:
Summarize the Sev-1 support policy and cite the source.

Assistant:
Sev-1 is a full production outage or critical workflow unavailable for all customers.
The initial response target is 15 minutes [support_handbook-p1-chunk-...].
```

Another example:

```text
User:
Calculate (42 / 6) + 7 and answer in one sentence.

Assistant:
The result of (42 / 6) + 7 is 14.
```

## What This Course Focuses On

This course focuses on the Python and GenAI engineering parts:

- FastAPI app design
- request/response schemas
- model client setup
- agent workflow design
- routing logic
- planner/executor architecture
- document ingestion
- embeddings
- Chroma vector store usage
- retrieval and citation handling
- real MCP server/client implementation
- tool execution
- memory design
- end-to-end request flow
- testing and debugging
- production hardening ideas

## What This Course Does Not Cover

This course does not explain Anti-API internals. The project uses an OpenAI-compatible model gateway, but the gateway itself is treated as infrastructure.

The course also does not deeply teach frontend design. The project includes a browser UI so the assistant can be tested like a normal product, but the focus remains on backend and GenAI architecture.

You will see how the UI calls `/chat`, `/health`, `/ingest`, and `/sessions/{session_id}`, but you will not get a full frontend design course.

## Core Technologies Used

The main technologies are:

- Python
- FastAPI
- Pydantic
- LangChain
- OpenAI-compatible chat and embedding APIs
- Chroma
- MCP Python SDK
- pypdf
- Uvicorn

The important design idea is that each tool has a clear responsibility:

- FastAPI exposes the product API.
- Pydantic defines typed request, response, and internal context objects.
- LangChain wraps chat and embedding models.
- Chroma stores embedded document chunks.
- MCP exposes tools, resources, and prompts through a real protocol boundary.
- The agent layer decides how to combine memory, tools, retrieval, planning, and final synthesis.

## Final Project Structure

The project is organized like this:

```text
agentic_ai_assistant/
├── app/
│   ├── agents/
│   ├── api/
│   ├── core/
│   ├── mcp/
│   ├── memory/
│   ├── models/
│   ├── rag/
│   ├── services/
│   ├── tools/
│   ├── main.py
│   └── web_ui.py
├── course/
├── data/
│   └── docs/
├── scripts/
├── requirements.txt
├── .env.example
└── README.md
```

The main backend entrypoint is:

```text
app/main.py
```

The main API routes live in:

```text
app/api/routes.py
```

The main agent workflow is spread across:

```text
app/agents/router.py
app/agents/planner.py
app/agents/executor.py
app/agents/service.py
```

The RAG pipeline lives in:

```text
app/rag/ingestion.py
app/rag/vectorstore.py
app/rag/retriever.py
```

The real MCP implementation lives in:

```text
app/mcp/server.py
app/mcp/client.py
```

## Mental Model

Think of the system as five cooperating layers:

```text
User Interface / API
        |
FastAPI Routes
        |
Agent Service
        |
Router + Planner + Retriever + Tools + Memory
        |
Models + Chroma + MCP Server
```

The assistant is not just one prompt sent directly to a model. It is a workflow:

1. receive a message
2. load session memory
3. route the request
4. build a plan
5. retrieve documents if needed
6. execute tools if needed
7. generate a final answer
8. save the conversation turn
9. return answer, sources, tools used, and trace

## What Makes This Project Agentic

The project is agentic because it makes explicit decisions about what to do next. It does not always send the same prompt to the same model.

Depending on the user request, it can choose:

- direct answer
- retrieval-first answer
- tool-first answer
- hybrid retrieval plus tools

The agent has a router, planner, execution state, tools, memory, and retrieval context. Those pieces make the behavior explainable and debuggable.

## What Makes This Project Production-Oriented

The project is not a single-file demo. It includes:

- modular folder structure
- environment-driven configuration
- typed API schemas
- typed internal context models
- reusable service classes
- persistent vector store
- persistent session store
- real MCP server/client integration
- clear API boundaries
- startup bootstrap logic
- local testing commands
- browser UI for manual testing

It is still a local portfolio project, not a fully deployed production service, but its architecture is close to what you would build before adding authentication, monitoring, background jobs, and deployment infrastructure.

## Course Roadmap

The rest of the course is split into focused chapters:

```text
01-project-goal-and-architecture.md
02-environment-and-configuration.md
03-fastapi-api-layer.md
04-model-gateway-and-llm-clients.md
05-agent-routing-and-workflow.md
06-planner-executor-design.md
07-rag-ingestion-pipeline.md
08-vector-store-and-retrieval.md
09-real-mcp-server-client.md
10-tool-system.md
11-conversation-memory.md
12-end-to-end-chat-flow.md
13-browser-ui-integration.md
14-testing-and-debugging.md
15-production-hardening.md
16-build-it-from-scratch.md
```

Each chapter explains one part of the system and how it connects to the rest.

