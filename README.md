# integration-cli

## Login

From the repository root, run `python3 cli.py` with Python 3.
The CLI uses the standard library and requires an existing TicketForge account.

Enter your username and password at the prompts. The password is hidden while
you type. After a successful login, press Enter to log out and discard the
in-memory credentials. At the username prompt, press Enter to exit.

## Create a ticket

After signing in, choose `1`, then enter a title and description. For example,
enter `Fix dashboard filter` and `Closed tickets appear in the open view.`
At the dependencies prompt, press Enter to skip, or choose `1` to view the
tickets returned by TicketForge. Enter one or more displayed references, such as
`TF-784, TF-783`, or enter `c` to cancel creation.
The CLI prints the assigned reference (for example, `Created TF-784.`) and
returns to the menu.

## List tickets

Choose `2` to see your first five tickets. When more are available, enter `m`
to append the next five. Enter any displayed row number to view its details.
Press Enter to return to the expanded list, or Enter at the list to go back.

## Edit a ticket

Choose `2. List and edit tickets`, enter a ticket number, then press `e` and Enter to edit.
Press Enter to keep a value, or type `/clear` to clear the description or
dependencies. Enter replacement dependencies as comma-separated references.
For stage, choose 1 (Open), 2 (In Progress), 3 (Review), or 4 (Closed).
Type `y` at the save prompt to submit the changes.
