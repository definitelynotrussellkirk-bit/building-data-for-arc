"""Local, exclusive review assignments with complete portable workspaces."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import random
import shutil
from threading import local
import uuid
import zipfile

from .catalog import Catalog, local_path, sha256
from .runtime import prepare_runtime
from .review_contract import build_contract, load_cohort, load_question

_lock_state = local()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


@contextmanager
def _lock(root: Path):
    """Serialize an owner, permitting nested calls only in this thread/process."""
    root = root.resolve()
    key = (os.getpid(), root)
    held = getattr(_lock_state, 'held', None)
    if held is None:
        held = _lock_state.held = {}
    if key in held:
        yield
        return
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / '.lock'
    library = root.parent
    packet = library.parent
    if (root.name == 'REVIEW' and library.name == 'repo'
            and (packet / 'PACKET-MANIFEST.json').is_file()):
        # Packet-local coordination is runtime state, outside the source delta.
        # Keep its inode in place: unlinking an active flock would split writers.
        runtime = packet / '.review'
        if runtime.is_symlink():
            raise ValueError('Packet review runtime cannot be a symlink')
        runtime.mkdir(parents=True, exist_ok=True)
        lock_path = runtime / 'library-review.lock'
        if lock_path.is_symlink():
            raise ValueError('Packet review lock cannot be a symlink')
    with lock_path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        held[key] = handle
        try:
            yield
        finally:
            held.pop(key, None)
            # A fork inherits descriptors and thread-local state, but must not
            # unlock the parent's open-file description during child cleanup.
            if os.getpid() == key[0]:
                fcntl.flock(handle, fcntl.LOCK_UN)


def assignments(review_root: Path) -> list[dict]:
    """Read assignments without claiming a generator or starting checks."""
    return [json.loads(path.read_text()) for path in sorted(review_root.glob("assignments/*/assignment.json"))]


def pick(catalog: Catalog, *, seed: int = 0, task_id: str | None = None,
         review_root: Path | None = None, question_id: str | None = None,
         cohort_receipt: Path | None = None, **filters) -> dict:
    """Reserve a random unclaimed generator and prepare a self-contained request."""
    root = (review_root or catalog.root / "REVIEW").resolve()
    filters = {**filters, "has_generator": True}
    filters.setdefault("kind", "per_puzzle")
    question = load_question(root, question_id, seed)
    cohort_ids, cohort = load_cohort(catalog, cohort_receipt) if cohort_receipt else (None, None)
    with _lock(root):
        active = {r["task_id"] for r in assignments(root) if r["status"] in {"preparing", "active"}}
        eligible = [r for r in catalog.query(**filters) if r["id"] not in active
                    and (cohort_ids is None or r["id"] in cohort_ids)]
        if task_id is not None:
            tid = catalog.resolve(task_id)
            eligible = [r for r in eligible if r["id"] == tid]
        if not eligible:
            raise ValueError("No unclaimed generator matches the requested filters")
        chosen = random.Random(seed).choice(eligible)
        identifier = "review-" + uuid.uuid4().hex[:16]
        folder = root / "assignments" / identifier
        folder.mkdir(parents=True)
        record = {"schema": "arcpuzzles-review-v1", "id": identifier, "task_id": chosen["id"],
                  "status": "preparing", "created_at": _now(), "seed": seed,
                  "catalog_root": str(catalog.root),
                  "eligible_count": len(eligible), "filters": filters,
                  "generator_sha256": chosen["generator_sha256"], "rule_hash": chosen["rule_hash"],
                  "approved_at_assignment": chosen["approved"]}
        if cohort is not None:
            record["cohort"] = {**cohort, "eligible_count": len(eligible)}
        _write(folder / "assignment.json", record)
    try:
        (folder / "baseline").mkdir()
        shutil.copy2(local_path(catalog.root, chosen["generator"]), folder / "baseline/generator.py")
        if sha256(folder / "baseline/generator.py") != chosen["generator_sha256"]:
            raise RuntimeError("Generator changed while preparing baseline; retry")
        (folder / "puzzle.json").write_text(json.dumps(catalog.get(chosen["id"]), indent=2) + "\n")
        prepare_runtime(catalog, folder / "workspace", chosen["id"])
        contract = build_contract(catalog, record, folder / "workspace", question)
        (folder / "ASSIGNMENT.json").write_text(json.dumps(contract, sort_keys=True, indent=2) + "\n")
        _write(folder / "RESULTS.json", {"schema": "arcpuzzles-review-results-v1",
              "assignment_id": identifier, "generator_id": chosen["id"], "completion_state": "in_progress",
              "changed_components": [], "patches": [], "checks": [], "remaining_failures": [],
              "improvement_claim": ""})
        (folder / "REVIEW.md").write_text("# Review\n\n## Before and after\n\n## Remaining failures\n\n## Proposed integration\n")
        (folder / "FEEDBACK_TO_CODEX.md").write_text("# General feedback\n\nWrite this after completing the generator work. Use stable item IDs such as `F1`, with evidence paths.\n")
        generator_path = chosen["runtime_generator"]
        request = f"""# Improve generator {chosen['id']}

