import copy
import json
from datetime import datetime
import os
from pathlib import Path

StATSDir = Path.home() / ".DashFlag"
STATSFile = StATSDir / "stats.json"

DEFAULT = {
    "sessions": 0,
    "first_played": None,
    "last_played": None,
    "highest_reached": 0,
    "highest_solved": 0,
    "total_wrong": 0,
    "total_hints": 0,
    "total_seconds": 0,
    "levels": {},
}

def load():
    try:
        data = json.loads(STATSFile.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = {}
    stats = copy.deepcopy(DEFAULT)
    stats.update(data)

    return stats

def save(stats):
    try:
        StATSDir.mkdir(exist_ok=True)
        tmp = STATSFile.with_suffix(".tmp")
        tmp.write_text(json.dumps(stats, indent=2), encoding="utf-8")
        tmp.replace(STATSFile)
    except OSError:
        pass

def reset():
    stats = copy.deepcopy(DEFAULT)
    save(stats)
    return stats

def start_session(stats):
    now = datetime.now().isoformat(timespec="seconds")
    stats["sessions"] += 1
    stats["first_played"] = stats["first_played"] or now
    stats["last_played"] = now

def record_level(stats, n, title, wrong, hints, seconds, solved):
    stats["highest_reached"] = max(stats["highest_reached"], n)
    stats["total_hints"] += hints
    stats["total_seconds"] += seconds
    stats["total_wrong"] += wrong

    lv = stats["levels"].setdefault(title, {
        "number": n, "plays": 0, "solved": False, 
        "hints": 0, "wrong": 0, "best_seconds": None,
    })
    lv["number"] = n
    lv["plays"] += 1
    lv["hints"] += hints
    lv["wrong"] += wrong

    if solved:
        lv["solved"] = True
        stats["highest_solved"] = max(stats["highest_solved"], n)
        if lv["best_seconds"] is None or seconds < lv["best_seconds"]:
            lv["best_seconds"] = round(seconds, 1)

def fmt_time(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"

def show(stats, total_levels):
    levels = stats["levels"]
    solved = [t for t, v in levels.items() if v["solved"]]

    os.system('cls' if os.name == 'nt' else 'clear')

    logo = r"""

    
          ▀▀▀▀▀ ▀     ▀▀▀▄  ▀▀▀▀▀
▀▀▀▀ ▀▀▀▀ ▄ ▀▀  █     ▄ ▀▀█ ▄ ▀▀█
          █      ▀▄▄▄ ▀   ▀  ▀▄▄▀    

    """
    
    print(f"{logo}") 

    print(f"\n== Stats ==\n")
    print(f"Highest level reached | {stats['highest_reached']} / {total_levels}")
    print(f"Highest level solved  | {stats['highest_solved']} / {total_levels}")
    print(f"Levels solved         | {len(solved)}")
    print(f"Hints used            | {stats['total_hints']}")
    print(f"Time played           | {fmt_time(stats['total_seconds'])}")
    print(f"Sessions              | {stats['sessions']}")
    print(f"First played          | {stats['first_played']}")
    print(f"Last played           | {stats['last_played']}")

    if levels:
        hardest = max(levels.items(), key=lambda kv: kv[1]["wrong"] + kv[1]["hints"] * 2)
        print(f"Hardest level for you | {hardest[0]} ")

        timed = [[t, v["best_seconds"]] for t, v in levels.items() if v["best_seconds"] is not None]
        if timed:
            fastest = min(timed, key=lambda x: x[1])
            print(f"Fastest level solved  | {fastest[0]} in {fmt_time(fastest[1])}")
    print()