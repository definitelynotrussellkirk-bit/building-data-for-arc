#!/usr/bin/env python3
"""One entry point for a relocatable ARCpuzzles review workspace."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "WORK"


def scan_owned_tree(root, *, max_entries=20000, seconds=3):
    """Bounded metadata-only scan of an explicitly identified working tree."""
    if not 1 <= max_entries <= 100000 or not 0 < seconds <= 10:
        raise ValueError("Scan limits must be 1–100000 entries and >0–10 seconds")
    root = Path(root).absolute()
    broad = {"/", "/workspace", "/workspace/scratch", "/tmp", "/opt", "/usr",
             "/root", "/home", "/dev", "/dev/shm", "/proc", "/sys", "/var"}
    if root.resolve().as_posix() in broad:
        raise ValueError("Choose a specific owned working directory, not a broad system root")
    if root.is_symlink():
        raise ValueError("Owned working directory must not be a symlink")
    if not root.is_dir():
        raise ValueError("Owned working directory must exist")
    device = root.stat().st_dev
    row = dict(path=str(root), entries_seen=0, unique_inodes=0, allocated_bytes=0,
               regular_file_bytes=0, mount_points_skipped=0, complete=True,
               limits_hit=[], errors=[])
    seen = set()
    deadline = time.monotonic() + seconds

    def visit(path):
        if row['entries_seen'] >= max_entries:
            row['limits_hit'].append('entry_budget')
            return False
        if time.monotonic() >= deadline:
            row['limits_hit'].append('time_budget')
            return False
        try:
            info = path.lstat()
        except OSError as exc:
            row['errors'].append(dict(path=str(path), error=str(exc)))
            return True
        row['entries_seen'] += 1
        if info.st_dev != device:
            row['mount_points_skipped'] += 1
            return True
        key = (info.st_dev, info.st_ino)
        if key in seen:
            return True
        seen.add(key)
        row['unique_inodes'] += 1
        row['allocated_bytes'] += getattr(info, 'st_blocks', 0) * 512
        if stat.S_ISREG(info.st_mode):
            row['regular_file_bytes'] += info.st_size
        if stat.S_ISDIR(info.st_mode):
            try:
                with os.scandir(path) as entries:
                    for entry in entries:
                        if not visit(Path(entry.path)):
                            return False
            except OSError as exc:
                row['errors'].append(dict(path=str(path), error=str(exc)))
        return True

    visit(root)
    row['complete'] = not (row['limits_hit'] or row['errors'])
    return row


def storage_report(args):
    """Optional diagnostic; deliberately independent of the packet and manifests."""
    import argparse
    from datetime import datetime, timezone
    parser = argparse.ArgumentParser(description="Read-only filesystem counters; no extraction or deletion")
    parser.add_argument('--label', default='', help='User-supplied comparison label, not verified model identity')
    parser.add_argument('--model', default='unknown', help='Model shown in the picker; self-reported')
    parser.add_argument('--freshness', choices=['fresh', 'continued', 'unknown'], default='unknown')
    parser.add_argument('--stage', choices=['before_extract', 'after_extract', 'after_setup', 'before_package', 'manual'],
                        default='manual')
    parser.add_argument('--archive', type=Path, help='Optional exact uploaded packet to hash')
    parser.add_argument('--jsonl', action='store_true', help='Print one compact JSON line for appending')
    parser.add_argument('--owned-root', action='append', default=[],
                        help='Optional specific directory you own; never identify unrelated sessions')
    parser.add_argument('--scan-entries', type=int, default=20000)
    parser.add_argument('--scan-seconds', type=float, default=3)
    options = parser.parse_args(args)
    if len(options.owned_root) > 4:
        raise ValueError("At most four explicitly owned directories may be scanned")
    report = dict(schema='arcpuzzles-storage-observation-v1', study_id='model-storage-20261023',
                  label=options.label, model=options.model, freshness=options.freshness, stage=options.stage,
                  observed_utc=datetime.now(timezone.utc).isoformat(), filesystems=[], owned_trees=[],
                  limits=["Counters describe this process, not verified model quotas or another task's mounts.",
                          "Overlapping paths may describe the same storage; do not add their totals.",
                          "Owned-tree counts are metadata observations, not guaranteed reclaimable space.",
                          "No file contents, session histories, extraction or deletion are requested."])
    if options.archive is not None:
        digest = hashlib.sha256()
        with options.archive.open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(chunk)
        report['archive'] = dict(bytes=options.archive.stat().st_size, sha256=digest.hexdigest())
        report['limits'][-1] = 'Only the explicitly named packet is hashed; no session histories, extraction or deletion.'
    try:
        report['mount_namespace'] = os.readlink('/proc/self/ns/mnt')
    except OSError:
        report['mount_namespace'] = None
    for path in dict.fromkeys(['/', '/tmp', '/dev/shm', '/workspace', str(Path.cwd())]):
        try:
            info, fs = os.stat(path), os.statvfs(path)
            unit = fs.f_frsize or fs.f_bsize
            report['filesystems'].append(dict(
                path=path, device_id=info.st_dev, total_bytes=fs.f_blocks * unit,
                free_bytes=fs.f_bfree * unit, available_bytes=fs.f_bavail * unit,
                total_inodes=fs.f_files or None,
                free_inodes=fs.f_ffree if fs.f_files else None,
                available_inodes=fs.f_favail if fs.f_files else None))
        except OSError as exc:
            report['filesystems'].append(dict(path=path, error=str(exc)))
    for path in options.owned_root:
        report['owned_trees'].append(scan_owned_tree(
            path, max_entries=options.scan_entries, seconds=options.scan_seconds))
    print(json.dumps(report, indent=None if options.jsonl else 2, sort_keys=True))
    return 0


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
    print(f"Selected staged tests: python3 review.py task-tests {tid} --phase after --out ../checks/task-tests")
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
    text = text.replace("python3 assignment.py nvarc", "python3 review.py nvarc")
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
    # Can run with only this file, before any packet extraction or installation.
    if args and args[0] == 'storage':
        return storage_report(args[1:])
    value = manifest()
    command = args[0] if args else "status"
    rest = args[1:]
    if command in {"-h", "--help", "help"}:
        print("Usage: python3 review.py [start|status|duties|tickets|audit|nvarc|check|task-tests|run|setup|solve|blind|package|verify|storage] [arguments]")
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
    scripts = {"audit": ("assignment.py", ["audit"]), "tickets": ("assignment.py", ["tickets"]), "nvarc": ("assignment.py", ["nvarc"]), "run": ("run_with_racket.py", []),
               "setup": ("setup_racket.py", []), "solve": ("solve_episode.py", []),
               "blind": ("solve_episode.py", ["blind"]), "package": ("package_return.py", [])}
    if command in {"check", "task-tests"}:
        contract = read_json(WORK / "ASSIGNMENT.json")
        # Accept an explicit included task anywhere without reordering option/value pairs.
        # Task IDs have a fixed 12-hex spelling; only consume a catalog target.
        targets = set(value.get("generators", {}))
        targets.add(contract["task_id"])
        explicit = [i for i, arg in enumerate(rest) if arg in targets]
        if len(explicit) > 1:
            raise ValueError("Specify at most one task ID")
        task_id = rest.pop(explicit[0]) if explicit else contract["task_id"]
        if command == "task-tests":
            if "--stage" in rest or any(arg.startswith("--stage=") for arg in rest) or "--battery" in rest:
                raise ValueError("task-tests selects only the task_tests stage; use check for other stages")
            rest = ["--stage", "task_tests", *rest]
        script, prefix = "run_with_racket.py", [sys.executable, "-m", "arcpuzzles", "check", task_id]
    elif command in scripts:
        script, prefix = scripts[command]
    else:
        raise ValueError(f"Unknown command: {command}; run python3 review.py --help")
    delegated = [sys.executable, str(WORK / script), *prefix, *rest]
    result = subprocess.run(delegated, cwd=WORK)
    if result.returncode:
        print(f"Failed command (cwd={WORK}): {shlex.join(delegated)}", file=sys.stderr)
    if command in {"audit", "tickets"} and result.returncode == 0:
        status(value)
    return result.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (ValueError, KeyError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
