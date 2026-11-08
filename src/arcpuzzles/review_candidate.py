"""Confine returned patches and run checks in disposable review workspaces."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import sys

from .catalog import Catalog, sha256
from .runtime import run_process


_DIFF = re.compile(r"^diff --git a/([^\s]+) b/([^\s]+)$", re.M)


def _receipt(review_root: Path, assignment_id: str, version: int) -> dict:
    if not re.fullmatch(r"review-[0-9a-f]{16}", assignment_id) or version < 1:
        raise ValueError("Invalid review assignment or return version")
    files = list((review_root / "assignments" / assignment_id / "returns").glob(f"return-{version:04d}-*.json"))
    if len(files) != 1:
        raise FileNotFoundError(f"Unknown review return {assignment_id} v{version}")
    return json.loads(files[0].read_text())


def _paths(patch: str, contract: dict) -> set[str]:
    lines = patch.splitlines()
    if any(line.startswith(("GIT binary patch", "Binary files ", "rename from ", "rename to ",
                            "copy from ", "copy to ")) for line in lines):
        raise ValueError("Binary, rename, and copy patches are not allowed")
    if any(line.startswith(("old mode ", "new mode ", "deleted file mode ")) for line in lines):
        raise ValueError("Mode changes and deletions are not allowed")
    if any(line.startswith("new file mode ") and line != "new file mode 100644"
           for line in lines):
        raise ValueError("Only regular nonexecutable new files are allowed")
    pairs = _DIFF.findall(patch)
    if not pairs:
        raise ValueError("Patch has no diff --git file header")
    tid = contract["task_id"]
    allowed = {"workspace/" + contract["generator"]["runtime_path"],
               "workspace/" + contract["rule"]["runtime_path"]}
    allowed.update("workspace/" + item["runtime_path"] for item in contract.get("base_authorities", []))
    paths = set()
    for old, new in pairs:
        if old != new or old.startswith("/") or ".." in Path(old).parts or "\\" in old:
            raise ValueError("Patch contains an unsafe or renamed path")
        if old not in allowed and not old.startswith((f"workspace/tests/{tid}/", f"workspace/notes/{tid}/")):
            raise ValueError(f"Patch path is outside assigned task: {old}")
        paths.add(old)
    for line in patch.splitlines():
        if line.startswith(("--- ", "+++ ")):
            name = line[4:].split("\t", 1)[0]
            if name != "/dev/null" and name[2:] not in paths:
                raise ValueError(f"Patch file header escapes assigned task: {name}")
    return paths


def _canonical_unchanged_except_task(before: Path, after: Path, task_id: str) -> None:
    old = before.read_text().splitlines()
    new = after.read_text().splitlines()
    if len(old) != len(new):
        raise ValueError("Canonical ledger row count changed")
    changed = 0
    for x, y in zip(old, new):
        if x != y:
            left, right = json.loads(x), json.loads(y)
            if left.get("task_id") != task_id or right.get("task_id") != task_id:
                raise ValueError("Patch changed an unrelated canonical row")
            changed += 1
    if changed > 1:
        raise ValueError("Patch changed multiple canonical rows")


_RACKET_CHECK = r'''
import json, sys
from pathlib import Path
from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import rule_application, load_gen, mirror_normalized, arc_bounds_violation, _norm_grid
tid, generator_id, baseline_file = sys.argv[1:]
rows = [json.loads(line) for line in Path('data/canonical/puzzles.jsonl').read_text().splitlines() if line.strip()]
variants = [row for row in rows if row.get('task_id') == tid]
old_rows = [json.loads(line) for line in Path(baseline_file).read_text().splitlines() if line.strip()]
old_sources = [row['program_solution'] for row in old_rows if row.get('task_id') == tid and row.get('program_solution')]
mod = load_gen(generator_id)
checks = []
canonical_cases = 0
b = RacketBridge()
try:
    for row in variants:
        src = row.get('program_solution')
        if not src:
            checks.append({'kind':'canonical', 'passed':False, 'reason':'missing rule'})
            continue
        for split in ('train','test'):
            pairs = row.get(split) or []
            if isinstance(pairs, dict): pairs = [pairs]
            for index, pair in enumerate(pairs):
                if 'output' not in pair: continue
                canonical_cases += 1
                try:
                    got = b.eval_text(rule_application(src, _norm_grid(pair['input'])))
                    passed = got == _norm_grid(pair['output'])
                    checks.append({'kind':'canonical', 'split':split, 'index':index, 'passed':passed})
                except Exception as exc:
                    checks.append({'kind':'canonical','split':split,'index':index,'passed':False,'error':str(exc)[:300]})
    if not variants or canonical_cases == 0:
        checks.append({'kind':'canonical','passed':False,'reason':'no labeled canonical pairs'})
    if variants and variants[0].get('program_solution'):
        src = variants[0]['program_solution']
        for seed in (0,1,17):
            try:
                grid = mod.generate(seed, seed, difficulty='medium')
                out = b.eval_text(rule_application(src, grid))
                old = b.eval_text(rule_application(old_sources[0], grid)) if old_sources else None
                mirror = getattr(mod, 'rule_mirror', None)
                passed = arc_bounds_violation(out) is None and (not callable(mirror) or mirror_normalized(mirror(grid)) == out)
                checks.append({'kind':'parity','seed':seed,'passed':passed,'baseline_output':old,'candidate_output':out})
            except Exception as exc:
                checks.append({'kind':'parity','seed':seed,'passed':False,'error':str(exc)[:300]})
finally:
    b.close()
passed = bool(checks) and all(c['passed'] for c in checks)
print(json.dumps({'passed':passed, 'checks':checks}))
sys.exit(0 if passed else 1)
'''


def check_candidate(catalog: Catalog, review_root: Path, assignment_id: str, version: int,
                    *, timeout: float = 4000) -> dict:
    """Apply and check one return without editing authoritative sources."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    review_root = review_root.resolve()
    returned = _receipt(review_root, assignment_id, version)
    if returned["status"] != "accepted":
        raise ValueError(f"Return is {returned['status']}, not accepted")
    folder = review_root / "assignments" / assignment_id
    contract = json.loads((folder / "ASSIGNMENT.json").read_text())
    extracted = Path(returned["archive_path"]).parent / "extracted"
    results = json.loads((extracted / "RESULTS.json").read_text())
    check_dir = review_root.parent / "var/review/checks" / assignment_id / f"{version:04d}"
    check_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = check_dir / "result.json"
    if receipt_path.exists():
        return json.loads(receipt_path.read_text())
    report = {"schema": "arcpuzzles-review-check-v1", "assignment_id": assignment_id,
              "version": version, "status": "unexamined", "paths": [], "checks": [],
              "receipt_path": str(receipt_path)}
    try:
        if sha256(folder / "workspace/RUNTIME_MANIFEST.json") != contract["runtime_manifest_sha256"]:
            raise ValueError("Frozen candidate runtime manifest changed")
        if sha256(folder / "workspace" / contract["generator"]["runtime_path"]) != contract["generator"]["sha256"]:
            raise ValueError("Frozen candidate generator changed")
        patches = [item if isinstance(item, str) else item["path"] for item in results.get("patches", [])]
        all_paths = set()
        for name in patches:
            content = (extracted / name).read_text()
            all_paths.update(_paths(content, contract))
        report["paths"] = sorted(all_paths)
        candidate = review_root.parent / "var/review/candidates" / assignment_id / f"{version:04d}"
        if candidate.exists():
            shutil.rmtree(candidate)
        candidate.mkdir(parents=True)
        shutil.copytree(folder / "workspace", candidate / "workspace", symlinks=False)
        report["candidate_path"] = str(candidate)
        if patches:
            baseline = run_process(["bash", "scripts/run_generator_battery.sh", contract["task_id"],
                                    "before", "--fresh"], candidate / "workspace", timeout=timeout)
            report["checks"].append({"kind": "baseline_battery", **baseline})
        for name in patches:
            source = extracted / name
            applied = run_process(["git", "apply", "--check", str(source)], candidate, timeout=min(timeout, 60))
            report["checks"].append({"kind": "git_apply_check", "patch": name, **applied})
            if applied["exit_code"] != 0:
                raise ValueError(f"Patch does not apply: {name}: {applied['stderr'][:500]}")
            done = run_process(["git", "apply", str(source)], candidate, timeout=min(timeout, 60))
            if done["exit_code"] != 0:
                raise ValueError(f"Patch apply failed: {name}: {done['stderr'][:500]}")
            for changed in all_paths:
                if (candidate / changed).is_symlink():
                    raise ValueError(f"Patch created a symlink: {changed}")
        canonical = contract["rule"]["runtime_path"]
        if "workspace/" + canonical in all_paths:
            _canonical_unchanged_except_task(folder / "workspace" / canonical,
                                             candidate / "workspace" / canonical,
                                             contract["rule"]["task_id"])
        if not patches:
            report["status"] = "no_changes"
        else:
            tid = contract["task_id"]
            workspace = candidate / "workspace"
            battery = run_process(["bash", "scripts/run_generator_battery.sh", tid, "after", "--fresh"],
                                  workspace, timeout=timeout)
            report["checks"].append({"kind": "battery", **battery})
            racket_changed = any(path == "workspace/" + canonical or
                                 path in {"workspace/" + x["runtime_path"] for x in contract.get("base_authorities", [])}
                                 for path in all_paths)
            if racket_changed:
                racket = run_process([sys.executable, "-c", _RACKET_CHECK, contract["rule"]["task_id"], tid,
                                      str(folder / "workspace" / canonical)], workspace, timeout=timeout)
                report["checks"].append({"kind": "racket", **racket})
            report["status"] = "passed" if all(c["exit_code"] == 0 and not c["timed_out"]
                                                for c in report["checks"] if c["kind"] != "baseline_battery") else "failed_checks"
        report["candidate_file_sha256"] = {path: sha256(candidate / path) for path in all_paths}
    except (OSError, ValueError, KeyError, UnicodeError) as exc:
        report["status"] = "rejected_patch"
        report["reason"] = f"{type(exc).__name__}: {exc}"
        if not report["paths"]:
            report.pop("candidate_path", None)
    receipt_path.write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report
