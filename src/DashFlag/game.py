import json
import shutil
import time
import os
import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path
First = True
powershell_path = shutil.which("powershell.exe")

SRCDir = Path(__file__).parent.resolve()
levels = SRCDir / "levels.json"

def runLevel(Title, question, answers, hints=(), setup=(), case_sensitive=False, run=False, check=None):
    global First
    
    if First is False:
        os.system('cls' if os.name == 'nt' else 'clear')

        logo = r"""

          ▀▀▀▀▀ ▀     ▀▀▀▄  ▀▀▀▀▀
▀▀▀▀ ▀▀▀▀ ▄ ▀▀  █     ▄ ▀▀█ ▄ ▀▀█
          █      ▀▄▄▄ ▀   ▀  ▀▄▄▀ 
            
    """

        print(f"{logo}") 
    First = False
    time.sleep(.5)
    print(f"== {Title} ==")
    print(f"{question}\n")

    if setup:
        for s in setup:
            subprocess.run(s, shell=True, executable=powershell_path)
            print(s)

    norm = (lambda s: s.strip()) if case_sensitive else (lambda s: s.strip().lower())
    accepted = {norm(a) for a in answers}
    hintsUsed = 0

    while True: 
        try:
            responce = input(">> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return(False)

        cmd = responce.strip().lower()
        if cmd == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            
            logo = r"""
            
          ▀▀▀▀▀ ▀     ▀▀▀▄  ▀▀▀▀▀
▀▀▀▀ ▀▀▀▀ ▄ ▀▀  █     ▄ ▀▀█ ▄ ▀▀█
          █      ▀▄▄▄ ▀   ▀  ▀▄▄▀ 
                        
            """
            
            print(f"{logo}") 
            time.sleep(.5)
            print(f"== {Title} ==")
            print(f"{question}\n")
            continue
        if cmd == "help":
            print("For a Hint, respond 'hint'.\nTo reset the question,'reset' For these keywords, 'help'\nTo Close, 'quit' or 'exit'.\n")
            continue
        if cmd in ("quit", "exit"):
            print("Goodbye!")
            time.sleep(.5)
            return False
        if cmd == "hint":
            if hintsUsed < len(hints):
                print(f"Hint {hintsUsed +1}: {hints[hintsUsed]}")
                hintsUsed += 1
            else:
                print("Final hint given" if hints else "No hints available.")
            continue   
        if not responce.strip():
            continue

        correct = check(responce) if check else norm(responce) in accepted
        if correct:
            print("Correct!")

            for i in range(1, 4):
                dots = "." * (i % 4)

                print(f"\rLoading{dots.ljust(3)}", end="", flush=True)
                time.sleep(0.5)

            #if run == True:
            #    print(subprocess.run(answers, shell=True))

            return True

        print("Sorry, try again. \n")

def run(save):
    global First

    os.system('cls' if os.name == 'nt' else 'clear')

    logo = r"""


          ▀▀▀▀▀ ▀     ▀▀▀▄  ▀▀▀▀▀
▀▀▀▀ ▀▀▀▀ ▄ ▀▀  █     ▄ ▀▀█ ▄ ▀▀█
          █      ▀▄▄▄ ▀   ▀  ▀▄▄▀ 

"""

    print(f"{logo}") 
    time.sleep(.5)
    print("For a Hint, respond 'hint'.\nTo reset the question,'reset' For these keywords, 'help'\nTo Close, 'quit' or 'exit'.\n")

    with open(levels, "r", encoding="utf-8") as f:
        LEVELS = json.load(f)

    currentLevel = save["level"]

    if currentLevel >= len(LEVELS):
        print("This save is compleated.")
        return


    for i in range(currentLevel, len(LEVELS)):
        if not runLevel(**LEVELS[i]):
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

def load():
    saves = get_saves()

    os.system('cls' if os.name == 'nt' else 'clear')
    
    logo = r"""

    
          ▀▀▀▀▀ ▀     ▀▀▀▄  ▀▀▀▀▀
▀▀▀▀ ▀▀▀▀ ▄ ▀▀  █     ▄ ▀▀█ ▄ ▀▀█
          █      ▀▄▄▄ ▀   ▀  ▀▄▄▀    

    """
    
    print(f"{logo}") 
    time.sleep(.5)
    print("== Load Save ==\n")


    if not saves:
        print("No saves found.")

        return None

    for i, save in enumerate(saves, 1):
        status = "Completed" if save["completed"] else f"Level {save['level'] + 1}"

        print(f"{i} | {save['name']} - {status}")

    print("\n Enter save number to load or 'exit'.")

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


        print("Invalid.")

def main():

    try:
        command = input("Ḻoad(L) or ṉew (L/n)? ")
    except (EOFError, KeyboardInterrupt):
        print()
        return(False)

    if command == "":
        save = load()
        
        if save:
            run(save)

    elif command == "load":
        save = load()

        if save:
            run(save)

    elif command == "new":
        new_game()

    else:
        print("Invalid.")