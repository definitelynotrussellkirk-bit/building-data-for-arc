#!/usr/bin/env python3
"""Atomically rebuild one parametric family's source-bound authoring evidence.

Run from WORK/repo (or anywhere in this packet), for example:

    python generators/8801696784e1/workspace/parametric/refresh_evidence.py \
        --out ../checks/8801696784e1-refresh

The command fails closed: partial output is not published, and the exact prior
manifest is restored if any test, protected Racket replay, causal replay,
projection, privacy inspection, or source-stability check fails.  It never
performs owner acceptance or training admission.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_ID = Path(__file__).resolve().parents[2].name
DEFAULT_ROOT = Path(__file__).resolve().parents[4]
CONFIG = {
    "8801696784e1": {
        "selected": {"object_kind": "asymmetric"},
        "counterfactual": {"object_kind": "symmetric"},
    },
    "05b5a82ace36": {
        "selected": {"template_selector": "smallest"},
        "counterfactual": {"template_selector": "largest"},
    },
}
if TASK_ID not in CONFIG:
    raise RuntimeError(f"unsupported refresh-evidence home: {TASK_ID}")
SELECTED_SETTINGS = CONFIG[TASK_ID]["selected"]
COUNTERFACTUAL_SETTINGS = CONFIG[TASK_ID]["counterfactual"]
DESCRIPTION_FIELDS = ("step_a", "intermediate", "step_b", "why_b_depends_on_a")
SCHEMA = "arcpuzzles-parametric-evidence-refresh-v1"

for entry in (DEFAULT_ROOT / "src", DEFAULT_ROOT / "shared" / "runtime"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))


def _raw(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}-", suffix=".tmp", dir=path.parent)
    pending = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(pending, path)
        _fsync_directory(path.parent)
    finally:
        pending.unlink(missing_ok=True)


def snapshot_sha256(files: list[dict[str, Any]]) -> str:
    """Return a deterministic aggregate hash for a sorted file inventory."""
    return _sha_bytes(_raw(files))


def _assert_regular_source(root: Path, path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"missing source file: {path}")
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError(f"symlink in source closure: {path}")
        current = current.parent


def source_snapshot(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    """Hash all source whose edit can invalidate this authoring evidence."""
    root = Path(root).resolve()
    home = root / "generators" / TASK_ID
    parametric = home / "workspace" / "parametric"
    selected: set[Path] = {home / "generator.py"}
    tests = home / "tests"
    if tests.is_dir():
        for path in tests.rglob("*"):
            if (path.is_file() and path.suffix in {".py", ".json"}
                    and "__pycache__" not in path.parts):
                selected.add(path)
    for path in parametric.rglob("*"):
        relative = path.relative_to(parametric)
        if any(part in {"evidence", "examples", "__pycache__", ".pytest_cache"}
               for part in relative.parts):
            continue
        if path.is_file() and path.suffix in {".py", ".rkt", ".json"}:
            selected.add(path)
    runtime = root / "shared" / "runtime"
    for path in runtime.rglob("*"):
        if (path.is_file() and path.suffix in {".py", ".rkt", ".json"}
                and "__pycache__" not in path.parts):
            selected.add(path)
    parser = root / "shared" / "tools" / "comment_solutions.py"
    if parser.is_file():
        selected.add(parser)
    package = root / "src" / "arcpuzzles"
    for name in (
        "parametric_promotion.py",
        "parametric_worker.py",
        "catalog.py",
        "runtime.py",
        "parametric_priority.py",
        "review_base_preflight.py",
        "review_witness.py",
    ):
        selected.add(package / name)
    files = []
    for path in sorted(selected):
        _assert_regular_source(root, path)
        files.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha_file(path),
        })
    return {"files": files, "sha256": snapshot_sha256(files)}


def _require_unchanged(root: Path, expected: dict[str, Any], stage: str) -> None:
    observed = source_snapshot(root)
    if observed != expected:
        raise ValueError(
            f"source changed during {stage}: expected {expected['sha256']}, "
            f"observed {observed['sha256']}"
        )


def require_source_binding(expected: dict[str, Any], receipt: dict[str, Any], label: str) -> None:
    """Reject a receipt that does not bind the exact expected source closure."""
    if receipt.get("source_binding") != expected:
        raise ValueError(f"mixed-source {label}: receipt does not bind current source")


def portable_relative(path: Path, root: Path) -> str:
    """Return a portable POSIX path, rejecting machine-external locations."""
    path = Path(path).resolve()
    root = Path(root).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside portable root {root}: {path}") from exc


class OutputTransaction:
    """Publish a directory by rename and remove it unless explicitly committed."""

    def __init__(self, destination: Path):
        self.destination = Path(destination).resolve()
        self.stage: Path | None = None
        self.published = False
        self.committed = False

    def __enter__(self) -> "OutputTransaction":
        if self.destination.exists() or self.destination.is_symlink():
            raise FileExistsError(f"choose a new refresh output: {self.destination}")
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        self.stage = Path(tempfile.mkdtemp(
            prefix=f".{self.destination.name}-{TASK_ID}-",
            dir=self.destination.parent,
        ))
        return self

    def publish(self) -> None:
        if self.stage is None or not self.stage.is_dir() or self.published:
            raise RuntimeError("output transaction is not publishable")
        os.rename(self.stage, self.destination)
        self.published = True
        _fsync_directory(self.destination.parent)

    def commit(self) -> None:
        if not self.published or not self.destination.is_dir():
            raise RuntimeError("cannot commit an unpublished output")
        self.committed = True

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if not self.committed:
            if self.destination.exists() and not self.destination.is_symlink():
                shutil.rmtree(self.destination, ignore_errors=True)
            if self.stage is not None and self.stage.exists():
                shutil.rmtree(self.stage, ignore_errors=True)
        return False




JOURNAL_SCHEMA = "arcpuzzles-parametric-refresh-transaction-v1"


def _safe_relative_member(base: Path, value: str, label: str) -> Path:
    """Resolve one persisted relative path without allowing traversal or symlinks."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"invalid {label} path in refresh journal")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise ValueError(f"unsafe {label} path in refresh journal: {value}")
    base = Path(base).resolve()
    candidate = (base / Path(*relative.parts)).resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError(f"escaped {label} path in refresh journal: {value}")
    return candidate


