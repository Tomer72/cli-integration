# List tickets · approved

## Brief
Show the first five tickets and let the user expand the list five at a time.

## Scope
Read-only browsing and numbered selection across the tickets loaded so far.

## Files involved
- `client.py` fetches one page at a time.
- `cli.py` manages the displayed rows and menu choices.
- `README.md` documents expansion and selection.

## Requirements
- Opening List tickets fetches only the first page with `limit=5`.
- When `hasMore` is true, offer `m` (Show 5 more). Each selection fetches one page and appends its rows. Existing numbers stay the same. Hide the option after the final page.
- Enter a row number for details. Enter returns to the expanded list without refetching; Enter at the list returns to the menu.
- Handle invalid choices, empty results, and expired credentials. If an expansion request fails, keep the loaded rows available and allow retry. Stop expansion on a missing or repeated cursor.

## Design
Have TicketForgeClient return rows and continuation information for one request. The CLI holds the loaded rows and cursor for the current visit, and sends the URL-encoded cursor only when the user requests more.

## Tasks
1. Replace eager pagination with single-page retrieval and an expand action.
2. Update the usage example and verify navigation.

## Validation
Simulate 12 tickets. Confirm the first view makes one list request and shows rows 1–5. Expand twice to see rows 1–10 and then 1–12. Verify stable selection, back navigation, the final menu, and recovery from a failed expansion.
