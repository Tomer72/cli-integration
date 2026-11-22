# Edit ticket · approved

## Brief
Open a ticket from the numbered list, edit it, and see the saved result.

## Scope
Edit title, description, stage, and dependencies. Preserve existing custom field values; editing custom fields is proposed for the expansion phase.

## Files involved
- `cli.py` offers Edit from ticket details and prompts for changes.
- `client.py` reads the current values needed for editing and submits the update.
- `README.md` documents one edit example.

## Requirements
- Show current values. Enter keeps a value. Allow an explicit clear for description or dependencies. Require a nonblank title.
- At Stage, show the current stage and four numbered choices: 1 Open, 2 In Progress, 3 Review, 4 Closed. One ticket has one active stage. Enter keeps the current stage; an invalid selection prompts again. Send open, in_progress, review, or closed respectively.
- Offer Save and Cancel. Cancel or an unchanged edit sends no update.
- After a successful save, show the saved details and retain the user's list position. Handle expired login and failed or unconfirmed saves.

## Design
Read the selected ticket with GET /api/tforge/workitem/{ref}?view=deep. An omitted customFields object represents no saved values. Send title, description, stage, dependsOn, and customFields in the PUT, preserving custom field values and their JSON types. Refresh the deep view after saving.

## Tasks
1. Confirm the update contract and field formats.
2. Implement the edit prompts, authenticated PUT, and detail refresh.
3. Document and verify the flow.

## Validation
Simulate a stage-only edit and verify other values survive. Check dependency replacement and clearing, invalid input, cancel, unchanged edits, a 401, and a lost save response.

For the stage picker, exercise all four choices, Enter to keep, and an invalid choice followed by a valid selection. Verify the saved API stage.