def _remove_recovery_path(path: Path) -> None:
    """Remove one transaction-owned path without following a replacement symlink."""
    parent = path.parent
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        raise ValueError(f"cannot safely remove special recovery path: {path}")
    if parent.is_dir():
        _fsync_directory(parent)


def _journal_path(work_root: Path) -> Path:
    return Path(work_root).resolve() / ".review" / f"parametric-refresh-{TASK_ID}.transaction.json"


def recover_interrupted_refresh(work_root: Path, root: Path) -> bool:
    """Roll back one durable journal left by process death; return whether it existed."""
    work_root = Path(work_root).resolve()
    root = Path(root).resolve()
    path = _journal_path(work_root)
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"unsafe refresh transaction journal: {path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unreadable refresh transaction journal: {path}") from exc
    if (not isinstance(state, dict) or state.get("schema") != JOURNAL_SCHEMA
            or state.get("task_id") != TASK_ID):
        raise ValueError("refresh transaction journal has the wrong schema or task")
    if state.get("root") != portable_relative(root, work_root):
        raise ValueError("refresh transaction journal belongs to another repository root")

    manifest = _safe_relative_member(work_root, state.get("manifest"), "manifest")
    expected_manifest = (
        root / "generators" / TASK_ID / "workspace" / "parametric" /
        "evidence" / "manifest.json"
    ).resolve()
    if manifest != expected_manifest:
        raise ValueError("refresh transaction journal names an unexpected manifest")
    try:
        previous = base64.b64decode(state.get("manifest_bytes_b64", ""), validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("refresh transaction journal has invalid manifest backup") from exc
    if _sha_bytes(previous) != state.get("manifest_sha256"):
        raise ValueError("refresh transaction journal manifest backup hash mismatch")
    if state.get("manifest_existed") is True:
        _atomic_write(manifest, previous)
    elif state.get("manifest_existed") is False:
        manifest.unlink(missing_ok=True)
        if manifest.parent.is_dir():
            _fsync_directory(manifest.parent)
    else:
        raise ValueError("refresh transaction journal has invalid manifest state")

    output_value = state.get("output")
    stage_value = state.get("stage")
    output_rel = PurePosixPath(output_value) if isinstance(output_value, str) else None
    if output_rel is None or not output_rel.parts or output_rel.parts[0] != "checks":
        raise ValueError("refresh transaction output is not under WORK/checks")
    output = _safe_relative_member(work_root, output_value, "output")
    stage = _safe_relative_member(work_root, stage_value, "stage")
    expected_prefix = f".{output.name}-{TASK_ID}-"
    if stage.parent != output.parent or not stage.name.startswith(expected_prefix):
        raise ValueError("refresh transaction stage does not match its output")
    _remove_recovery_path(output)
    _remove_recovery_path(stage)

    revision_value = state.get("revision")
    revision_created = state.get("revision_created")
    if revision_value is not None:
        revision = _safe_relative_member(root, revision_value, "revision")
        revision_base = (
            root / "generators" / TASK_ID / "workspace" / "parametric" /
            "evidence" / "revisions"
        ).resolve()
        if revision.parent != revision_base or not revision.name.startswith("refresh-"):
            raise ValueError("refresh transaction journal names an unexpected revision")
        if revision_created is True:
            _remove_recovery_path(revision)
            for pending in revision_base.glob(f".{revision.name}-*"):
                _remove_recovery_path(pending)
        elif revision_created is not False:
            raise ValueError("refresh transaction journal has invalid revision state")
    elif revision_created not in (None, False):
        raise ValueError("refresh transaction journal has revision state without a path")

    path.unlink()
    _fsync_directory(path.parent)
    return True


class RefreshJournal:
    """Durably describe rollback state so a later invocation survives SIGKILL."""

    def __init__(self, work_root: Path, root: Path, manifest: Path,
                 publication: OutputTransaction):
        self.work_root = Path(work_root).resolve()
        self.root = Path(root).resolve()
        self.manifest = Path(manifest).resolve()
        self.publication = publication
        self.path = _journal_path(self.work_root)
        self.state: dict[str, Any] | None = None
        self.committed = False

    def __enter__(self) -> "RefreshJournal":
        if self.path.exists() or self.path.is_symlink():
            raise ValueError("unrecovered refresh transaction journal exists")
        if self.publication.stage is None:
            raise RuntimeError("output transaction must be entered before the refresh journal")
        output_rel = portable_relative(self.publication.destination, self.work_root)
        output_parts = PurePosixPath(output_rel).parts
        if not output_parts or output_parts[0] != "checks":
            raise ValueError("refresh output must be under WORK/checks")
        manifest_existed = self.manifest.is_file()
        if self.manifest.exists() and not manifest_existed:
            raise ValueError("manifest must be a regular file")
        previous = self.manifest.read_bytes() if manifest_existed else b""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state = {
            "schema": JOURNAL_SCHEMA,
            "task_id": TASK_ID,
            "root": portable_relative(self.root, self.work_root),
            "manifest": portable_relative(self.manifest, self.work_root),
            "manifest_existed": manifest_existed,
            "manifest_bytes_b64": base64.b64encode(previous).decode("ascii"),
            "manifest_sha256": _sha_bytes(previous),
            "output": output_rel,
            "stage": portable_relative(self.publication.stage, self.work_root),
            "revision": None,
            "revision_created": False,
        }
        _atomic_write(self.path, _raw(self.state))
        return self

    def record_revision(self, revision: Path, *, created: bool) -> None:
        if self.state is None:
            raise RuntimeError("refresh journal is not active")
        revision = Path(revision).resolve()
        revision_base = (
            self.root / "generators" / TASK_ID / "workspace" / "parametric" /
            "evidence" / "revisions"
        ).resolve()
        if revision.parent != revision_base or not revision.name.startswith("refresh-"):
            raise ValueError("refusing to journal a revision outside the task evidence home")
        self.state["revision"] = portable_relative(revision, self.root)
        self.state["revision_created"] = bool(created)
        _atomic_write(self.path, _raw(self.state))

    def commit(self) -> None:
        self.committed = True

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc_type is not None or not self.committed:
            recover_interrupted_refresh(self.work_root, self.root)
        else:
            self.path.unlink(missing_ok=True)
            if self.path.parent.is_dir():
                _fsync_directory(self.path.parent)
        return False


class ManifestTransaction:
    """Restore the exact prior manifest unless the entire refresh commits."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.previous: bytes | None = None
        self.existed = False
        self.committed = False

    def __enter__(self) -> "ManifestTransaction":
        if self.path.is_symlink() or any(parent.is_symlink() for parent in self.path.parents):
            raise ValueError("manifest path must contain no symlink")
        self.existed = self.path.exists()
        if self.existed:
            if not self.path.is_file():
                raise ValueError("manifest must be a regular file")
            self.previous = self.path.read_bytes()
        return self

    def replace(self, raw: bytes) -> None:
        _atomic_write(self.path, raw)

    def commit(self) -> None:
        self.committed = True

    def _rollback(self) -> None:
        if self.existed:
            assert self.previous is not None
            _atomic_write(self.path, self.previous)
        else:
            self.path.unlink(missing_ok=True)
            if self.path.parent.exists():
                _fsync_directory(self.path.parent)

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc_type is not None or not self.committed:
            self._rollback()
        return False


def _load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _prototype():
    return _load_module(HERE / "prototype.py", f"_refresh_prototype_{TASK_ID}")


def activate_racket(work_root: Path) -> Path:
    """Activate the packet's verified Racket for this process and its children."""
    work_root = Path(work_root).resolve()
    explicit = os.environ.get("RACKET_PATH")
    selected = Path(explicit).expanduser().resolve() if explicit else None
    if selected is None or not selected.is_file() or not os.access(selected, os.X_OK):
        cached = work_root / ".review" / "racket-runtime" / "racket" / "bin" / "racket"
        if cached.is_file() and os.access(cached, os.X_OK):
            selected = cached.resolve()
        else:
            setup = _load_module(work_root / "setup_racket.py", f"_refresh_setup_racket_{TASK_ID}")
            selected = Path(setup.ensure_racket()).resolve()
    if not selected.is_file() or not os.access(selected, os.X_OK):
        raise ValueError(f"packet Racket is not executable: {selected}")
    os.environ["RACKET_PATH"] = str(selected)
    current_path = os.environ.get("PATH", "")
    entries = [entry for entry in current_path.split(os.pathsep) if entry]
    parent = str(selected.parent)
    os.environ["PATH"] = os.pathsep.join([parent, *[entry for entry in entries if entry != parent]])
    return selected


def fill_recipe(draft: dict[str, Any]) -> dict[str, Any]:
    """Derive the authored intermediate from the exact qualified selected case."""
    recipe = deepcopy(draft)
    if (recipe.get("selected_case", {}).get("settings") != SELECTED_SETTINGS
            or not isinstance(recipe.get("cases"), list) or len(recipe["cases"]) != 1):
        raise ValueError("witness draft does not select the configured case")
    grid = recipe["selected_case"].get("input")
    prototype = _prototype()

    if TASK_ID == "8801696784e1":
        candidates = []
        for component in prototype._components(grid):
            crop = prototype._crop(grid, component)
            if not prototype._both_symmetric(crop):
                candidates.append((len(component), crop))
        if not candidates:
            raise ValueError("qualified selected case contains no asymmetric object")
        crop = max(candidates, key=lambda item: item[0])[1]
        code = grid[-1][-1]
        if code not in {1, 2, 3}:
            raise ValueError("qualified selected case has no valid corner code")
        recipe.update({
            "step_a": (
                "Remove the bottom-right code cell and select the connected object's tight crop "
                "that is not symmetric under both left-right and up-down reflection."
            ),
            "intermediate": (
                "Retain the selected asymmetric crop together with the bottom-right rotation code."
            ),
            "step_b": (
                "Rotate that exact crop clockwise for code 1, 180 degrees for code 2, or "
                "counterclockwise for code 3, then enlarge every cell to a 2 by 2 block."
            ),
            "why_b_depends_on_a": (
                "The rotation and enlargement consume the cell-by-cell crop chosen in step A; "
                "choosing the symmetric object changes the protected final output."
            ),
        })
        recipe["cases"][0]["intermediate_value"] = {
            "selected_object_kind": "asymmetric",
            "corner_code": code,
            "selected_crop": crop,
        }
        return recipe

    components = prototype._components(grid)
    if len(components) < 2 or len({len(component) for component in components}) < 2:
        raise ValueError("qualified selected case lacks distinct template sizes")
    selected = min(components, key=len)
    offsets = prototype._normalize(selected)
    recipe.update({
        "step_a": (
            "Find every multi-cell 2/4-connected template and select the one with the smallest "
            "cell count."
        ),
        "intermediate": (
            "Normalize the selected template to offsets from its top-left occupied cell."
        ),
        "step_b": (
            "For every colored anchor, stamp those exact normalized offsets in the anchor's "
            "color, clipping cells that fall outside the grid."
        ),
        "why_b_depends_on_a": (
            "Step B stamps the precise offset set chosen in step A; selecting the largest "
            "template changes the protected final output."
        ),
    })
    recipe["cases"][0]["intermediate_value"] = {
        "template_selector": "smallest",
        "component_size": len(selected),
        "normalized_offsets": [list(cell) for cell in offsets],
    }
    return recipe


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    _atomic_write(
        path,
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                   allow_nan=False).encode("utf-8") + b"\n",
    )




