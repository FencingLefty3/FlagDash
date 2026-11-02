import json
import os
import sys
from pathlib import Path


PRESETS = {
    "default": {"PrimaryColor": "", "SecondaryColor": "", "errorColor": "",
                "successColor": "", "infoColor": ""},
    "matrix":  {"PrimaryColor": "bright_green", "SecondaryColor": "green",
                "errorColor": "bright_red", "successColor": "bright_green", "infoColor": "green"},
    "retro":   {"PrimaryColor": "bright_magenta", "SecondaryColor": "bright_blue",
                "errorColor": "bright_red", "successColor": "bright_green", "infoColor": "bright_yellow"},
    "sepia":   {"PrimaryColor": "f4ecd8", "SecondaryColor": "b8860b",
                "errorColor": "124", "successColor": "142", "infoColor": "109"},
}

NAMED = {
    "black": "\033[30m", "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
    "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m", "white": "\033[37m",
    "bright_red": "\033[91m", "bright_green": "\033[92m", "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m", "bright_magenta": "\033[95m", "bright_cyan": "\033[96m",
    "gray": "\033[90m", "orange": "\033[38;5;208m", "pink": "\033[38;5;13m",
    "purple": "\033[38;5;93m", "teal": "\033[38;5;6m", "brown": "\033[38;5;94m",
}

SETTINGS = Path.home() / ".dashflag" / "settings.json"
KEYS = ("PrimaryColor", "SecondaryColor", "errorColor", "successColor", "infoColor")

RESET_FG = "\033[39m"
_colors = {}
_enabled = False

def _parse(value):
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if not v:
        return ""
    if v in NAMED:
        return NAMED[v]
    if v.isdigit() and 0 <= int(v) <= 255:
        return f"\033[38;5;{int(v)}m"
    h = v.lstrip("#")
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    if len(h) == 6:
        try:
            r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
            return f"\033[38;2;{r};{g};{b}m"
        except ValueError:
            pass
    return None

def write_settings(values):
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS.with_suffix(".tmp")
    tmp.write_text(json.dumps(values, indent=4), encoding="utf-8")
    tmp.replace(SETTINGS)

def load():
    global _enabled

    _enabled = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    if os.name == "nt":
        os.system("")

    problems = []
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError
    except FileNotFoundError:
        data = dict(PRESETS["default"])
        try:
            write_settings(data)
        except OSError:
            pass
    except (json.JSONDecodeError, ValueError, OSError):
        problems.append("settings.json isn't valid JSON (no comments or trailing commas). Using defaults. "
                   "Run 'DashFlag theme default' to repair it.")
        data = dict(PRESETS["default"])

    for key in KEYS:
        parsed = _parse(data.get(key, ""))
        if parsed is None:
            problems.append(f"{key}: '{data.get(key)}' isn't a color.")
            parsed = ""
        _colors[key] = parsed
    return problems

def _wrap(key, text):
    code = _colors.get(key, "")
    if not _enabled or not code:
        return text
    return f"{code}{text}{RESET_FG}"

def primary(t):   return _wrap("PrimaryColor", t)
def secondary(t): return _wrap("SecondaryColor", t)
def error(t):     return _wrap("errorColor", t)
def success(t):   return _wrap("successColor", t)
def info(t):      return _wrap("infoColor", t)

def apply_preset(name):
    name = name.lower()
    if name not in PRESETS:
        return False
    write_settings(PRESETS[name])
    load()
    return True

def _paint(values, key, text):
    code = _parse(values.get(key, ""))
    if not _enabled or not code:
        return text
    return f"{code}{text}{RESET_FG}"


def select_theme():
    names = list(PRESETS)

    print("== Themes ==\n")
    for i, name in enumerate(names, 1):
        p = PRESETS[name]
        sample = " ".join([
            _paint(p, "SecondaryColor", "title"),
            _paint(p, "PrimaryColor", "question"),
            _paint(p, "infoColor", "hint"),
            _paint(p, "successColor", "correct"),
            _paint(p, "errorColor", "wrong"),
        ])
        print(f"{i} | {name:<8} {sample}")

    print("\n Enter theme number, or 'exit'.")

    while True:
        try:
            response = input(">> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if response == "exit":
            return

        if response.isdigit() and 1 <= int(response) <= len(names):
            name = names[int(response) - 1]
            apply_preset(name)
            print(f"Theme set to {name}. Edit {SETTINGS} to customise.")
            return

        print("Invalid.")