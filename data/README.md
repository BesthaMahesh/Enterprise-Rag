# Enterprise HR RAG + ACL Knowledge Base

This dataset is designed around the enterprise RAG lifecycle:
Data ingestion -> parsing/cleaning -> semantic/structural chunking -> metadata + ACL + versioning
-> dense + sparse indexing -> hybrid retrieval -> fusion -> reranking -> context construction
-> token budgeting -> LLM -> grounded/citation validation -> evaluation -> observability.

## Main demonstration
Employee login:
- Can retrieve employee-accessible policies.
- Cannot retrieve HR/private/company-financial documents.
- Prompt injection cannot override ACL.

HR login:
- Can retrieve employee-accessible and HR-authorized private documents.
- Can answer synthetic company/HR financial questions from authorized documents.

Admin login:
- Can retrieve all synthetic restricted documents in this demonstration.

## Critical security rule
ACL must be applied before retrieval/context construction. Do not retrieve all documents and ask the LLM to hide unauthorized information.

## Important distinction
General company/private knowledge -> RAG with ACL.
Personal live information such as an employee's current salary or leave balance -> authorized HR/payroll API or database, not unrestricted RAG.

All financial values in this package are fictional demonstration data.