def _publish_compact_task_tests(stage: Path, receipt: dict[str, Any]) -> None:
    """Replace verbose runtime diagnostics with the source-bound portable receipt."""
    runtime = Path(stage) / "task-tests"
    if runtime.is_symlink() or not runtime.is_dir():
        raise ValueError("task-test runtime output is missing or unsafe")
    shutil.rmtree(runtime)
    _write_json(Path(stage) / "task-tests.json", receipt)


def _normalize_causal_replay(stage: Path) -> dict[str, Any]:
    """Bind replay to its packaged witness with a portable relative path."""
    stage = Path(stage).resolve()
    replay_path = stage / "causal" / "replay.json"
    witness = stage / "causal" / "witness.json"
    replay = _json(replay_path)
    value = replay.get("witness_path")
    if not isinstance(value, str) or not value:
        raise ValueError("causal replay lacks a witness path")
    observed = Path(value).resolve() if Path(value).is_absolute() else (replay_path.parent / value).resolve()
    if observed != witness.resolve() or not witness.is_file():
        raise ValueError("causal replay witness path does not name the packaged witness")
    replay["witness_path"] = "causal/witness.json"
    _write_json(replay_path, replay)
    return replay

def _compact_test_receipt(result: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    if (result.get("passed") is not True or result.get("status") != "completed"
            or result.get("exit_code") != 0 or result.get("timed_out") is not False):
        raise ValueError("task tests did not complete successfully")
    counts = result.get("test_counts")
    if (not isinstance(counts, dict) or counts.get("failed") != 0
            or counts.get("errors") != 0 or not isinstance(counts.get("passed"), int)
            or counts["passed"] <= 0):
        raise ValueError("task test receipt has invalid counts")
    command = list(result.get("command") or [])
    if command:
        command[0] = "python3"
    return {
        "schema": "arcpuzzles-source-bound-task-tests-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "source_snapshot_sha256": snapshot["sha256"],
        "source_files": snapshot["files"],
        "command": command,
        "test_counts": counts,
        "test_paths": result.get("test_paths"),
        "evidence_sha256": result.get("evidence_sha256"),
        "runtime_manifest_receipt_input_sha256": result.get("runtime_manifest", {}).get(
            "receipt_input_sha256"
        ),
        "owner_accepted": False,
        "training_admitted": False,
    }


def _task_evidence_destination(root: Path, receipt: dict[str, Any]) -> Path:
    raw = _raw(receipt)
    base = (
        Path(root).resolve() / "generators" / TASK_ID / "workspace" / "parametric" /
        "evidence" / "revisions"
    )
    name = f"refresh-{receipt['source_snapshot_sha256'][:16]}-{_sha_bytes(raw)[:16]}"
    return base / name


def _install_task_evidence(root: Path, receipt: dict[str, Any]) -> tuple[Path, bool]:
    raw = _raw(receipt)
    destination = _task_evidence_destination(root, receipt)
    base = destination.parent
    base.mkdir(parents=True, exist_ok=True)
    member = destination / "task-tests.json"
    if destination.exists():
        if destination.is_symlink() or not member.is_file() or member.read_bytes() != raw:
            raise ValueError(f"existing evidence revision differs: {destination}")
        return destination, False
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=base))
    try:
        (stage / "task-tests.json").write_bytes(raw)
        _fsync_directory(stage)
        os.rename(stage, destination)
        _fsync_directory(base)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return destination, True


