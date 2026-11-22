"""Terminal presentation and keyboard controls for TicketForge."""

import os
import shutil
import textwrap
import sys
import unicodedata
from getpass import getpass
from contextlib import contextmanager
from datetime import datetime

try:
    from prompt_toolkit.application import Application, get_app
    from prompt_toolkit.formatted_text import ANSI, to_formatted_text
    from prompt_toolkit.formatted_text.utils import split_lines
    from prompt_toolkit.layout import HSplit, Layout, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.widgets import TextArea
    from prompt_toolkit.key_binding import KeyBindings
except ImportError:
    Application = None


def interactive():
    return bool(Application and sys.stdin.isatty() and sys.stdout.isatty()
                and os.environ.get("TERM") != "dumb")


def color_enabled():
    return interactive() and "NO_COLOR" not in os.environ


def display(value):
    """Keep external ticket text printable in the terminal."""
    return "".join(c if not unicodedata.category(c).startswith("C") else " "
                   for c in str(value))


_screen = ""
_messages = []
_presented = 0


def message(text):
    if interactive():
        _messages.append(text)
    else:
        print(text() if callable(text) else text)


def header(screen, username=None):
    global _screen, _presented
    _screen = display(screen) + (f"   ·   {display(username)}" if username else "")
    del _messages[:_presented]
    _presented = 0
    if not interactive():
        print(f"\nTicketForge CLI   |   Tomer Dahan's Assignment\n{_screen}\n  / Commands\n")


def fixed_prompt(label, bindings, *, content=None, hint="", default="", secret=False):
    """Render the current interaction inside the shared terminal frame."""
    global _presented
    _presented = len(_messages)

    def brand():
        title, attribution = "TicketForge CLI", "Tomer Dahan's Assignment"
        width = get_app().output.get_size().columns
        gap = width - len(title) - len(attribution) - 2
        space = " " * gap if gap >= 2 else "\n "
        return [("bold fg:#5599ff" if color_enabled() else "bold", " " + title),
                ("", space), ("fg:#b8bec8" if color_enabled() else "", attribution)]

    def body():
        parts = list(to_formatted_text(ANSI("\n".join(m() if callable(m) else m for m in _messages))))
        if parts:
            parts.append(("", "\n\n"))
        if content:
            parts.extend(content())
        return parts

    entry = TextArea(text=default, multiline=False, password=secret, height=1,
                     wrap_lines=False, prompt="❯ ",
                     accept_handler=lambda buffer: get_app().exit(result=buffer.text))
    entry.buffer.cursor_position = len(default)
    short_label = label.strip().rstrip(":› ").strip()

    def text_window(text, **kwargs):
        return Window(FormattedTextControl(text), **kwargs)

    scroll_line = [None]
    def scroll(event, direction):
        info = main.render_info
        if info:
            row = info.first_visible_line()
            scroll_line[0] = max(0, min(info.content_height - 1,
                                        row + direction * max(1, info.window_height - 1)))
            event.app.invalidate()

    @bindings.add("c-c")
    def interrupt(event):
        event.app.exit(exception=KeyboardInterrupt())

    @bindings.add("c-d")
    def end_input(event):
        if not event.current_buffer.text:
            event.app.exit(exception=EOFError())
        else:
            event.current_buffer.delete()

    @bindings.add("pageup")
    def previous_page(event):
        scroll(event, -1)

    @bindings.add("pagedown")
    def next_page(event):
        scroll(event, 1)

    def scrollable_body():
        parts = body()
        if scroll_line[0] is None:
            return parts
        lines = list(split_lines(parts))
        result = []
        for index, line in enumerate(lines):
            if index == scroll_line[0]:
                result.append(("[SetCursorPosition]", ""))
            result.extend((style, text) for style, text in line if "[SetCursorPosition]" not in style)
            result.append(("", "\n"))
        return result

    main = text_window(scrollable_body, wrap_lines=True)
    rule_style = "fg:#68778b" if color_enabled() else ""
    def rule():
        return Window(height=1, char="─", style=rule_style)

    root = HSplit([
        text_window(brand, dont_extend_height=True, wrap_lines=True),
        text_window(" " + _screen, height=1),
        Window(height=1), main,
        text_window(hint or "Ctrl-P Commands   ·   PgUp/PgDn Scroll", height=1),
        text_window(short_label, height=1), rule(), entry, rule(),
    ], height=lambda: get_app().output.get_size().rows)
    print("\033[H", end="", flush=True)
    app = Application(layout=Layout(root, focused_element=entry), key_bindings=bindings,
                      erase_when_done=False)
    return app.run()


