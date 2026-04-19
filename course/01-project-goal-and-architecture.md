# Project Goal And Architecture

## Project Goal

The goal of this project is to build a local agentic AI assistant that behaves like a real backend system, not a toy chatbot.

The assistant should be able to:

- receive user messages through FastAPI
- maintain session memory
- classify the user request
- decide whether to answer directly, retrieve documents, call tools, or combine multiple steps
- retrieve relevant knowledge from a vector database
- cite sources in the final response
- execute deterministic tools
- communicate with a real MCP server
- return a structured API response with trace information

The important point is that the system is not only a model wrapper. It is a workflow engine around the model.

## High-Level Architecture

At a high level, the system looks like this:

```text
Browser UI / API Client
        |
        v
FastAPI App
        |
        v
Assistant Service
        |
        +--> Session Memory
        |
        +--> Workflow Router
        |
        +--> Planner Model
        |
        +--> RAG Retriever
        |
        +--> MCP Client
        |       |
        |       v
        |   MCP Server
        |       |
        |       +--> Tools
        |       +--> Prompts
        |       +--> Resources
        |
        +--> Execution Model
                |
                v
          Final Answer
```

Each part has a separate responsibility.

## Main Components

### FastAPI App

The FastAPI app is the HTTP entrypoint.

Files:

```text
app/main.py
app/api/routes.py
```

It exposes:

- `GET /`
- `GET /health`
- `POST /ingest`
- `POST /chat`
- `GET /sessions/{session_id}`
- `/mcp`

The `/` route serves the browser UI.

The `/mcp` mount exposes the MCP server over streamable HTTP.

The `/chat` route is the main product API.

## Assistant Service

The assistant service coordinates the full chat flow.

File:

```text
app/agents/service.py
```

It does the following:

1. cleans the user message
2. builds a `UserQueryContext`
3. loads memory for the session
4. asks the router which workflow to use
5. asks the planner to build execution steps
6. retrieves knowledge if the route needs RAG
7. runs the executor
8. stores the user and assistant turns
9. returns a `ChatResponse`

This service is the orchestration layer.

## Router

The router decides the workflow type.

File:

```text
app/agents/router.py
```

Available routes:

- `direct`
- `rag`
- `tool`
- `hybrid`

The router uses explicit heuristics. For example:

- short greetings go to `direct`
- policy/release/document questions go to `rag`
- calculations and timestamps go to `tool`
- multi-step questions that mention internal knowledge can go to `hybrid`
- questions like “what MCP tools are available” go to `tool` so the system can introspect the live MCP server

This explicit routing makes the system easier to explain and debug than a fully opaque agent loop.

## Planner

The planner creates a short execution plan.

File:

```text
app/agents/planner.py
```

The planner uses:

- an MCP prompt named `planning_prompt`
- a planner model
- a fallback static plan if model planning fails

The planner output is parsed into typed `PlanStep` objects.

This gives the final response an execution trace and makes the assistant behavior easier to inspect.

## Executor

The executor generates the final answer.

File:

```text
app/agents/executor.py
```

It supports two execution styles:

- direct model generation
- tool-aware execution

For the current default model setup, tool execution is deterministic and manual. The system chooses the tool in Python, executes it through MCP-backed tools, stores the result, and then asks the model to synthesize the answer.

This avoids relying on provider-specific native tool-calling behavior when the selected model route does not support it cleanly.

## RAG Layer

The RAG layer handles ingestion, vector storage, and retrieval.

Files:

```text
app/rag/ingestion.py
app/rag/vectorstore.py
app/rag/retriever.py
```

RAG flow:

```text
Documents -> Chunking -> Embeddings -> Chroma -> Similarity Search -> Citations -> Prompt Context
```

Supported document types:

- Markdown
- text
- RST
- PDF

The vector store is Chroma.

The embedding model is configured as:

```text
text-embedding-3-small
```

## MCP Layer

The project uses real MCP through the official Python SDK.

Files:

```text
app/mcp/server.py
app/mcp/client.py
```

The MCP server exposes:

Tools:

- `calculator`
- `current_timestamp`
- `session_summary`
- `knowledge_lookup`

Resources:

- `session://{session_id}`
- `knowledge://catalog`

Prompt:

- `planning_prompt`

The FastAPI app mounts the MCP server at:

```text
/mcp
```

The internal app client can also start the MCP server over stdio.

This means the project does not merely use MCP-style schemas. It has an actual MCP server and client.

## Memory Layer

Memory stores previous turns for a session.

Files:

```text
app/memory/base.py
app/memory/store.py
```

The current implementation is file-backed:

```text
data/sessions/
```

Each session gets a JSON file. This lets both the FastAPI app and the MCP server access the same memory.

The memory layer is abstracted through `BaseMemoryStore`, so it could later be replaced with Redis, Postgres, or another database.

## Model Layer

Model clients are centralized in:

```text
app/services/llm.py
```

There are three model roles:

- execution model
- planner model
- embedding model

The execution model generates final answers.

The planner model creates short plans.

The embedding model converts document chunks and queries into vectors.

The code uses OpenAI-compatible APIs. The gateway details are outside the scope of this course.

## API Schema Layer

Request and response schemas are defined in:

```text
app/models/api.py
```

Important schemas:

- `ChatRequest`
- `ChatResponse`
- `IngestRequest`
- `IngestResponse`
- `HealthResponse`
- `SessionResponse`

Using schemas gives the API a stable contract.

## Context Schema Layer

Internal execution context schemas live in:

```text
app/mcp/contexts.py
```

Important context objects:

- `UserQueryContext`
- `MemoryContext`
- `RetrievedKnowledgeContext`
- `ToolResultContext`
- `RoutingDecision`
- `AgentExecutionState`

These objects are not just API schemas. They are the internal state containers that move through the agent workflow.

## End-To-End Request Lifecycle

Here is what happens when a user sends a chat message:

```text
POST /chat
  |
  v
ChatRequest is validated
  |
  v
AssistantService.chat()
  |
  v
Load session memory
  |
  v
Route the request
  |
  v
Build execution plan
  |
  +--> If RAG/hybrid: call MCP knowledge_lookup
  |
  +--> If tool/hybrid: execute MCP-backed tools
  |
  v
Call execution model
  |
  v
Persist user and assistant turns
  |
  v
Return ChatResponse
```

The response includes:

- final answer
- route
- sources
- tools used
- execution summary
- updated memory count

## Why The Architecture Is Split This Way

The project separates responsibilities so each part can evolve independently:

- The API layer does not know retrieval internals.
- The router does not call models directly.
- The planner does not execute tools.
- The executor does not parse PDFs.
- The MCP server owns protocol-exposed tools/resources/prompts.
- The memory store can be replaced without rewriting the agent.
- The vector store can be changed without rewriting the FastAPI routes.

This is the difference between a demo script and a backend architecture.

## What To Understand Before Continuing

Before moving to the next chapters, make sure you understand this flow:

```text
User Message
-> FastAPI
-> AssistantService
-> Router
-> Planner
-> RAG and/or MCP Tools
-> Execution Model
-> Memory
-> API Response
```

Every later chapter expands one part of that pipeline.

