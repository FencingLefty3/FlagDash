import json
import shutil
import time
import os
import sys
import re
import subprocess
from . import stats as stats_mod
from . import settings as themes
from datetime import datetime
from pathlib import Path
First = True
powershell_path = shutil.which("powershell.exe")

SRCDir = Path(__file__).parent.resolve()
levels = SRCDir / "levels.json"

logo = r"""

    
          ▀▀▀▀▀ ▀     ▀▀▀▄  ▀▀▀▀▀
▀▀▀▀ ▀▀▀▀ ▄ ▀▀  █     ▄ ▀▀█ ▄ ▀▀█
          █      ▀▄▄▄ ▀   ▀  ▀▄▄▀    

"""
HELP = "For a Hint, respond 'hint'.\nTo reset the question,'reset' For these keywords, 'help'\nTo Close, 'quit' or 'exit'.\n"

def runLevel(Title, question, answers, hints=(), setup=(), case_sensitive=False, run=False, check=None, stats=None, n=0):
    global First

    for cmd in (setup or []):
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       capture_output=True) 

    if First is False:
        os.system('cls' if os.name == 'nt' else 'clear')

        print(themes.secondary(logo)) 
    First = False
    time.sleep(.5)
    print(themes.secondary(f"== {Title} =="))
    print(themes.primary(f"{question}\n"))

    if setup:
        for s in setup:
            subprocess.run(s, shell=True, executable=powershell_path)

    norm = (lambda s: s.strip()) if case_sensitive else (lambda s: s.strip().lower())
    accepted = {norm(a) for a in answers}
    hintsUsed = 0
    wrong = 0
    start = time.monotonic()

    def finish(solved):
        if stats is not None:
            stats_mod.record_level(stats, n, Title, wrong, hintsUsed, time.monotonic() - start, solved)
            stats_mod.save(stats)
        return solved


    while True: 
        try:
            responce = input(">> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return(False)

        cmd = responce.strip().lower()
        if cmd == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            
            
            print(themes.secondary(logo)) 
            time.sleep(.5)
            print(f"== {Title} ==")
            print(f"{question}\n")
            continue
        if cmd == "help":
            print(themes.info(HELP))
            continue
        if cmd in ("quit", "exit"):
            print("Goodbye!")
            time.sleep(.5)
            return False
        if cmd == "hint":
            if hintsUsed < len(hints):
                print(themes.info(f"Hint {hintsUsed + 1}: {hints[hintsUsed]}"))
                hintsUsed += 1
            else:
                print(themes.info("Final hint given" if hints else "No hints available."))
            continue   
        if not responce.strip():
            continue

        correct = check(responce) if check else norm(responce) in accepted
        if correct:
            print(themes.success("Correct!"))

            for i in range(1, 4):
                dots = "." * (i % 4)

                print(f"\rLoading{dots.ljust(3)}", end="", flush=True)
                time.sleep(0.5)

            #if run == True:
            #    print(subprocess.run(answers, shell=True))

            return finish(True)
        wrong += 1
        print(themes.error("Sorry, try again. \n"))

def run(save):
    global First

    os.system('cls' if os.name == 'nt' else 'clear')


    print(themes.secondary(logo)) 
    time.sleep(.5)
    print(themes.info(HELP))

    with open(levels, "r", encoding="utf-8") as f:
        LEVELS = json.load(f)
        stats = stats_mod.load()
        stats_mod.start_session(stats)

    currentLevel = save["level"]

    if currentLevel >= len(LEVELS):
        print("This save is compleated.")
        return


    for i in range(currentLevel, len(LEVELS)):
        if not runLevel(n=i + 1, stats=stats, **LEVELS[i]):
            print("Exiting...")
            return

        

        save_game(save["name"], i + 1, i + 1 >= len(LEVELS))
        
    print("You have beat the game!")   


def new_game():

    print("== New Game ==")

    try:
        name = input("Save Name: ")
    except (EOFError, KeyboardInterrupt):
        print()
        return(False)

    if not name:
        name = "Player"

    if any(s["name"].lower() == name.lower() for s in get_saves()):
        print("Save already Exists")
        return

    save = {
        "name": name,
        "level": 0,
        "completed": False
    }

    save_game(name, 0)
    run(save)




def save_dir():
    if os.name == "nt":
        base = Path(os.getenv("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    folder = base / "DashFlag" / "saves"
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def save_game(name, level, completed=False):
    folder = save_dir()

    filename = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    path = folder / f"{filename}.json"

    data = {
        "name": name,
        "level": level,
        "completed": completed,
        "last_played": datetime.now().isoformat(timespec="seconds")
    }

    tempPath = path.with_suffix(".tmp")
    with open(tempPath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    tempPath.replace(path)

def get_saves():
    folder = save_dir()
    saves = []

    for path in folder.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["path"] = path
                saves.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(saves, key=lambda s: s.get("last_played", ""), reverse=True)

def delete():
    saves = get_saves()

    print("== Delete Saves==\n")

    if not saves:
        print("No saves found.")
        return
    for i, save in enumerate(saves, 1):
        status = "Completed" if save["completed"] else f"Level {save['level'] + 1}"
        print(f"{i} | {save['name']} - {status}")

    print("\n Enter save number to delete, or 'exit'.")

    while True:
        try:
            responce = input(">> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if responce == "exit":
            return
        if not responce.isdigit() or not 1 <= int(responce) <= len(saves):
            print("Invalid.")
            continue

        save = saves[int(responce) - 1]

        try:
            confirm = input(
                f"Delete save '{save['name']}'? This cannot be undone. (y/N): "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if confirm == "y":
            try:
                save["path"].unlink()
                print(f"Save '{save['name']}' deleted.")
            except OSError as error:
                print(f"Failed to delete save '{save['name']}'. {error}")
            return
        elif confirm == "n" or confirm == "":
            print("Deletion cancelled.")
            return
    
def theme_cmd(args):
    arg = args[0].lower() if args else ""
    if arg == "path":
        print(themes.SETTINGS)
    elif arg in themes.PRESETS:
        themes.apply_preset(arg)
        print(f"Theme set to {arg}. Edit {themes.SETTINGS} to customise.")
    else:
        print("Themes: " + ", ".join(themes.PRESETS))
        print("Use: DashFlag settings <name>   or   DashFlag settings path")


def show_stats():
    with open(levels, "r", encoding="utf-8") as f:
        total_levels = len(json.load(f))
    stats_mod.show(stats_mod.load(), total_levels)


def load():
    saves = get_saves()

    os.system('cls' if os.name == 'nt' else 'clear')

    
    print(themes.secondary(logo)) 
    time.sleep(.5)
    print("== Load Save ==\n")


    if not saves:
        print("No saves found.")

        return None

    for i, save in enumerate(saves, 1):
        status = "Completed" if save["completed"] else f"Level {save['level'] + 1}"

        print(f"{i} | {save['name']} - {status}")

    print("\n Enter save number to load, 'stats', 'settings', 'delete' or 'exit'.")

    while True:
        try:
            responce = input(">> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return(False)

        if responce == "exit":
            return None

        if responce.isdigit() and 1<= int(responce) <= len(saves):
            return saves[int(responce) - 1]

        if responce == "delete":
            delete()
            return None

        if responce == "settings":
            themes.select_theme()
            continue

        if responce == "stats":
            show_stats()
            return None
        
        print("Invalid.")

def main():

    for problem in themes.load():
        print(problem)

    command = sys.argv[1].lower() if len(sys.argv) > 1 else ""

    if command:
        if command == "load":
            save = load()

            if save:
                run(save)

        elif command == "new":
            new_game()

        elif command == "delete":
            delete()

        elif command == "stats":
            stats = stats_mod.load()
            total_levels = len(json.load(open(levels, "r", encoding="utf-8")))
            stats_mod.show(stats, total_levels)

        elif command == "settings":
            themes.select_theme()
        else:
            print("Invalid.")
    else:

        try:
            command = input("Ḻoad(L) or ṉew (L/n)? ").lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return(False)

        if command == "l" or command == "load" or command == "":
            save = load()

            if save:
                run(save)

        elif command == "n" or command == "new":
            new_game()

        else:
            print("Invalid.")