class ExitRequested(Exception):
    """Leave the application from any screen."""


@contextmanager
def workspace():
    active = interactive()
    if active:
        print("\033[?1049h\033[2J\033[H", end="", flush=True)
    try:
        yield
    finally:
        if active:
            print("\033[0m\033[?1049l", end="", flush=True)


STAGE_COLORS = {"open": 35, "in_progress": 214, "review": 141, "closed": 25}


def tint(text, color):
    return f"\033[1;38;5;{color}m{text}\033[0m" if color_enabled() else text


def stage_label(stage):
    return display(stage).replace("_", " ").title()


def timestamp(value):
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return display(value)
        return parsed.astimezone().strftime("%d %b %Y · %H:%M %Z")
    except (TypeError, ValueError, AttributeError):
        return display(value)


def ticket_box(ticket):
    width = max(6, min(shutil.get_terminal_size().columns, 80))
    inside = width - 4
    lines = ["╭" + "─" * (width - 2) + "╮"]

    def row(text, color=None):
        # Use display columns for full-width characters and combining marks.
        line = ""
        used = 0
        for char in display(text):
            cells = 0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
            if used + cells > inside:
                lines.append("│ " + (tint(line, color) if color else line) + " " * (inside - used) + " │")
                line, used = "", 0
            line += char
            used += cells
        lines.append("│ " + (tint(line, color) if color else line) + " " * (inside - used) + " │")

    row(f"{ticket['ref']} · {ticket.get('title') or 'Untitled'}", 45)
    stage = ticket.get("stage") or ""
    row("Stage        " + stage_label(stage), STAGE_COLORS.get(stage))
    owner = ticket.get("owner") or {}
    for label, value in (
        ("Description", ticket.get("description") or "No description"),
        ("Depends on", ", ".join(ticket.get("dependsOn") or []) or "None"),
        ("Owner", owner.get("username") or "Unknown"),
        ("Created", timestamp(ticket.get("created"))),
        ("Updated", timestamp(ticket.get("updated"))),
    ):
        if label == "Owner":
            row("")
        prefix = f"{label:<13}" if inside >= 32 else f"{label}: "
        for line in textwrap.wrap(prefix + display(value), inside, subsequent_indent=""):
            row(line)
    lines.append("╰" + "─" * (width - 2) + "╯")
    return "\n".join(lines)


def palette(back=None):
    options = [("exit", "/exit   Quit TicketForge")]
    if back:
        options.append(("back", "/back   Go back"))
    options.append(("resume", "Resume"))
    command = menu(options, default="resume", commands=False)
    if command == "exit":
        raise ExitRequested
    return back if command == "back" else None


def field(label, *, secret=False, login=False):
    draft = ""
    while True:
        if interactive():
            bindings = KeyBindings()

            @bindings.add("c-p")
            def commands(event):
                event.app.exit(result=(event.current_buffer.text,))

            if login:
                @bindings.add("/")
                def login_commands(event):
                    event.app.exit(result=(event.current_buffer.text,))

            value = fixed_prompt(label, bindings, default=draft, secret=secret,
                                 hint="/ Commands   ·   Ctrl-P Commands" if login else "")
            if isinstance(value, tuple):
                draft = value[0]
                palette()
                continue
        else:
            value = getpass(label) if secret else input(label)
        if login and value == "/exit":
            raise ExitRequested
        if login and value == "/":
            palette()
            continue
        return value


