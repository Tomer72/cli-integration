# Create ticket · approved

## Brief
Create a ticket and optionally select existing tickets it depends on.

## Scope
Title, description, and dependency selection during creation. Custom fields and the standalone list command remain separate features.

## Files involved
- `cli.py` prompts for ticket details and dependency choices.
- `client.py` retrieves candidate tickets and publishes the new ticket.
- `README.md` gives a short example with dependencies.

## Requirements
- Require a nonblank title and prompt for a description. Enter skips dependencies and preserves the existing single-POST flow.
- When selection is requested, show existing tickets by reference and title. Accept one or more comma-separated references; explain invalid choices before submitting. If the lookup fails, let the user choose how to proceed.
- Send one authenticated JSON POST to `/api/tforge/workitem/publish`. With no selection, send `dependsOn: null`. For selected dependencies, send an array of ticket references. The captured two-ticket example is `"dependsOn": ["TF-784", "TF-783"]`. For one selection, use a one-element array.
- Print `workitem.ref` on success. Return to login on 401. Report unconfirmed creation without automatically retrying.

## Design
Reuse `TicketForgeClient` for the authenticated candidate lookup and extend `create_ticket` with optional dependency references. Keep selection and display in `cli.py`.

## Tasks
1. Add the picker and extend the client on approval.
2. Update the usage example and exercise the revised flow.

## Validation
Simulate zero, one, and multiple selections; inspect the outgoing JSON and displayed reference. Check an invalid choice, an empty list, a failed lookup, a blank title, a 401, and a lost publish response. Verify each submitted ticket causes exactly one POST.
