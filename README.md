# TicketForge CLI

## Login

From the repository root, install the interactive controls and launch the CLI:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python cli.py

Use an existing TicketForge account. Move through menus with the up and down
arrows, then press Enter. You can also type a displayed shortcut and press
Enter. Plain terminals use the same shortcuts. Set `NO_COLOR=1` to disable colors.

Enter your username and password at the prompts. The password is hidden while
you type. After a successful login, choose **Log out** from Home to discard the
in-memory credentials. Use `/exit` to quit. In an interactive terminal, `/` opens Commands at login or in a menu; press Ctrl-P while editing text. Quitting restores your shell screen.

## Create a ticket

After signing in, choose `1`, then enter a title and description. For example,
enter `Fix dashboard filter` and `Closed tickets appear in the open view.`
At the dependencies prompt, press Enter to skip, or choose `1` to view the
tickets returned by TicketForge. Use ↑/↓ to move, Space to toggle dependencies, and Enter to apply. Esc cancels the selection. In plain mode, toggle by number.
The CLI prints the assigned reference (for example, `Created TF-784.`) and
returns to the menu.

## List tickets

Choose `2` to see your first five tickets. When more are available, enter `m`
to append the next five. Enter any displayed row number to view its details.
Choose **Back to tickets** to return to the expanded list, or choose **Back to home** to leave the list.

## Edit a ticket

Choose `2. List and edit tickets`, enter a ticket number, then press `e` and Enter to edit.
Ticket details show the owner and local timestamps. Press Enter to keep a value, or type `/clear` to clear the description. Choose **Select dependencies** to change the preselected tickets. Clear all checkmarks to remove dependencies.
For stage, choose 1 (Open), 2 (In Progress), 3 (Review), or 4 (Closed).
Type `y` at the save prompt to submit the changes.
