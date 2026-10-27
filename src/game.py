import json
import time
import os
import subprocess
from pathlib import Path
First = True

SRCDir = Path(__file__).parent.resolve()
levels = SRCDir / "levels.json"

def runLevel(Title, question, answers, hints=(), case_sensitive=False, run=False, check=None):
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

        if cmd in ("quit", "exit"):
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

def run():


    logo = r"""


          ▀▀▀▀▀ ▀     ▀▀▀▄  ▀▀▀▀▀
▀▀▀▀ ▀▀▀▀ ▄ ▀▀  █     ▄ ▀▀█ ▄ ▀▀█
          █      ▀▄▄▄ ▀   ▀  ▀▄▄▀ 

"""

    print(f"{logo}") 
    time.sleep(.5)
    print("For a Hint, respond 'hint'.\nTo Close, 'quit' or 'exit'.\n")

    with open(levels, "r", encoding="utf-8") as f:
        LEVELS = json.load(f)

    for level in LEVELS:
        if not runLevel(**level):
            print("Exiting...")
            return
    print("You have beat the game!")
           
           
           

run()