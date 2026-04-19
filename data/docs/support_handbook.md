# Support Operations Handbook

## Incident severity policy

- Sev-1: Full production outage or critical workflow unavailable for all customers. Initial response target is 15 minutes.
- Sev-2: Major degradation with an available workaround. Initial response target is 60 minutes.
- Sev-3: Limited impact issue affecting a subset of users. Initial response target is 4 business hours.
- Sev-4: Question, feature request, or cosmetic defect. Initial response target is 2 business days.

## Escalation guidance

- Escalate to engineering immediately for Sev-1 incidents.
- For Sev-2 incidents, confirm workaround availability before escalating.
- Product should be tagged when an issue has repeated customer impact across at least three accounts in a 7-day window.

## Knowledge authoring

- Every published article must include a summary, reproduction steps, mitigation steps, and ownership metadata.
- Release-note questions should be answered from the release notes rather than inferred from memory.

## AI assistant policy

- The assistant can summarize handbook policy when grounded in retrieved content.
- The assistant must disclose when the knowledge base is incomplete or has not been ingested.
- The assistant should keep the final response concise, cite sources where relevant, and avoid exposing chain-of-thought.
