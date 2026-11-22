# Feature workflow

Work on one feature at a time. Follow the agreed order: login, create ticket, list tickets, update ticket, tests/logging/verification, UI and user experience, then expanded capabilities.

1. Create a dedicated branch named `cli/<feature>` using a short descriptive name, such as `cli/login`, `cli/create`, `cli/list`, or `cli/update`.
2. Write a short spec in `docs/specs/<feature>.md` using the headings below. Mark it pending approval. If information is missing, ask one question at a time.
3. Present the spec and wait for explicit user approval before coding. If the user requests revisions, update the spec and present it again.
4. Implement the approved scope. Verify each feature as it is built, including those that precede the dedicated testing phase.
5. Personally simulate the manual workflow through the normal CLI entry point. Report the actions taken, observed results, and whether verification used simulated responses or the live service.

## Spec template

Use the following seven headings in order. Keep each section short enough to review quickly.

- **Brief** — State the user-facing outcome in one sentence.
- **Scope** — Define what this feature covers and any closely related work deferred.
- **Files involved** — List the files to create or change and each file's purpose.
- **Requirements** — Describe observable behavior, including relevant failure cases.
- **Design** — Name the key functions and any classes. Explain their responsibilities and what later features can reuse. Introduce a class only when it serves a concrete purpose.
- **Tasks** — List the few implementation steps in order.
- **Validation** — Give the manual actions to simulate and the expected results for success and relevant failures.