def _assert_current(root: Path, expected_contract: dict[str, Any],
                    expected_binding: dict[str, Any], snapshot: dict[str, Any],
                    stage: str) -> None:
    from arcpuzzles.review_base_preflight import source_ready

    _require_unchanged(root, snapshot, stage)
    contract, binding = source_ready(root, TASK_ID)
    if contract != expected_contract or binding != expected_binding:
        raise ValueError(f"current source binding changed during {stage}")


def _inventory(directory: Path) -> list[dict[str, Any]]:
    files = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink in refresh output: {path}")
        if path.is_file() and path.name != "refresh.json":
            files.append({
                "path": path.relative_to(directory).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha_file(path),
            })
        elif not path.is_dir() and not path.is_file():
            raise ValueError(f"special file in refresh output: {path}")
    return files


def _run_first_turn(work_root: Path, root: Path, bundle: Path,
                    output: Path) -> dict[str, Any]:
    env = os.environ.copy()
    pythonpath = [str(root / "src"), str(root / "shared" / "runtime")]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env.update(
        PYTHONPATH=os.pathsep.join(pythonpath),
        PYTHONNOUSERSITE="1",
        PYTHONDONTWRITEBYTECODE="1",
    )
    command = [
        sys.executable,
        str(work_root / "check_first_turn.py"),
        "--bundle",
        str(bundle),
        "--out",
        str(output),
    ]
    result = subprocess.run(
        command,
        cwd=root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    if result.returncode != 0:
        raise ValueError(
            "first-turn privacy check failed: " + json.dumps({
                "exit_code": result.returncode,
                "stdout": result.stdout[-1500:],
                "stderr": result.stderr[-1500:],
            })
        )
    report = _json(output)
    if report.get("status") != "passed" or report.get("failures") != []:
        raise ValueError("first-turn privacy report is not passing")
    return report


@contextmanager
def _exclusive_refresh(work_root: Path):
    runtime = work_root / ".review"
    runtime.mkdir(parents=True, exist_ok=True)
    lock_path = runtime / f"parametric-refresh-{TASK_ID}.lock"
    with lock_path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(f"another evidence refresh is active for {TASK_ID}") from exc
        yield


def refresh(output: Path, *, root: Path = DEFAULT_ROOT, timeout: float = 300,
            demos: int = 3) -> dict[str, Any]:
    """Execute and atomically publish a complete single-source evidence chain."""
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_manifest import build_manifest
    from arcpuzzles.review_base_preflight import preflight, source_ready
    from arcpuzzles.review_witness import build_witness, write_template
    from arcpuzzles.runtime import check

    root = Path(root).resolve()
    work_root = root.parent
    output = Path(output).resolve()
    output_relative = portable_relative(output, work_root)
    if not PurePosixPath(output_relative).parts or PurePosixPath(output_relative).parts[0] != "checks":
        raise ValueError("refresh output must be under WORK/checks")
    if (not (work_root / "preview_public.py").is_file()
            or not (work_root / "check_first_turn.py").is_file()):
        raise ValueError("refresh must run inside a complete review WORK packet")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(timeout) not in (int, float) or not 30 <= timeout <= 1800:
        raise ValueError("timeout must be in 30..1800 seconds")

    racket = activate_racket(work_root)
    revision: Path | None = None
    revision_created = False
    manifest = (
        root / "generators" / TASK_ID / "workspace" / "parametric" /
        "evidence" / "manifest.json"
    )
    try:
        with _exclusive_refresh(work_root):
            recover_interrupted_refresh(work_root, root)
            snapshot = source_snapshot(root)
            with (ManifestTransaction(manifest) as transaction,
                  OutputTransaction(output) as publication,
                  RefreshJournal(work_root, root, manifest, publication) as journal):
                assert publication.stage is not None
                stage = publication.stage
                test_result = check(
                    Catalog(root),
                    TASK_ID,
                    stage="task_tests",
                    phase="after",
                    output=stage / "task-tests",
                    timeout=timeout,
                )
                _require_unchanged(root, snapshot, "task tests")
                test_receipt = _compact_test_receipt(test_result, snapshot)
                planned_revision = _task_evidence_destination(root, test_receipt)
                journal.record_revision(planned_revision, created=not planned_revision.exists())
                revision, revision_created = _install_task_evidence(root, test_receipt)
                _publish_compact_task_tests(stage, test_receipt)

                old_hash = _sha_file(manifest) if manifest.is_file() else None
                counts = test_receipt["test_counts"]
                manifest_result = build_manifest(
                    Catalog(root),
                    TASK_ID,
                    evidence=revision.relative_to(root).as_posix(),
                    reported_checks=(
                        f"refresh_evidence.py task_tests passed "
                        f"{counts['passed']}/{counts['tests']}; "
                        f"source_snapshot={snapshot['sha256']}"
                    ),
                    output=manifest,
                    replace_sha256=old_hash,
                )
                manifest_result = {
                    **manifest_result,
                    "manifest": manifest.relative_to(root).as_posix(),
                }
                _require_unchanged(root, snapshot, "manifest publication")
                contract, binding = source_ready(root, TASK_ID)

                qualification_result = preflight(
                    root,
                    TASK_ID,
                    stage / "qualification",
                    demos=demos,
                    timeout=timeout,
                )
                qualification_path = Path(qualification_result["receipt"])
                qualification = _json(qualification_path)
                require_source_binding(binding, qualification, "qualification")
                _assert_current(
                    root, contract, binding, snapshot, "protected authoring preflight"
                )

                recipe_path = stage / "witness-recipe.json"
                write_template(
                    root,
                    qualification_path,
                    recipe_path,
                    settings=SELECTED_SETTINGS,
                    counterfactual_settings=COUNTERFACTUAL_SETTINGS,
                )
                recipe = fill_recipe(_json(recipe_path))
                _write_json(recipe_path, recipe)
                build_witness(
                    root,
                    qualification_path,
                    recipe,
                    stage / "causal",
                    timeout=min(60.0, timeout),
                )
                causal_result = _normalize_causal_replay(stage)
                require_source_binding(binding, causal_result, "causal replay")
                require_source_binding(
                    binding, _json(stage / "causal" / "witness.json"), "causal witness"
                )
                require_source_binding(
                    binding, _json(stage / "causal" / "replay.json"), "causal replay file"
                )
                _assert_current(root, contract, binding, snapshot, "causal witness")

                preview = _load_module(
                    work_root / "preview_public.py", f"_refresh_preview_{TASK_ID}"
                )
                preview_result = preview.export_qualified(
                    qualification_path,
                    stage / "preview",
                    library=root,
                    presentation_seed=0,
                )
                preview_result = {
                    **preview_result,
                    "manifest": "preview/private/manifest.json",
                }
                preview_verification = preview.verify_export(stage / "preview", library=root)
                _write_json(stage / "preview-verification.json", preview_verification)
                preview_manifest = _json(stage / "preview" / "private" / "manifest.json")
                require_source_binding(binding, preview_manifest, "preview projection")
                _assert_current(root, contract, binding, snapshot, "preview projection")

                first_turn = _run_first_turn(
                    work_root, root, stage / "preview", stage / "first-turn.json"
                )
                if (first_turn.get("training_admitted") is not False
                        or first_turn.get("owner_acceptance") != "not_performed"):
                    raise ValueError("first-turn report crossed the authoring status boundary")
                _assert_current(
                    root, contract, binding, snapshot, "first-turn privacy inspection"
                )

                artifacts = _inventory(stage)
                summary = {
                    "schema": SCHEMA,
                    "status": "passed",
                    "task_id": TASK_ID,
                    "source_snapshot": snapshot,
                    "source_binding_sha256": _sha_bytes(_raw(binding)),
                    "source_binding": binding,
                    "racket": {
                        "path": portable_relative(racket, work_root),
                        "sha256": _sha_file(racket),
                    },
                    "manifest": {
                        "path": manifest.relative_to(root).as_posix(),
                        "sha256": _sha_file(manifest),
                        "builder_result": manifest_result,
                        "evidence_root": revision.relative_to(root).as_posix(),
                    },
                    "task_tests": test_receipt,
                    "qualification": {
                        "schema": qualification.get("schema"),
                        "verification_status": qualification.get("verification_status"),
                        "jobs": len(qualification.get("jobs", [])),
                        "sha256": _sha_file(qualification_path),
                    },
                    "causal": {
                        "status": causal_result.get("status"),
                        "evaluations": causal_result.get("construction", {}).get("evaluations"),
                        "witness_sha256": _sha_file(stage / "causal" / "witness.json"),
                        "replay_sha256": _sha_file(stage / "causal" / "replay.json"),
                    },
                    "preview": {
                        "export": preview_result,
                        "verification": preview_verification,
                    },
                    "first_turn": {
                        key: first_turn.get(key)
                        for key in (
                            "status",
                            "public_views_checked",
                            "first_turns_checked",
                            "invariance_checks",
                            "positive_controls",
                        )
                    },
                    "artifacts": artifacts,
                    "owner_accepted": False,
                    "training_admitted": False,
                    "limitations": (
                        "Authoring preflight and protected replay only. This refresh neither "
                        "performs owner acceptance nor admits the family to training."
                    ),
                }
                _write_json(stage / "refresh.json", summary)
                _assert_current(root, contract, binding, snapshot, "final summary")
                publication.publish()
                transaction.commit()
                publication.commit()
                journal.commit()
                return {
                    **summary,
                    "output": str(output),
                    "refresh_sha256": _sha_file(output / "refresh.json"),
                }
    except BaseException:
        if revision_created and revision is not None and revision.exists():
            shutil.rmtree(revision, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="new output directory; partial results are never published",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        report = refresh(args.out, root=args.root, timeout=args.timeout, demos=args.demos)
    except Exception as error:
        print(
            json.dumps({
                "status": "failed",
                "task_id": TASK_ID,
                "error": f"{type(error).__name__}: {error}",
            }, sort_keys=True),
            file=sys.stderr,
        )
        return 1
    print(json.dumps({
        "status": report["status"],
        "task_id": TASK_ID,
        "output": report["output"],
        "refresh_sha256": report["refresh_sha256"],
        "tests": report["task_tests"]["test_counts"],
        "qualification_jobs": report["qualification"]["jobs"],
        "causal_evaluations": report["causal"]["evaluations"],
        "first_turn": report["first_turn"],
        "owner_accepted": False,
        "training_admitted": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