def menu(options, default=None, *, commands=True, stages=None):
    """Choose by arrow keys or type a visible shortcut and press Enter."""
    keys = [key for key, _ in options]
    selected = keys.index(default) if default in keys else 0
    labels = [f"{key:>2}  {display(label)}" for key, label in options]
    back = next((k for k in ("b", "c", "n") if k in keys), None)
    if not interactive():
        if commands:
            print("  / Commands")
        for label in labels:
            print("  " + label)
        while True:
            key = input(f"Choose an option [Enter: {keys[selected]}]: ").strip().lower()
            if commands and key == "/exit":
                raise ExitRequested
            if commands and key == "/":
                action = palette(back)
                if action:
                    return action
                continue
            if not commands:
                key = key.lstrip("/")
            if not key:
                return keys[selected]
            if key in keys:
                return key
            print("Choose one of the shortcuts shown above.")

    bindings = KeyBindings()

    if commands:
        @bindings.add("/")
        def open_palette(event):
            event.app.exit(result="/")

    @bindings.add("up")
    @bindings.add("down")
    def move(event):
        nonlocal selected
        direction = 1 if event.key_sequence[0].key == "down" else -1
        selected = (selected + direction) % len(keys)
        event.current_buffer.reset()
        event.app.invalidate()

    def render():
        lines = []
        for index, label in enumerate(labels):
            active = index == selected
            style = "bold fg:ansicyan" if active and color_enabled() else ""
            if stages and keys[index] in stages and color_enabled():
                color = {"open": "#00af5f", "in_progress": "#ffaf00",
                         "review": "#af87ff", "closed": "#3575bd"}.get(stages[keys[index]])
                if color:
                    style = ("bold " if active else "") + "fg:" + color
            if active:
                lines.append(("[SetCursorPosition]", ""))
            lines.append((style, (" ❯ " if active else "   ") + label + "\n"))
        return lines

    while True:
        key = fixed_prompt("Choose an action" if commands else "Commands", bindings, content=render,
                           hint="↑ ↓ Move   ·   Enter Select   ·   Type a shortcut" +
                                ("   ·   / Commands" if commands else "")).strip().lower()
        if commands and key == "/":
            action = palette(back)
            if action:
                return action
            continue
        if not commands:
            key = key.lstrip("/")
        if not key:
            return keys[selected]
        if key in keys:
            return key
        message("Choose one of the shortcuts shown above.")


def checklist(candidates, initial):
    refs = list(candidates)
    selected = set(initial)
    focus = 0
    if not interactive():
        for n, ref in enumerate(refs, 1):
            print(f"{n}. [{'x' if ref in selected else ' '}] {display(ref)}  {display(candidates[ref])}")
        while True:
            value = input("Toggle by number, Enter to apply, c to cancel: ").strip()
            if not value:
                break
            if value == "c":
                return None
            if value == "/exit":
                raise ExitRequested
            if value in [str(n) for n in range(1, len(refs) + 1)]:
                selected.symmetric_difference_update([refs[int(value) - 1]])
                print(f"{len(selected)} selected")
    else:
        bindings = KeyBindings()

        @bindings.add("up")
        @bindings.add("down")
        def move(event):
            nonlocal focus
            focus = (focus + (1 if event.key_sequence[0].key == "down" else -1)) % len(refs)
            event.app.invalidate()

        @bindings.add(" ")
        def toggle(event):
            selected.symmetric_difference_update([refs[focus]])
            event.app.invalidate()

        @bindings.add("escape")
        def cancel(event):
            event.app.exit(result="cancel")

        @bindings.add("/")
        def commands(event):
            event.app.exit(result="/")

        def render():
            rows = []
            for i, ref in enumerate(refs):
                mark = "✓" if ref in selected else " "
                prefix = "❯" if i == focus else " "
                style = "bold fg:ansicyan" if color_enabled() and i == focus else ""
                if i == focus:
                    rows.append(("[SetCursorPosition]", ""))
                rows.append((style, f"{prefix} [{mark}] {display(ref)}  {display(candidates[ref])}\n"))
            return rows

        while True:
            result = fixed_prompt("Choose dependencies", bindings, content=render,
                                  hint="↑ ↓ Move   ·   Space Toggle   ·   Enter Apply   ·   Esc Cancel   ·   / Commands")
            if result == "cancel":
                return None
            if result != "/":
                break
            if palette("cancel"):
                return None
    return [ref for ref in refs if ref in selected]
