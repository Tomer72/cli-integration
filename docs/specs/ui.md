# Terminal interface · approved

## Brief
Make TicketForge easy to navigate from the keyboard, with a compact bold header and a clear next action on every screen.

## Scope
Login, home menu, create prompts, dependency selection, ticket browsing, details, and edit prompts.

## Files involved
- `ui.py` renders headers, menus, status messages, and keyboard prompts.
- `cli.py` connects those controls to the existing flows.
- `requirements.txt` declares prompt_toolkit. `README.md` documents installation and controls.

## Requirements
- Show a bold TicketForge title bar with the current screen and signed-in username when available. Give the login screen labeled username and hidden-password prompts.
- Put one menu action per line. Highlight the current row with a pointer and color. Support arrows and Enter on menus, with numbered shortcuts for ticket and stage selection. Make Edit, Back, Load five more, Cancel, and Log out visible where applicable.
- Keep input and feedback close together. Label errors and successes in words. Wrap long titles and give narrow or color-disabled terminals a readable layout.

- Open in the terminal’s alternate screen, give the header, content, and action hints separate rows, and restore the shell on exit or interruption.
- For create and edit, use one dependency checklist: arrows move, Space toggles, Enter applies, and Escape cancels. Preselect existing dependencies during editing.
- Open ticket details with a deep read. Show the owner username and local creation/update times with date and timezone. Label the owner accurately; use a creator label only when the API identifies a creator.
- Use consistent stage labels and colors in the list, details, and editor: Open green, In Progress amber, Review violet, Closed deep blue with legible contrast. Distinguish current and changed values with text as well as color.
- Show a slash-command hint. At login and navigation menus, / opens a palette with /exit (quit) and /back where applicable. During text entry use a dedicated palette shortcut so ticket text and passwords stay literal. Blank input at login keeps the prompt open.

- Anchor a one-line header to the top of the interactive terminal. Show bold blue “TicketForge CLI” on the left and light-grey “Tomer Dahan’s Assignment” on the right. On narrow terminals, stack the two labels.
- Anchor the active prompt between two horizontal rules near the bottom. Keep its cursor on the same row across screens and show the active field name or menu hint. Keep password input masked.
- Put menus, ticket details and feedback in the space between header and input. Keep focused options visible as the content scrolls or the window resizes.

- Title the login screen “Sign in to TicketForge”. Prompt with “Enter your username” and “Enter your password (hidden)”. Use action labels for ticket inputs, such as “Enter a ticket title” and “Enter a description”. When editing, show the current value and explain that Enter keeps it.
- Frame the selected ticket and the refreshed ticket after saving in a width-aware box. Place the reference and title first, then stage, description, dependencies, owner, and timestamps. Wrap long content inside the border and keep Edit and Back outside it.

## Design
Use prompt_toolkit for interactive input. Keep presentation in small functions in ui.py. Use the terminal's background, a cyan accent for the header and focus, and a blank line between the title bar, actions, and key hints. Use plain numbered input when interactive controls are unavailable.

Format timestamps with the Python standard library. Reuse the existing deep ticket endpoint and preserve plain input and no-color support.

Use a persistent prompt_toolkit layout with a header, scrollable content area, and bottom input. Retain the line-based fallback for plain terminals.

## Tasks
1. Build the header, login prompts, and menu controls.
2. Apply them across create, browse, and edit, then update usage instructions.

3. Apply the full-screen, checklist, ticket metadata, stage color, and command palette refinements.

## Validation
Drive the CLI through a simulated login, creation, pagination, selection, stage edit, save, and logout. Check arrow keys, numbers, Enter, cancellation, a failed login, a narrow terminal, and plain-text output.

Verify the alternate screen restores on exit and Ctrl-C, select multiple dependencies and cancel a change, check a timestamp across a date boundary, and exercise the palette and stage labels with color on and off.

Check that the cursor stays on the same row across login, menus, and edit prompts at a fixed window size, and that resizing keeps the prompt visible.

Verify sign-in and ticket prompts in interactive and plain modes, and inspect the detail box with a long description in wide and narrow terminals.
