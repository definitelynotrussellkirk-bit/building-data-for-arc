"""Build a passive one-file patch. Never writes into the supplied repository."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

HELPERS = r'''

def _sync_draw_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _draw_mkdir(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"Draw directory cannot be a symlink: {path}")
    if path.is_dir():
        return
    _draw_mkdir(path.parent)
    path.mkdir(exist_ok=True)
    _sync_draw_directory(path.parent)


@contextmanager
def _main_draw_lock(packet_root: Path):
    # POSIX locks are released by the OS on process death; no stale lock recovery.
    review = packet_root / ".review"
    _draw_mkdir(review)
    lock = review / "main-draw.lock"
    if lock.is_symlink():
        raise ValueError("Main draw lock cannot be a symlink")
    with lock.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _write_draw_bytes(path: Path, raw: bytes, staging: Path, *, replace=False) -> None:
    if path.is_symlink():
        raise ValueError(f"Draw output cannot be a symlink: {path}")
    if path.exists() and not replace:
        if not path.is_file() or path.read_bytes() != raw:
            raise ValueError(f"Existing draw output conflicts with pending contract: {path.name}")
        _sync_draw_directory(path.parent)
        return
    _draw_mkdir(path.parent)
    _draw_mkdir(staging)
    descriptor, name = tempfile.mkstemp(prefix="write-", dir=staging)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _sync_draw_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _copy_draw_baseline(source: Path, destination: Path, digest: str, staging: Path) -> None:
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        raise ValueError(f"Invalid baseline destination: {destination}")
    if destination.is_file() and _sha(destination.read_bytes()) == digest:
        destination.chmod(0o444)
        _sync_draw_directory(destination.parent)
        return
    _draw_mkdir(destination.parent)
    _draw_mkdir(staging)
    descriptor, name = tempfile.mkstemp(prefix="copy-", dir=staging)
    os.close(descriptor)
    temporary = Path(name)
    try:
        shutil.copy2(source, temporary)
        if _sha(temporary.read_bytes()) != digest:
            raise ValueError(f"Packet source changed during baseline copy: {source}")
        temporary.chmod(0o444)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _sync_draw_directory(destination.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _draw_json(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def draw_main(packet_root: Path, seed: bytes | None = None) -> dict:
    packet_root = packet_root.resolve()
    with _main_draw_lock(packet_root):
        return _draw_main_locked(packet_root, seed)

'''


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected one exact source context, found {text.count(old)}: {old[:90]!r}")
    return text.replace(old, new, 1)


def build(repo):
    path = repo / "src/arcpuzzles/review_full_draw.py"
    original = path.read_text()
    current = replace_once(original, "import hashlib\n", "from contextlib import contextmanager\nimport fcntl\nimport hashlib\n")
    current = replace_once(current, "import sys\n", "import sys\nimport tempfile\n")
    current = replace_once(current,
        "\ndef draw_main(packet_root: Path, seed: bytes | None = None) -> dict:\n",
        HELPERS + "\ndef _draw_main_locked(packet_root: Path, seed: bytes | None = None) -> dict:\n")
    current = replace_once(current, '''    if contract_path.is_file():
        return json.loads(contract_path.read_text())
    manifest, packet_id = load_manifest(packet_root)
    seed = _seed(seed)
''', '''    pending_path = packet_root / ".review/pending-main-draw.json"
    staging = packet_root / ".review/main-draw-staging"
    if pending_path.is_symlink():
        raise ValueError("Pending main draw cannot be a symlink")
    if contract_path.is_file() and not pending_path.exists():
        # Completed legacy/current draws remain idempotent after reviewer edits.
        return json.loads(contract_path.read_text())
    manifest, packet_id = load_manifest(packet_root)
    pending = None
    if pending_path.exists():
        pending = json.loads(pending_path.read_text())
        if (not isinstance(pending, dict)
                or pending.get("schema") != "arcpuzzles-pending-main-draw-v1"
                or not isinstance(pending.get("contract"), dict)):
            raise ValueError("Invalid pending main draw journal")
        saved = pending["contract"]
        if saved.get("packet_id") != packet_id:
            raise ValueError("Pending draw belongs to a different packet manifest")
        try:
            saved_seed = _seed(bytes.fromhex(saved["seed"]))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Invalid pending draw seed") from error
        if seed is not None and _seed(seed) != saved_seed:
            raise ValueError("Explicit seed conflicts with pending draw; resume without a new seed")
        seed = saved_seed
    else:
        existing = packet_root / ".review/baseline"
        if existing.is_symlink() or (existing.exists() and any(existing.rglob("*"))):
            raise ValueError("Unjournaled partial baseline requires explicit recovery; refusing a new draw")
    seed = _seed(seed)
''')
    current = replace_once(current, '''    baseline_root = packet_root / ".review/baseline"
    for name in paths:
        source = packet_root / name
        destination = baseline_root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        destination.chmod(0o444)
    with contract_path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(contract, sort_keys=True, indent=2) + "\\n")
''', '''    prepared = {"schema": "arcpuzzles-pending-main-draw-v1", "contract": contract}
    if pending is not None and pending != prepared:
        raise ValueError("Pending draw contract no longer matches the verified packet")
    # Commit the exact seed/task/question/source bindings before the first copy.
    _write_draw_bytes(pending_path, _draw_json(prepared), staging)
    baseline_root = packet_root / ".review/baseline"
    for name in paths:
        _copy_draw_baseline(packet_root / name, baseline_root / name, baseline[name], staging)
    _write_draw_bytes(contract_path, _draw_json(contract), staging)
''')
    current = replace_once(current, '''        with _contract_path(packet_root, "BLIND_ASSIGNMENT.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(blind, sort_keys=True, indent=2) + "\\n")
''', '''        _write_draw_bytes(_contract_path(packet_root, "BLIND_ASSIGNMENT.json"),
                          _draw_json(blind), staging)
''')
    current = replace_once(current, '''    (packet_root / "DUTIES.md").write_text(duties, encoding="utf-8")
    results_path = packet_root / "RESULTS.json"
    if not results_path.exists():
        results_path.write_text(json.dumps({"completion_state": "in_progress",
            "stopping_reason": "Not recorded", "remaining_failures": [],
            "verification_commands": []}, indent=2) + "\\n", encoding="utf-8")
    return contract
''', '''    _write_draw_bytes(packet_root / "DUTIES.md", duties.encode("utf-8"), staging, replace=True)
    results_path = packet_root / "RESULTS.json"
    if not results_path.exists():
        _write_draw_bytes(results_path, _draw_json({"completion_state": "in_progress",
            "stopping_reason": "Not recorded", "remaining_failures": [],
            "verification_commands": []}), staging)
    # Journal remains until every required output has been durably finalized.
    # Staging is a dedicated namespace owned only by this locked transaction.
    if staging.exists():
        shutil.rmtree(staging)
        _sync_draw_directory(staging.parent)
    pending_path.unlink()
    _sync_draw_directory(pending_path.parent)
    return contract
''')
    compile(current, "candidate_review_full_draw.py", "exec")
    (HERE / "candidate_review_full_draw.py").write_text(current)
    (HERE / "proposal.patch").write_text("".join(difflib.unified_diff(
        original.splitlines(keepends=True), current.splitlines(keepends=True),
        fromfile="a/src/arcpuzzles/review_full_draw.py", tofile="b/src/arcpuzzles/review_full_draw.py")))
    binding = {
        "schema": "passive-draw-journal-source-binding-v1",
        "original_path": "repo/src/arcpuzzles/review_full_draw.py",
        "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "candidate_sha256": hashlib.sha256(current.encode()).hexdigest(),
        "implementation_status": "passive_proposal_not_installed",
    }
    (HERE / "source-binding.json").write_text(json.dumps(binding, indent=2) + "\n")
    print(json.dumps(binding, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parents[2] / "repo")
    args = parser.parse_args()
    build(args.repo.resolve())