Assignment: `{identifier}`. Baseline SHA-256: `{chosen['generator_sha256']}`.
This is a local prepared request; it has not been sent to a reviewer.

Read `puzzle.json`, the generator, its existing notes/tests, and the canonical
Racket authorities. Improve the intended distribution and refute plausible
shortcuts. Preserve stable identity, deterministic seeds, and reference-rule
semantics. Keep failed observations and unresolved findings visible.

First inspect the baseline and canonical examples. Run before checks. Then
improve the generator and, if justified, its Racket solution. Run after checks,
compare distributions and rule parity, and **iterate** until this generator is
as strong as you can make it. Record **remaining failures** and why you stopped.
Next **answer the assigned question** if `ASSIGNMENT.json` includes one. Only
then write **general feedback** about tooling or the review process.

The complete local execution tree is `workspace/`. Install Python 3.12+, Racket,
and `pip install -r workspace/requirements.txt`. From inside `workspace/`:

```bash
bash scripts/run_generator_battery.sh {chosen['id']} before --fresh
# Edit {generator_path}; use focused tests while working.
bash scripts/run_generator_battery.sh {chosen['id']} after --fresh
```

For shorter commands, run one stage at a time: `lint`, `selfcheck`, `rule_smoke`,
`defect_lint`, `dist_gate`, `profile_floor`, `semantic_gate`, `diversity`,
`override`, `grammar`, `racket_lint`, `authority_sync`. The complete battery can
take substantial time. Warnings, advisory results, and absent contracts are not
proof that semantics passed. Do not weaken checks to clear a failure.

Return byte-identical `ASSIGNMENT.json`, completed `RESULTS.json`, `REVIEW.md`,
and `FEEDBACK_TO_CODEX.md`. Put code patches at `patches/generator__{chosen['id']}.patch`
and/or `patches/racket__{chosen['id']}.patch`, against original `workspace/` paths.
List every returned patch, check log, and question answer in `RESULTS.json`.
Make a new return ZIP with only those files and declared artifacts; do not rezip
the entire request packet.
Include changed tests and notes. Explain every unrun or failed check. Original code is retained
in `baseline/`; patches are reviewed before any integration or approval change.

Keep the authored repo's generator unchanged while working in this packet.
This assignment does not start an agent, call a paid service, or send a message.
"""
        (folder / "REQUEST.md").write_text(request)
        record["status"] = "active"
    except Exception as exc:
        record.update(status="preparation_failed", error=f"{type(exc).__name__}: {exc}")
        with _lock(root):
            _write(folder / "assignment.json", record)
        raise
    with _lock(root):
        _write(folder / "assignment.json", record)
    return {**record, "directory": str(folder), "request": str(folder / "REQUEST.md")}


def finish(review_root: Path, identifier: str, *, status: str, note: str) -> dict:
    """Close an assignment and release its claim; never apply a patch or approve."""
    if status not in {"completed", "cancelled"} or not note.strip():
        raise ValueError("Provide completed/cancelled status and a nonempty disposition note")
    if not identifier.startswith("review-") or any(c not in "review-0123456789abcdef" for c in identifier):
        raise ValueError("Invalid review assignment ID")
    with _lock(review_root):
        path = local_path(review_root, f"assignments/{identifier}/assignment.json")
        record = json.loads(path.read_text())
        if record["status"] != "active":
            raise ValueError(f"Review is {record['status']}, not active")
        if status == "completed":
            returns = sorted((path.parent / "returns").glob("return-*.json"))
            if not returns:
                raise ValueError("Complete review requires an assess receipt; cancel an unreturned assignment")
            latest = max(int(item.name.split("-")[1]) for item in returns)
            if not list((path.parent / "assessments").glob(f"assessment-{latest:04d}-*.json")):
                raise ValueError("Complete review requires assessment of the latest return")
        record.update(status=status, closed_at=_now(), disposition=note)
        _write(path, record)
    return record


def pack(review_root: Path, identifier: str, output: Path) -> Path:
    """Create a local review ZIP; never transmit it."""
    folder = local_path(review_root, f"assignments/{identifier}")
    if not (folder / "assignment.json").is_file():
        raise FileNotFoundError(f"Unknown review assignment: {identifier}")
    if output.resolve().is_relative_to(folder.resolve()):
        raise ValueError("ZIP output must be outside the assignment folder")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Review packet contains a symlink: {path}")
            if path.is_file() and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts:
                archive.write(path, path.relative_to(folder))
    return output
