#!/usr/bin/env python3
"""One entry point for a relocatable ARCpuzzles review workspace."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "WORK"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def manifest():
    raw = (WORK / "PACKET-MANIFEST.json").read_bytes()
    value = json.loads(raw)
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    if raw != canonical or value.get("layout", {}).get("workspace") != "WORK":
        raise ValueError("Invalid workspace packet manifest")
    entries = value["layout"]["entry_files"]
    if set(entries) != {"START-HERE.md", "review.py"}:
        raise ValueError("Invalid workspace entry file inventory")
    for name, digest in entries.items():
        path = ROOT / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Entry file changed: {name}")
    return value


def status(value):
    contract_path = WORK / "ASSIGNMENT.json"
    if not contract_path.exists():
        print("NEXT: python3 review.py start\nDraw one repair assignment. All work stays in WORK/.")
        return
    contract = read_json(contract_path)
    print(f"Assignment: {contract['assignment_id']}")
    blind = WORK / "BLIND_ASSIGNMENT.json"
    finish = WORK / "solve-blind/summary.json"
    if blind.exists() and not (finish.exists() and read_json(finish).get("stopping_reason")):
        print("NEXT: python3 review.py blind prepare")
        print("Finish the blind solve before opening any generator, rule, notes or audit evidence.")
        print("Work: WORK/solve-blind/ — visible examples, solution.py and SOLVE_NOTES.md")
        print("Full ordered directions: python3 review.py duties")
        return
    tid = contract["task_id"]
    print(f"Repair: WORK/repo/generators/{tid}/ (generator.py, notes.md, tests/, counterexamples/)")
    print("Directions: python3 review.py duties")
    ticket_mode = bool(value.get('supplementary_ticket_policy'))
    print("Repair report: WORK/REVIEW.md; current decisions: the selected task's notes.md")
    if not ticket_mode:
        print("Legacy reports: WORK/DECISIONS.md and WORK/QUESTION_ANSWER.md")
    audit_path = WORK / "AUDIT_ASSIGNMENT.json"
    if audit_path.exists():
        drawn = read_json(audit_path)
        for i, row in enumerate(drawn.get('tickets', []), 1):
            print(f"Ticket {i}: {row['type']} — WORK/TICKETS.md; outcome in WORK/RESULTS.json")
        for i, row in enumerate(drawn.get("targets", []) if not ticket_mode else [], 1):
            target = row["task_id"]
            print(f"Audit {i}: {target} — WORK/AUDIT.md section ## {target}; evidence: WORK/checks/audit/{target}/")
    else:
        print("Two bounded tickets: run python3 review.py tickets once" if ticket_mode else
              "Two audits: run python3 review.py audit once after repair; both targets are assigned together")
    if value.get("reviewer_solve", {}).get("required"):
        print("Post-repair solve: python3 review.py solve prepare; work: WORK/solve/")
    print("Shared improvements: WORK/FEEDBACK_TO_CODEX.md — F1:, F2:, symptom, evidence, suggested change")
    print("Check evidence: WORK/checks/; command records and stopping reason: WORK/RESULTS.json")
    print("Return: python3 review.py package — send only WORK/review_response_*.zip")
    print("Reference/internal: WORK/repo/shared/, WORK/repo/catalog/, WORK/.review/; selected task notes own current decisions.")


def translated_duties(text):
    # Only rewrite command entry points; payload paths still resolve inside WORK/repo.
    commands = {"assignment.py": "audit", "package_return.py": "package",
                "run_with_racket.py": "run", "setup_racket.py": "setup",
                "solve_episode.py blind": "blind", "solve_episode.py": "solve"}
    text = text.replace("python3 assignment.py tickets", "python3 review.py tickets")
    text = text.replace("python3 assignment.py audit", "python3 review.py audit")
    text = text.replace("python3 assignment.py", "python3 review.py start")
    for script, command in commands.items():
        if script != "assignment.py":
            text = text.replace("python3 " + script, "python3 review.py " + command)
    # File links and bare inline paths are relative to the clean outer directory.
    text = re.sub(r"`((?:repo/|solve/|solve-blind/|checks/)[^`\n]*)`", r"`WORK/\1`", text)
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md",
                 "AUDIT.md", "RESULTS.json", "RETURN-GUIDE.md", "ARC-DESIGN.md", "DUTIES.md"):
        text = text.replace("`" + name + "`", "`WORK/" + name + "`")
    return text


def main(args):
    value = manifest()
    command = args[0] if args else "status"
    rest = args[1:]
    if command in {"-h", "--help", "help"}:
        print("Usage: python3 review.py [start|status|duties|tickets|audit|check|run|setup|solve|blind|package|verify] [arguments]")
        print("check ARGS uses the selected task; run COMMAND runs from WORK/repo; package outputs to WORK/.")
        return 0
    if command == "verify":
        changed = []
        for name, digest in value["files"].items():
            path = WORK / name
            if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                changed.append(name)
        if changed:
            print("Files differ from the issued packet (expected after edits):\n" + "\n".join(changed))
            return 1
        print(f"Verified {len(value['files'])} workspace files and both outer entry files.")
        return 0
    if command == "status":
        status(value)
        return 0
    if command == "start":
        sys.path.insert(0, str(WORK / "repo/src"))
        from arcpuzzles.review_full_draw import draw_main
        draw_main(WORK)
        status(value)
        return 0
    if command == "duties":
        path = WORK / "DUTIES.md"
        if not path.exists():
            raise ValueError("Run python3 review.py start first")
        print(translated_duties(path.read_text()))
        return 0
    scripts = {"audit": ("assignment.py", ["audit"]), "tickets": ("assignment.py", ["tickets"]), "run": ("run_with_racket.py", []),
               "setup": ("setup_racket.py", []), "solve": ("solve_episode.py", []),
               "blind": ("solve_episode.py", ["blind"]), "package": ("package_return.py", [])}
    if command == "check":
        contract = read_json(WORK / "ASSIGNMENT.json")
        script, prefix = "run_with_racket.py", [sys.executable, "-m", "arcpuzzles", "check", contract["task_id"]]
    elif command in scripts:
        script, prefix = scripts[command]
    else:
        raise ValueError(f"Unknown command: {command}; run python3 review.py --help")
    result = subprocess.run([sys.executable, str(WORK / script), *prefix, *rest], cwd=WORK)
    if command in {"audit", "tickets"} and result.returncode == 0:
        status(value)
    return result.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (ValueError, KeyError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
