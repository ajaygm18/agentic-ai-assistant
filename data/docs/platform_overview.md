# Atlas Assist Platform Overview

Atlas Assist is an internal support operations platform used by customer success and implementation teams.

## Core capabilities

- Unified ticket workspace for email, chat, and escalation queues.
- Embedded workflow automations for SLA tracking, ownership assignment, and approval routing.
- A knowledge composer that publishes structured support playbooks.
- A reporting layer that tracks first-response SLA, reopen rate, escalation reasons, and resolution quality.

## Assistant integration notes

- The internal AI assistant is allowed to retrieve published playbooks and release notes.
- The assistant should not invent customer-specific facts that are not present in retrieved documents.
- If a user asks about release changes or internal policy, the answer should cite the supporting document chunk.

## Architecture summary

- Frontend: React dashboard used by support operators and team leads.
- API layer: Python FastAPI services for automation and analytics endpoints.
- Data layer: Postgres for operational records and Chroma for experimental semantic retrieval.
- AI layer: OpenAI chat models with retrieval augmentation and deterministic tool calls for exact tasks.

## Operational guidance

- For policy questions, the assistant should prefer the handbook over prior conversation memory.
- For calculations, date math, or exact timestamps, the assistant should use a tool rather than guess.
- For mixed questions such as "compare release 3.4 changes and tell me what to prioritize today", the assistant should combine retrieval, memory, and tool usage.
