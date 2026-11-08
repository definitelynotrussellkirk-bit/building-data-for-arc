"""Prepare local execution trees and run inherited tools with bounded lifetimes."""
from __future__ import annotations

import json
import ast
import codecs
import hashlib
import locale
import math
import os
import selectors
import shlex
from contextlib import contextmanager, suppress
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from typing import Any
from xml.etree import ElementTree

from .catalog import Catalog, local_path, sha256
from .receipt_input import read_receipt

CHECK_PHASES = ("before", "after", "audit")


class CheckInterrupted(KeyboardInterrupt):
    """A foreground check received a signal; cleanup still runs in Python."""
    def __init__(self, signum: int):
        super().__init__(signal.Signals(signum).name)
        self.signum = signum


@contextmanager
def _check_signals():
    # HTTP worker threads and embedding callers retain their own handlers.
    previous = {}
    stopping = False
    def interrupt(signum, frame):
        nonlocal stopping
        if not stopping:
            stopping = True
            raise CheckInterrupted(signum)
    if threading.current_thread() is threading.main_thread():
        for signum, default in ((signal.SIGTERM, signal.SIG_DFL),
                                (signal.SIGINT, signal.default_int_handler)):
            handler = signal.getsignal(signum)
            if handler == default:
                previous[signum] = handler
                signal.signal(signum, interrupt)
    try:
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def _read_process_identity(pid: int) -> dict | None:
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return {'pid': pid, 'birth': fields[19], 'state': fields[0],
                'group': int(fields[2]), 'session': int(fields[3])}
    except (OSError, IndexError, ValueError):
        return None


def _process_table_supported() -> bool:
    """Some sandboxes expose a /proc view inconsistent with their syscall PIDs."""
    try:
        own = Path('/proc/self/stat').read_text()
        if int(own.split('(', 1)[0]) != os.getpid():
            return False
        identity = _read_process_identity(os.getpid())
        return identity is not None and identity['birth'] == own.rsplit(')', 1)[1].split()[19]
    except (OSError, IndexError, ValueError):
        return False


def _process_identity(pid: int) -> dict | None:
    """Linux PID plus birth tick: a reused PID cannot establish liveness."""
    return _read_process_identity(pid) if _process_table_supported() else None


def _session_processes(session: int) -> list[dict] | None:
    if not _process_table_supported():
        return None
    return [identity for path in Path('/proc').iterdir() if path.name.isdigit()
            if (identity := _read_process_identity(int(path.name))) is not None
            and identity['session'] == session and identity['state'] not in ('Z', 'X')]


def check_status(output: Path) -> dict:
    """Inspect an ordinary checkpoint without altering it or signalling anyone."""
    result = json.loads((output / 'result.json').read_text())
    result['resumable'] = (result.get('stage') == 'battery'
                           and result.get('status') != 'running')
    if result.get('status') == 'running':
        owner = result.get('controller') or {}
        now = _process_identity(owner.get('pid')) if type(owner.get('pid')) is int else None
        alive = (now is not None and now['birth'] == owner.get('birth')
                 and now['state'] not in ('Z', 'X'))
        result['controller_alive'] = alive if owner.get('birth') is not None and _process_table_supported() else None
        child = result.get('child_process') or {}
        members = _session_processes(child['session']) if type(child.get('session')) is int else None
        if result['controller_alive'] is False:
            result.update(status='controller_lost_child_alive' if members else 'parent_interrupted_unclean',
                          reason='Controller exited without a terminal checkpoint; inspect descendants before restarting.')
        elif result['controller_alive'] is None:
            result.update(status='liveness_unknown', reason='No verifiable controller identity in this checkpoint.')
        result['resumable'] = False
        result['live_session_processes'] = members
    if result.get('status') == 'interrupted':
        result['resumable'] = result['resumable'] and result.get('child_cleanup', {}).get('session_empty') is True
    return result

STAGES = {
    "lint": ("lint_generator.py", "Static structure, metadata, RNG and axis declarations"),
    "selfcheck": ("generator_selfcheck.py", "Determinism, invariants, mutation sensitivity"),
    "rule_smoke": ("rule_smoke.py", "Racket execution, output diversity and purity"),
    "defect_lint": ("generator_defect_lint.py", "Known generator defects and rule-hash drift"),
    "dist_gate": ("generator_distribution_gate.py", "Canonical distribution comparison"),
    "profile_floor": ("canonical_profile_gate.py", "Canonical acceptance and profile support"),
    "semantic_gate": ("generator_semantic_gate.py", "Semantic witnesses and counterfactual checks"),
    "diversity": ("gen_diversity_probe.py", "Generated input/output diversity"),
    "override": ("check_generator_override_contract.py", "Declared override axes and unknown keys"),
    "grammar": ("grammar_gate.py", "DSL admissibility and callable inventory"),
    "racket_lint": ("racket_linter.py", "Canonical Racket source lint"),
    "authority_sync": ("check_task_authority_sync.py", "Selected/archival rule authority agreement"),
}



def _runtime_mappings(catalog: Catalog, wanted: set[str] | None):
    """The same source selection for snapshots and source-identity checks."""
    if wanted is not None:
        wanted = set(wanted)
        pending = list(wanted)
        while pending:
            task = pending.pop()
            try:
                dependencies = catalog.describe(task).get('runtime_dependencies', [])
            except KeyError:
                # A selected rule task may be a canonical-only identity.
                continue
            if not isinstance(dependencies, list) or any(not isinstance(dep, str) or not dep for dep in dependencies):
                raise ValueError(f'Invalid runtime dependencies for {task}')
            for dependency in dependencies:
                try:
                    dep = catalog.describe(dependency)['id']
                except KeyError as error:
                    raise ValueError(f'Unknown runtime dependency for {task}: {dependency}') from error
                if dep not in wanted:
                    wanted.add(dep)
                    pending.append(dep)
    mapping = json.loads((catalog.root / "catalog/runtime_files.json").read_text())
    authorities = json.loads((catalog.root / "catalog/authority_files.json").read_text())
    seen = set()
    for item in mapping:
        relative, target = item["path"], item["target"]
        if wanted is not None:
            if relative.startswith("generators/") and Path(relative).parts[1] not in wanted:
                continue
            if target.startswith("data/base/solutions/") and authorities.get(target) not in wanted:
                continue
        if target in seen:
            raise ValueError(f"Duplicate runtime target: {target}")
        seen.add(target)
        yield item


def generation_source_identity(catalog: Catalog, task_id: str) -> str:
    """Hash exact selected generation source bytes without copying a runtime tree.

    Includes the selected generator, mapped helpers/canonical data/archival
    authority, worker and controller. Paths in the recipe are library-relative,
    so relocation alone does not change identity.
    """
    row = catalog.describe(task_id)
    wanted = {row["id"], row.get("rule_task_id", row["id"])}
    files = []
    for item in _runtime_mappings(catalog, wanted):
        source = local_path(catalog.root, item["path"])
        if source.is_symlink() or not source.is_file():
            raise FileNotFoundError(f"Missing regular generation source: {source}")
        files.append({"library_path": item["path"], "runtime_path": item["target"], "sha256": sha256(source)})
    recipe = {"schema": "arcpuzzles-generation-sources-v1", "task_id": row["id"],
              "files": sorted(files, key=lambda item: item["runtime_path"]),
              "catalog_provenance": {key: row.get(key) for key in
                                     ("approved", "train_safety", "family", "split", "rule_hash", "rule_task_id")},
              "worker_sha256": sha256(Path(__file__).with_name("worker.py")),
              "controller_sha256": sha256(Path(__file__)),
              "cli_sha256": sha256(Path(__file__).with_name("cli.py"))}
    return hashlib.sha256(json.dumps(recipe, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def prepare_runtime(catalog: Catalog, destination: Path, task_id: str | None = None,
                    *, task_ids: list[str] | None = None) -> dict[str, Any]:
    """Copy local sources into a portable execution layout; never use symlinks."""
    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"Runtime destination must be empty: {destination}")
    if destination == catalog.root or destination in catalog.root.parents:
        raise ValueError("Runtime destination cannot contain the library")
    destination.mkdir(parents=True, exist_ok=True)
    if task_id is not None and task_ids is not None:
        raise ValueError("Use task_id or task_ids, not both")
    selected = [catalog.describe(tid) for tid in task_ids] if task_ids is not None else (
        [catalog.describe(task_id)] if task_id else [])
    row = selected[0] if task_id else None
    wanted = {identity for item in selected for identity in
              (item["id"], item.get("rule_task_id", item["id"]))} if selected else None
    if task_ids is not None and not selected:
        raise ValueError("task_ids cannot be empty")
    files = []
    for item in _runtime_mappings(catalog, wanted):
        relative, target = item["path"], item["target"]
        source = local_path(catalog.root, relative)
        output = local_path(destination, target)
        if source.is_symlink() or not source.is_file():
            raise FileNotFoundError(f"Missing regular library source: {source}")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
        files.append({"library_path": relative, "runtime_path": target, "sha256": sha256(output)})
    shutil.copy2(Path(__file__).with_name("worker.py"), destination / "arcpuzzles_worker.py")
    shutil.copy2(Path(__file__).with_name("export_worker.py"), destination / "arcpuzzles_export_worker.py")
    shutil.copy2(Path(__file__).with_name("native_export.py"), destination / "arcpuzzles_native_export.py")
    reader = destination / 'scripts/receipt_input.py'
    reader.parent.mkdir(exist_ok=True)
    reader_source = Path(__file__).with_name('receipt_input.py')
    if reader.exists() and reader.read_bytes() != reader_source.read_bytes():
        raise ValueError('Mapped runtime receipt reader conflicts with the installed reader')
    if not reader.exists():
        shutil.copy2(reader_source, reader)
    (destination / "requirements.txt").write_text("numpy>=1.26\nPillow>=10\npytest>=8\n")
    (destination / "requirements-tensors.txt").write_text("torch>=2.5\nsafetensors>=0.5\n")
    receipt = {"schema": "arcpuzzles-runtime-v1", "task_id": row["id"] if row else None,
               "receipt_input_sha256": sha256(reader),
               "canonical_scope": "full imported canonical ledger", "base_authority_scope": sorted(wanted) if wanted else "all",
               "task_ids": [item["id"] for item in selected], "files": files}
    receipt['dependency_task_ids'] = sorted({Path(item['library_path']).parts[1] for item in files
        if item['library_path'].startswith('generators/')
        and wanted is not None and Path(item['library_path']).parts[1] not in wanted})
    (destination / "RUNTIME_MANIFEST.json").write_text(json.dumps(receipt, indent=2) + "\n")
    for item in selected:
        if not item["generator"]:
            continue
        staged = local_path(destination, item["runtime_generator"])
        if sha256(staged) != item["generator_sha256"]:
            raise RuntimeError("Generator changed while preparing runtime; prepare a new snapshot")
    return receipt


def run_process(command: list[str], cwd: Path, *, timeout: float = 180,
                on_output: Callable[[str], None] | None = None,
                on_start: Callable[[dict], None] | None = None,
                extra_env: dict[str, str] | None = None) -> dict[str, Any]:
    """Capture the actual exit code and terminate the process group on timeout."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    # Legacy shell tools invoke python3; keep them in the API's environment
    # even when its entry point was launched without activating the venv.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["TERM"] = "dumb"
    env["NO_COLOR"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    env.update(extra_env or {})
    # A relocated Python environment can carry its own racket launcher.
    # Honor the selected runtime before that launcher for PATH-consuming gates.
    if env.get("RACKET_PATH"):
        racket = shutil.which(env["RACKET_PATH"], path=env["PATH"])
        if racket:
            env["PATH"] = str(Path(racket).absolute().parent) + os.pathsep + env["PATH"]
    process = subprocess.Popen(command, cwd=cwd, env=env, text=on_output is None, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    def stop_session() -> tuple[str, str]:
        def send(signum, *, keep_leader=False):
            members = _session_processes(process.pid)
            groups = {p['group'] for p in members} if members is not None else {process.pid}
            # Bash job control and GNU timeout can create additional groups.
            # All belong to our new session; never signal a caller's session.
            for group in groups:
                if keep_leader and group == process.pid:
                    continue
                with suppress(ProcessLookupError):
                    os.killpg(group, signum)
        send(signal.SIGTERM)
        try:
            tails = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            # Let the battery parent commit its final aggregate after its
            # stubborn stage descendants are killed. It cannot start new work
            # after TERM, and this grace is bounded independently of the stage.
            send(signal.SIGKILL, keep_leader=True)
            try:
                tails = process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                send(signal.SIGKILL)
                tails = process.communicate()
        # A descendant may have closed the captured pipes without exiting.
        send(signal.SIGKILL)
        return tails
    try:
        if on_start is not None:
            on_start(_process_identity(process.pid) or {'pid': process.pid, 'session': process.pid})
        if on_output is None:
            stdout, stderr = process.communicate(timeout=timeout)
        else:
            # Read both pipes concurrently. The callback sees progress while the
            # same bytes are retained in the receipt; no PYTHONPATH is inherited.
            captured = {"stdout": [], "stderr": []}
            encoding = locale.getpreferredencoding(False)
            decoders = {name: codecs.getincrementaldecoder(encoding)() for name in captured}
            deadline = time.monotonic() + timeout
            with selectors.DefaultSelector() as selector:
                for name in captured:
                    selector.register(getattr(process, name), selectors.EVENT_READ, name)
                try:
                    while selector.get_map():
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise subprocess.TimeoutExpired(command, timeout)
                        for key, _ in selector.select(remaining):
                            raw = os.read(key.fd, 65536)
                            captured[key.data].append(raw)
                            chunk = decoders[key.data].decode(raw, final=not raw)
                            if chunk:
                                on_output(chunk)
                            if not raw:
                                selector.unregister(key.fileobj)
                    process.wait(timeout=max(0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    timed_out = True
                    tails = stop_session()
                    for name, raw in zip(captured, tails):
                        captured[name].append(raw)
                        chunk = decoders[name].decode(raw, final=True)
                        if chunk:
                            on_output(chunk)
            stdout, stderr = (b"".join(captured[name]).decode(encoding) for name in captured)
    except subprocess.TimeoutExpired:
        timed_out = True
        stdout, stderr = stop_session()
    except BaseException as exc:
        # Interrupted callers must not leave a generator/Racket process running.
        stop_session()
        members = _session_processes(process.pid)
        # Allow the kernel to reap a just-signalled descendant before publishing
        # a clean interruption. Unknown liveness never authorizes resume.
        deadline = time.monotonic() + 1
        while members and time.monotonic() < deadline:
            time.sleep(.01)
            members = _session_processes(process.pid)
        exc.child_cleanup = {'session': process.pid, 'session_empty': members == [],
                             'remaining_processes': members}
        raise
    return {"command": command, "exit_code": process.returncode, "timed_out": timed_out,
            "stdout": stdout, "stderr": stderr}


def demonstration_policy(stage: Path, row: dict[str, Any], requested: int | None,
                         *, default_floor: int = 3) -> dict[str, Any]:
    """Resolve a literal declaration from the selected, hash-bound source only."""
    source = local_path(stage, row["runtime_generator"]).read_bytes()
    if hashlib.sha256(source).hexdigest() != row["generator_sha256"]:
        raise RuntimeError("Staged generator differs from its admission snapshot")
    minimum = None
    for statement in ast.parse(source).body:
        targets = (statement.targets if isinstance(statement, ast.Assign) else
                   [statement.target] if isinstance(statement, ast.AnnAssign) else [])
        if any(isinstance(target, ast.Name) and target.id == "EXAMPLES_NEEDED" for target in targets):
            try:
                value = ast.literal_eval(statement.value)
            except (ValueError, TypeError) as exc:
                raise ValueError("EXAMPLES_NEEDED must be a literal integer in 1..32") from exc
            if type(value) is not int or not 1 <= value <= 32:
                raise ValueError("EXAMPLES_NEEDED must be a literal integer in 1..32")
            minimum = value
    if requested is not None and (type(requested) is not int or requested < 1):
        raise ValueError("n_train must be a positive integer or omitted")
    return {"requested_n_train": requested, "resolved_n_train": (requested if requested is not None
            else max(default_floor, minimum or 0)), "declared_minimum": minimum,
            "default_floor": default_floor, "automatic": requested is None}


def generate(catalog: Catalog, task_id: str, *, count: int = 1, seed: int = 0,
             difficulty: str | None = None, n_train: int | None = None, n_test: int = 1,
             sample_index: int = 0, overrides: dict[str, Any] | None = None,
             allow_unapproved: bool = False, timeout: float = 180,
             reference: str = "canonical", start_index: int = 0) -> list[dict[str, Any]]:
    """Generate Racket-verified episodes from a fixed copy of local source."""
    for name, value in (("count", count), ("n_train", n_train), ("n_test", n_test)):
        if name == "n_train" and value is None:
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError("difficulty must be easy, medium, or hard")
    if reference not in {"canonical", "archival"}:
        raise ValueError("reference must be canonical or archival")
    if reference == "archival" and not allow_unapproved:
        raise ValueError("Archival reference execution requires allow_unapproved; it never inherits approval")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(start_index) is not int or not 0 <= start_index < count:
        raise ValueError("start_index must be an integer in 0..count-1")
    overrides = dict(overrides or {})
    if any(not isinstance(key, str) or not key.isidentifier() for key in overrides):
        raise ValueError("Override keys must be Python argument names")
    if {"seed", "sample_index", "difficulty"} & overrides.keys():
        raise ValueError("Use the explicit seed, sample_index, and difficulty arguments")
    json.dumps(overrides, allow_nan=False)  # Reject values the worker cannot reproduce.
    row = catalog.describe(task_id)
    if not row["has_generator"]:
        raise ValueError(f"{task_id} has no generator")
    if not row["approved"] and not allow_unapproved:
        raise ValueError(f"{task_id} is not approved: {', '.join(row['approval_reasons'])}; use allow_unapproved for explicit research")
    if row["kind"] == "generic" and overrides:
        raise ValueError("Generic generators support difficulty, but no override axes")
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-generate-") as directory:
        stage = Path(directory)
        prepare_runtime(catalog, stage, row["id"])
        if sha256(local_path(stage, row["runtime_generator"])) != row["generator_sha256"]:
            raise RuntimeError("Generator changed after approval lookup; retry with a fresh catalog")
        return generate_in_runtime(stage, row, count=count, seed=seed, difficulty=difficulty,
                                   n_train=n_train, n_test=n_test, sample_index=sample_index,
                                   overrides=overrides, timeout=timeout, reference=reference,
                                   start_index=start_index)


MAX_APPLY_INPUTS = 64


def validate_grid(value: Any, label: str = "grid") -> list[list[int]]:
    """A rectangular 1..30 x 1..30 list of integer colors 0..9; bools are not colors."""
    if not isinstance(value, list) or not 1 <= len(value) <= 30:
        raise ValueError(f"{label} must be a list of 1..30 rows")
    width = None
    for row in value:
        if not isinstance(row, list) or not 1 <= len(row) <= 30:
            raise ValueError(f"{label} rows must be lists of 1..30 cells")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError(f"{label} cells must be integers 0..9")
        if width is not None and len(row) != width:
            raise ValueError(f"{label} is ragged")
        width = len(row)
    return value


def parse_apply_inputs(payload: Any) -> list[list[list[int]]]:
    """Accept a grid, {"input": grid}, {"inputs": [...]}, or a list of grids / {"input": grid}."""
    if isinstance(payload, dict):
        if set(payload) == {"input"}:
            payload = [payload]
        elif set(payload) == {"inputs"}:
            payload = payload["inputs"]
        else:
            raise ValueError('object input must have exactly one key: "input" or "inputs"')
    if not isinstance(payload, list) or not payload:
        raise ValueError("input must be a grid or a nonempty list of grids")
    if isinstance(payload[0], list) and payload[0] and not isinstance(payload[0][0], list):
        payload = [payload]
    items = [item["input"] if isinstance(item, dict) and set(item) == {"input"} else item for item in payload]
    if len(items) > MAX_APPLY_INPUTS:
        raise ValueError(f"at most {MAX_APPLY_INPUTS} inputs per call")
    return [validate_grid(item, f"input {index}") for index, item in enumerate(items)]


def _grid_sha256(grid: Any) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


class ApplyFailure(RuntimeError):
    def __init__(self, task_id: str, run: dict[str, Any]):
        self.run = run
        super().__init__(f"Rule application failed for {task_id} (exit={run['exit_code']}, "
                         f"timeout={run['timed_out']}):\n" + run["stderr"][-4000:])


def apply_rule(catalog: Catalog, task_id: str, inputs: list[list[list[int]]], *, reference: str = "canonical",
               allow_unapproved: bool = False, timeout: float = 120,
               check_generator_domain: bool = False) -> dict[str, Any]:
    """Run a task's reference rule on hand-made grids; never changes approval or admits data."""
    inputs = [validate_grid(grid, f"input {index}") for index, grid in enumerate(inputs)]
    if not inputs or len(inputs) > MAX_APPLY_INPUTS:
        raise ValueError(f"supply 1..{MAX_APPLY_INPUTS} inputs")
    if reference not in {"canonical", "archival"}:
        raise ValueError("reference must be canonical or archival")
    if reference == "archival" and not allow_unapproved:
        raise ValueError("Archival reference execution requires allow_unapproved; it never inherits approval")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    row = catalog.describe(task_id)
    if not row["has_generator"] or row["kind"] != "per_puzzle":
        raise ValueError(f"{task_id}: apply needs a per-puzzle generator whose canonical rule can be resolved")
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-apply-") as directory:
        stage = Path(directory)
        prepare_runtime(catalog, stage, row["id"])
        if sha256(local_path(stage, row["runtime_generator"])) != row["generator_sha256"]:
            raise RuntimeError("Generator changed after lookup; retry with a fresh catalog")
        request = {"mode": "apply", "task_id": row["id"], "runtime_generator": row["runtime_generator"],
                   "reference": reference, "inputs": inputs,
                   "check_generator_domain": check_generator_domain}
        (stage / "request.json").write_text(json.dumps(request))
        run = run_process([sys.executable, "-E", "-s", str(stage / "arcpuzzles_worker.py")], stage, timeout=timeout)
        if run["timed_out"] or run["exit_code"] != 0:
            raise ApplyFailure(row["id"], run)
        applied = json.loads((stage / "applied.json").read_text())
    results = []
    for grid, result in zip(inputs, applied["results"], strict=True):
        results.append({**result, "input": grid, "input_sha256": _grid_sha256(grid),
                        "output_sha256": _grid_sha256(result["output"]) if result["output"] is not None else None})
    return {"schema": "arcpuzzles-apply-v1", "task_id": row["id"], "rule_task_id": applied["rule_task_id"],
            "reference": reference, "rule_file": applied["rule_file"],
            "executed_rule_hash": applied["executed_rule_hash"], "catalog_rule_hash": row["rule_hash"],
            "rule_hash_matches_catalog": applied["executed_rule_hash"] == row["rule_hash"],
            "rule_text_sha256": applied["rule_text_sha256"], "generator_sha256": row["generator_sha256"],
            "catalog_approved": row["approved"],
            "approved": row["approved"] and reference == "canonical" and applied["executed_rule_hash"] == row["rule_hash"],
            "train_safety": row["train_safety"],
            "elapsed_seconds": round(time.monotonic() - started, 3), "results": results,
            "note": "Reference output for audit evidence; not a training label or approval."}


class GenerationFailure(RuntimeError):
    """A failed worker with its full process receipt available to batch exporters.

    `partial_episodes` holds the episodes the worker completed before failing,
    in index order, with provenance; they are never returned as a complete batch.
    """

    def __init__(self, task_id: str, run: dict[str, Any], partial_episodes: list | None = None,
                 requested: int | None = None):
        self.run = run
        self.partial_episodes = partial_episodes or []
        self.requested = requested
        kept = (f"; {len(self.partial_episodes)}/{requested} episodes completed and kept"
                if requested is not None else "")
        hint = "; raise --timeout and resume" if run["timed_out"] else ""
        super().__init__(f"Generation failed for {task_id} "
                         f"(exit={run['exit_code']}, timeout={run['timed_out']}{kept}{hint}):\n"
                         + run["stderr"][-6000:] + run["stdout"][-2000:])


def generate_in_runtime(stage: Path, row: dict[str, Any], *, count: int, seed: int,
                        difficulty: str | None, n_train: int | None, n_test: int,
                        sample_index: int = 0, overrides: dict[str, Any] | None = None,
                        timeout: float = 180, reference: str = "canonical",
                        start_index: int = 0, default_n_train: int = 3) -> list[dict[str, Any]]:
    """Generate sequentially in a previously pinned local runtime snapshot.

    Returns episodes start_index..count-1. On failure, GenerationFailure carries
    the episodes completed before the failure.
    """
    if sha256(local_path(stage, row["runtime_generator"])) != row["generator_sha256"]:
        raise RuntimeError("Staged generator differs from its admission snapshot")
    if reference not in {"canonical", "archival"}:
        raise ValueError("reference must be canonical or archival")
    policy = demonstration_policy(stage, row, n_train, default_floor=default_n_train)
    overrides = dict(overrides or {})
    request = {"task_id": row["id"], "count": count, "seed": seed, "difficulty": difficulty,
               "n_train": policy["resolved_n_train"], "demonstration_policy": policy,
               "n_test": n_test, "kind": row["kind"],
               "sample_index": sample_index, "overrides": overrides,
               "runtime_generator": row["runtime_generator"], "reference": reference,
               "start_index": start_index}
    (stage / "request.json").write_text(json.dumps(request))
    partial_path = stage / "episodes.partial.jsonl"
    partial_path.unlink(missing_ok=True)
    try:
        run = run_process([sys.executable, "-E", "-s", str(stage / "arcpuzzles_worker.py")], stage, timeout=timeout)
    except KeyboardInterrupt:
        # run_process already stopped the child group; preserve its flushed prefix
        # before the disposable runtime is removed.
        run = {"command": [], "exit_code": 130, "timed_out": False, "interrupted": True,
               "stdout": "", "stderr": "Generation interrupted by keyboard signal"}
    if run["timed_out"] or run["exit_code"] != 0:
        kept = []
        if partial_path.exists():
            for line in partial_path.read_text().splitlines():
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    break  # a torn final line is not a completed episode
                if not isinstance(item, dict) or item.get("episode_index") != start_index + len(kept):
                    break
                if start_index + len(kept) >= count:
                    break
                kept.append(item)
        _attach_provenance(kept, row, difficulty, overrides, reference, policy)
        raise GenerationFailure(row["id"], run, kept, count - start_index)
    episodes = json.loads((stage / "episodes.json").read_text())
    if len(episodes) != count - start_index:
        raise RuntimeError("Worker returned fewer episodes than requested")
    _attach_provenance(episodes, row, difficulty, overrides, reference, policy)
    return episodes


def _attach_provenance(episodes: list[dict[str, Any]], row: dict[str, Any], difficulty: str | None,
                       overrides: dict[str, Any], reference: str,
                       policy: dict[str, Any]) -> list[dict[str, Any]]:
    for episode in episodes:
        approved = row["approved"] and reference == "canonical"
        if approved and episode.get("executed_rule_hash") != row["rule_hash"]:
            raise RuntimeError(f"{row['id']}: executed rule differs from the approved canonical rule")
        episode["provenance"] = {"schema": "arcpuzzles-generation-v1", "generator_sha256": row["generator_sha256"],
                                 "rule_hash": episode["executed_rule_hash"],
                                 "catalog_rule_hash": row["rule_hash"], "reference": reference,
                                 "family": row["family"], "split": row["split"],
                                 "difficulty": difficulty, "overrides": overrides,
                                 "demonstration_policy": policy,
                                 "lesson_check": episode.get("lesson_check", {"status": "not_recorded"}),
                                 "approved": approved, "train_safety": (row["train_safety"]
                                     if reference == "canonical" or row["train_safety"] == "unsafe" else "unverified"),
                                 "catalog_approved": row["approved"], "catalog_train_safety": row["train_safety"]}
    return episodes


def _task_test_snapshot(catalog: Catalog, root: Path, receipt: dict, tid: str) -> list[str]:
    """Mirror selected library/API sources beside the legacy runtime layout."""
    def copy(source: Path, relative: str, identity: str) -> None:
        if source.is_symlink():
            raise ValueError(f"Task test source cannot be a symlink: {source}")
        if not source.is_file():
            return
        target = local_path(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_bytes()
        if target.exists():
            if target.read_bytes() != raw:
                raise RuntimeError(f"Source changed while preparing task tests: {identity}")
            return
        target.write_bytes(raw)
        receipt["files"].append({"library_path": identity, "runtime_path": relative,
                                 "sha256": hashlib.sha256(raw).hexdigest()})

    # Public Catalog calls inside tests must use this snapshot, not the owner
    # checkout. Legacy frozen fixtures keep their existing execution paths.
    for item in list(receipt["files"]):
        copy(local_path(catalog.root, item["library_path"]), item["library_path"], item["library_path"])
    for source in (catalog.root / "catalog").iterdir():
        copy(source, "catalog/" + source.name, "catalog/" + source.name)
    copy(catalog.root / "shared/data/canonical/puzzles.jsonl",
         "shared/data/canonical/puzzles.jsonl", "shared/data/canonical/puzzles.jsonl")
    home = catalog.root / "generators" / tid
    for source in home.rglob("*"):
        relative = source.relative_to(catalog.root)
        if "__pycache__" in relative.parts or "evidence" in relative.parts or source.suffix == ".pyc":
            continue
        copy(source, relative.as_posix(), relative.as_posix())
    package = Path(__file__).parent
    for source in package.rglob("*.py"):
        relative = source.relative_to(package).as_posix()
        copy(source, "src/arcpuzzles/" + relative, "<controller>/arcpuzzles/" + relative)
    tests = root / "generators" / tid / "tests"
    canonical_tests = {p.relative_to(root).as_posix() for p in tests.rglob("*.py")
                       if p.is_file() and (p.name.startswith("test_") or p.name.endswith("_test.py"))}
    selected = [tests.relative_to(root).as_posix()] if canonical_tests else []
    frozen = root / "generators" / tid / f"test_generator_{tid}.py"
    if frozen.is_file():
        relative = frozen.relative_to(root).as_posix()
        selected.append(relative)
        canonical_tests.add(relative)
    # Keep legacy files for imports, but do not collect the same source twice.
    # Source identity matters: equal bytes from distinct test homes can carry
    # different fixtures and must remain separate tests.
    mirrored = {item["runtime_path"] for item in receipt["files"]
                if item["library_path"] in canonical_tests
                and item["runtime_path"] != item["library_path"]}
    omitted = []
    for path in sorted((root / "tests").glob(f"test_generator_{tid}*.py")):
        relative = path.relative_to(root).as_posix()
        if relative in mirrored:
            omitted.append(relative)
        else:
            selected.append(relative)
    receipt["task_test_collection"] = {"roots": selected, "omitted_mirrors": omitted,
                                       "deduplication": "same_library_source"}
    (root / "RUNTIME_MANIFEST.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return selected


def _static_test_path(node, names, test_path, root):
    """Resolve a small literal Path expression without importing test code."""
    try:
        if isinstance(node, ast.Name):
            return test_path if node.id == '__file__' else names.get(node.id)
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)):
            return node.value
        if isinstance(node, ast.Call) and not node.keywords:
            if isinstance(node.func, ast.Name) and node.func.id == 'Path' and len(node.args) == 1:
                value = _static_test_path(node.args[0], names, test_path, root)
                return Path(value) if value is not None else None
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'resolve' and not node.args:
                value = _static_test_path(node.func.value, names, test_path, root)
                if isinstance(value, Path):
                    return (root / value).resolve()
        if isinstance(node, ast.Attribute):
            value = _static_test_path(node.value, names, test_path, root)
            if isinstance(value, Path) and node.attr in ('parent', 'parents'):
                return getattr(value, node.attr)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == 'parents':
            value = _static_test_path(node.value, names, test_path, root)
            index = _static_test_path(node.slice, names, test_path, root)
            if value is not None and type(index) is int:
                return value[index]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left = _static_test_path(node.left, names, test_path, root)
            right = _static_test_path(node.right, names, test_path, root)
            if isinstance(left, Path) and isinstance(right, (str, Path)):
                return left / right
    except (IndexError, TypeError, ValueError):
        pass
    return None


def _missing_legacy_import(root, node, module):
    path = root.joinpath(*module.split('.'))
    source = path.with_suffix('.py')
    if not source.is_file():
        if path.is_dir():  # Namespace package or package; leave symbols to Python.
            return None
        return f'Missing staged module {module}.'
    if isinstance(node, ast.ImportFrom):
        try:
            tree = ast.parse(source.read_text())
        except (SyntaxError, UnicodeError):
            return None
        # Dynamic exports cannot be proven absent statically.
        if any(isinstance(n, ast.ImportFrom) and any(a.name == '*' for a in n.names)
               or isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == '__getattr__'
               for n in ast.walk(tree)):
            return None
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        names.update(n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
        names.update(a.asname or a.name.split('.')[0] for n in ast.walk(tree)
                     if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names)
        missing = [a.name for a in node.names if a.name.startswith('_') and a.name not in names]
        if missing:
            return f'Missing private import from {module}: {", ".join(missing)}.'
    return None


def _task_test_import_diagnostics(root: Path, selected: list[str]) -> list[dict]:
    """Preflight known missing dependencies without importing tests.

    Available legacy imports remain warnings; unresolved dynamic paths are left
    to pytest. Only statically known missing paths/modules/private names block.
    """
    diagnostics = []
    paths = set()
    for relative in selected:
        path = local_path(root, relative)
        paths.update(path.rglob('*.py') if path.is_dir() else [path])
    for path in sorted(paths):
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except (SyntaxError, UnicodeError):
            continue  # pytest retains its normal syntax/collection error
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        def guarded(node):
            while node in parents:
                node = parents[node]
                if isinstance(node, (ast.Try, ast.TryStar, ast.If, ast.IfExp)):
                    return True
            return False
        assignments = {}
        for candidate in ast.walk(tree):
            if isinstance(candidate, ast.Name) and isinstance(candidate.ctx, ast.Store):
                assignments[candidate.id] = assignments.get(candidate.id, 0) + 1
        rebound = {name for name, count in assignments.items() if count > 1}
        def uncertain_path(node):
            # An initial missing candidate may have a portable fallback later.
            owner = parents.get(node)
            targets = owner.targets if isinstance(owner, ast.Assign) else []
            return any(isinstance(n, ast.Name) and n.id in rebound
                       for part in (node, *targets) for n in ast.walk(part))
        def unguarded_read(node):
            owner = parents.get(node)
            targets = {t.id for t in owner.targets if isinstance(t, ast.Name)} if isinstance(owner, ast.Assign) else set()
            for call in ast.walk(tree):
                if not isinstance(call, ast.Call) or guarded(call):
                    continue
                value = None
                if isinstance(call.func, ast.Attribute) and call.func.attr in ('read_text', 'read_bytes', 'open'):
                    value = call.func.value
                elif isinstance(call.func, ast.Name) and call.func.id == 'open' and call.args:
                    value = call.args[0]
                if value is node or isinstance(value, ast.Name) and value.id in targets:
                    return True
            return False
        names = {}
        for assignment in tree.body:
            if isinstance(assignment, ast.Assign):
                value = _static_test_path(assignment.value, names, path, root)
                for target in assignment.targets:
                    if isinstance(target, ast.Name):
                        names[target.id] = value
        fixed_roots = set()
        for assignment in ast.walk(tree):
            if isinstance(assignment, ast.Assign):
                nodes = list(ast.walk(assignment.value))
                if (any(isinstance(n, ast.Name) and n.id == '__file__' for n in nodes)
                        and any(isinstance(n, ast.Attribute) and n.attr in ('parent', 'parents') for n in nodes)):
                    fixed_roots.update(t.id for t in assignment.targets if isinstance(t, ast.Name))
        path_lines = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                nodes = list(ast.walk(node))
                strings = [n.value for n in nodes if isinstance(n, ast.Constant) and isinstance(n.value, str)]
                direct = (any(isinstance(n, ast.Name) and n.id == '__file__' for n in nodes)
                          and any(isinstance(n, ast.Attribute) and n.attr in ('parent', 'parents') for n in nodes))
                derived = any(isinstance(n, ast.Name) and n.id in fixed_roots for n in nodes)
                if (direct or derived) and 'canonical' in '/'.join(strings) and node.lineno not in path_lines:
                    path_lines.add(node.lineno)
                    resolved = _static_test_path(node, names, path, root)
                    missing = isinstance(resolved, Path) and not (root / resolved).exists() and not guarded(node) and not uncertain_path(node) and unguarded_read(node)
                    diagnostics.append({'path': path.relative_to(root).as_posix(), 'line': node.lineno,
                        'severity': 'error' if missing else 'warning', 'code': 'fixed_depth_canonical_path',
                        'message': (f'Missing canonical path {resolved}. ' if missing else '') + 'Fixed __file__/parents depth can point beneath a task in the portable runtime. '
                                   'Use reviewer_support.find_root(__file__), canonical_path, and canonical_pairs.'})
            modules = ([node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 else
                       [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
            for module in modules:
                if module and (module == 'scripts' or module.startswith('scripts.')):
                    missing = None if guarded(node) else _missing_legacy_import(root, node, module)
                    diagnostics.append({'path': path.relative_to(root).as_posix(), 'line': node.lineno,
                        'severity': 'error' if missing else 'warning', 'code': 'legacy_scripts_import',
                        'message': (missing + ' ' if missing else '') + f'{module} uses the legacy staged runtime namespace. '
                                   'For canonical data use reviewer_support.canonical_pairs, canonical_path, find_root; '
                                   'for other internals use a documented public API or a task-local helper. '
                                   'Replay retained tests with arcpuzzles check TASK --stage task_tests.'})
    return diagnostics


def _task_test_counts(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        root = ElementTree.parse(path).getroot()
        suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
        if not suites:
            return None
        counts = {name: sum(int(s.get(attribute, '0')) for s in suites)
                  for name, attribute in (('tests', 'tests'), ('failed', 'failures'),
                                          ('errors', 'errors'), ('skipped', 'skipped'))}
        counts['passed'] = counts['tests'] - counts['failed'] - counts['errors'] - counts['skipped']
        return counts
    except (ElementTree.ParseError, ValueError):
        return None  # interrupted/malformed evidence cannot imply a zero-error run


def _write_audit_summary(root: Path, result: dict) -> None:
    """Describe only the requested preset; keep native battery evidence separate."""
    if result.get('stage') != 'audit':
        return
    expected = ('task_tests', 'semantic_gate')
    outcomes = result.get('audit_stages', {})
    stages = {
        name: {key: value for key, value in outcomes.get(name, {}).items()
               if key in ('status', 'passed', 'exit_code', 'timed_out', 'reason',
                          'test_status', 'test_counts', 'semantic_status')}
        for name in expected
    }
    for row in stages.values():
        row.setdefault('status', 'not_run')
        row.setdefault('passed', None)
    status = result.get('status', 'running')
    completed = [name for name, row in stages.items()
                 if row['status'] == 'completed' and not row.get('timed_out')]
    complete = len(completed) == len(expected) and status in ('completed', 'source_changed')
    passed = result.get('passed') is True
    verdict = ('source_changed' if status == 'source_changed' else
               'interrupted' if status == 'interrupted' else
               'infrastructure_failed' if status == 'infrastructure_failed' else
               'running' if status == 'running' else
               'incomplete' if not complete else 'passed' if passed else 'failed')
    manifest = result.get('runtime_manifest') or {}
    pins = {row['sha256'] for row in manifest.get('files', [])
            if row.get('library_path') == f"generators/{result['task_id']}/generator.py"}
    summary = {
        'schema': 'arcpuzzles-audit-preset-summary-v1', 'task_id': result['task_id'],
        'expected_stages': list(expected), 'completed_stages': completed,
        'preset_complete': complete, 'passed': passed, 'verdict': verdict,
        'controller_status': status, 'stages': stages,
        'generator_sha256': next(iter(pins)) if len(pins) == 1 else None,
        'runtime_manifest_sha256': hashlib.sha256(json.dumps(
            manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            if manifest else None,
        'changed_runtime_sources': result.get('changed_runtime_sources', []),
        'completion_scope': 'Both requested stages terminated without timeout; passing additionally requires executed tests, a green semantic gate, and unchanged source.',
        'verdict_note': f"Audit preset: {len(completed)}/{len(expected)} requested stages completed; {verdict}. The separate battery summary covers all twelve stages.",
        'native_battery_summary': f"checks/{result['task_id']}_audit_battery_summary.json",
    }
    result['audit_summary'] = summary
    path = root / f"checks/{result['task_id']}_audit_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_name(path.name + '.checkpoint-tmp')
    scratch.write_text(json.dumps(summary, indent=2) + '\n')
    os.replace(scratch, path)


def _save_check_checkpoint(root: Path, output: Path, result: dict) -> None:
    """Atomic file snapshots: completed evidence survives caller interruption."""
    _write_audit_summary(root, result)
    summary = root / f"checks/{result['task_id']}_{result['phase']}_battery_summary.json"
    if result.get('status') == 'interrupted' and summary.is_file():
        with suppress(json.JSONDecodeError):
            aggregate = json.loads(summary.read_text())
            journal = root / f"checks/{result['task_id']}_{result['phase']}_commands.jsonl"
            latest = {}
            if journal.is_file():
                for line in journal.read_text().splitlines():
                    with suppress(json.JSONDecodeError):
                        row = json.loads(line)
                        if row.get('subject_sha16') == aggregate.get('subject_sha16'):
                            latest[row.get('stage')] = row
            for name, entry in aggregate.get('stages', {}).items():
                last = latest.get(name, {})
                # Already committed terminal receipts/markers remain intact.
                # A stale aggregate can precede the active stage's started row.
                receipt_path = root / f"checks/{result['task_id']}_{result['phase']}_{name}.receipt"
                terminal = False
                if receipt_path.is_file():
                    with suppress(json.JSONDecodeError):
                        receipt = json.loads(receipt_path.read_text())
                        terminal = (receipt.get('subject_sha16') == aggregate.get('subject_sha16')
                                    and receipt.get('run_id') == last.get('run_id')
                                    and type(receipt.get('exit')) is int)
                if entry.get('status') == 'running' or (last.get('status') == 'started'
                        and not terminal and entry.get('status') not in ('green', 'advisory', 'failed')):
                    entry.update(status='interrupted', exit=None)
            entries = aggregate.get('stages', {})
            for state in ('running', 'interrupted', 'pending'):
                names = [name for name, entry in entries.items() if entry.get('status') == state]
                aggregate[state + '_stages'] = names
                aggregate.setdefault('counts', {})[state] = len(names)
            aggregate['resumable_stages'] = [name for name, entry in entries.items()
                                             if entry.get('status') in ('pending', 'interrupted', 'failed')]
            aggregate.update(verdict='interrupted', controller_status='interrupted',
                             verdict_note='Controller interrupted; read the preserved per-stage evidence.',
                             generated_by='python_controller_interruption')
            if result.get('child_cleanup', {}).get('session_empty') is True:
                aggregate.setdefault('live', {}).update(pid_alive=False, used_for_verdict=False)
            scratch = summary.with_name(summary.name + '.checkpoint-tmp')
            scratch.write_text(json.dumps(aggregate, indent=2) + '\n')
            os.replace(scratch, summary)
    hashes = {}
    for source in (root / "checks").rglob("*"):
        # Battery locks are mutable coordination state, removed by worker
        # cleanup. They are not evidence and can vanish between stat/read.
        if any(part.startswith(".lock_") for part in source.relative_to(root / "checks").parts):
            continue
        if source.is_symlink():
            raise ValueError(f"Check evidence cannot be a symlink: {source}")
        if not source.is_file():
            continue
        target = local_path(output, source.relative_to(root).as_posix())
        target.parent.mkdir(parents=True, exist_ok=True)
        scratch = target.with_name(target.name + ".checkpoint-tmp")
        raw = source.read_bytes()
        scratch.write_bytes(raw)
        os.replace(scratch, target)
        hashes[source.relative_to(root).as_posix()] = hashlib.sha256(raw).hexdigest()
    result["evidence_sha256"] = hashes
    if summary.is_file():
        # The legacy writer does not atomically replace every summary. A live
        # partial write is retained as bytes, and cannot stop an otherwise
        # healthy check. The terminal read below still requires valid JSON.
        with suppress(json.JSONDecodeError):
            result["battery_summary"] = json.loads(summary.read_text())
    target = output / "result.json"
    scratch = output / "result.json.checkpoint-tmp"
    scratch.write_text(json.dumps(result, indent=2) + "\n")
    os.replace(scratch, target)


def _check_settings(root: Path) -> dict:
    """Bind explicit runtime choices without persisting environment secrets."""
    racket = os.environ.get("RACKET_PATH", "racket")
    executable = shutil.which(racket)
    patch_setting = os.environ.get("SYNC_PATCH", "")
    patch = Path(patch_setting) if patch_setting else None
    if patch is not None and not patch.is_absolute():
        patch = root / patch
    return {"racket_path": racket, "racket_sha256": sha256(Path(executable)) if executable else None,
            "python": sys.executable, "python_version": sys.version,
            "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
            "sync_patch": patch_setting,
            "sync_patch_sha256": sha256(patch) if patch is not None and patch.is_file() else None,
            "controller_sha256": sha256(Path(__file__))}


def _restore_check(root: Path, output: Path, previous: dict) -> list[str]:
    """Only committed checkpoint bytes are evidence; PIDs/locks are not."""
    invalid = set()
    prefix = f"{previous['task_id']}_{previous['phase']}_"
    hashes = previous.get("evidence_sha256", {})
    for relative, digest in hashes.items():
        path = Path(relative)
        if path.parts[0] != "checks" or any(part.startswith(".lock_") for part in path.parts):
            continue
        # Never source an inherited shell environment, even if hash-bound.
        if path.name == "racket_env.sh" or path.name.endswith(".pid") or path.name == "pid":
            continue
        source = local_path(output, relative)
        if source.is_symlink() or not source.is_file() or sha256(source) != digest:
            stage = next((name for name in STAGES if path.name.startswith(prefix + name + ".")), None)
            invalid.update([stage] if stage else STAGES)
            continue
        target = local_path(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for stage in STAGES:
        log = root / "checks" / f"{prefix}{stage}.log"
        if not log.is_file():
            invalid.add(stage)
    for stage in invalid:
        for suffix in ("ok", "receipt"):
            (root / "checks" / f"{prefix}{stage}.{suffix}").unlink(missing_ok=True)
    journal = root / "checks" / f"{prefix}commands.jsonl"
    if journal.exists():
        rows = []
        for line in journal.read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # Torn journal tail is retained in the archived attempt.
            if isinstance(row, dict) and row.get("stage") not in invalid:
                rows.append(row)
        journal.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return sorted(invalid)


def _task_test_prerequisites(root: Path, timeout: float) -> dict[str, Any]:
    """Probe imports with the exact interpreter and isolated child environment.

    Use an empty working directory before copying any task/reviewer source, so
    a library-local or user-site package cannot make this preflight pass.
    """
    probe = '''import importlib, json, os, site, sys
dependencies, errors = {}, {}
for name in ('pytest', 'numpy', 'PIL'):
    try:
        module = importlib.import_module(name)
        dependencies[name] = {'version': getattr(module, '__version__', None),
                              'path': getattr(module, '__file__', None)}
    except Exception as exc:
        errors[name] = {'type': type(exc).__name__, 'message': str(exc)}
report = {'test_interpreter': sys.executable, 'python_version': sys.version,
          'python_no_user_site': site.ENABLE_USER_SITE is False,
          'pythonpath': os.environ.get('PYTHONPATH'), 'dependencies': dependencies,
          'dependency_errors': errors,
          'missing_dependencies': [name for name, error in errors.items()
                                   if error['type'] == 'ModuleNotFoundError'],
          'passed': not errors and sys.version_info >= (3, 12)}
print(json.dumps(report))
sys.exit(0 if report['passed'] else 2)
'''
    command = [sys.executable, "-c", probe]
    try:
        run = run_process(command, root, timeout=min(timeout, 30))
    except OSError as exc:
        run = {"command": command, "exit_code": 2, "timed_out": False,
               "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}
    report = {"test_interpreter": sys.executable, "passed": False,
              "dependencies": {}, "missing_dependencies": [], "dependency_errors": {}}
    if not run["timed_out"]:
        with suppress(json.JSONDecodeError, TypeError):
            parsed = json.loads(run["stdout"])
            if isinstance(parsed, dict):
                report.update(parsed)
    report["passed"] = bool(report.get("passed") and run["exit_code"] == 0 and not run["timed_out"])
    report.update(command=command, exit_code=run["exit_code"], timed_out=run["timed_out"],
                  stdout=run["stdout"], stderr=run["stderr"])
    if not report["passed"]:
        setup = (f"{shlex.quote(sys.executable)} -m venv .venv-review && "
                 ".venv-review/bin/python -m pip install 'numpy>=1.26' 'Pillow>=10' 'pytest>=8'")
        details = "\n".join(f"{name}: {error['type']}: {error['message']}"
                            for name, error in report["dependency_errors"].items())
        report["setup_message"] = (
            f"Task-test prerequisite preflight failed for {sys.executable} with PYTHONNOUSERSITE=1. "
            "No task source was staged and no tests ran. Requires Python 3.12+ and importable pytest, NumPy and Pillow.\n"
            f"{details or run['stderr'] or 'Interpreter probe failed or timed out.'}\n"
            f"Set up the selected interpreter: {setup}\n"
            "Rerun arcpuzzles using .venv-review/bin/python; in a packet, use that same interpreter "
            "for both run_with_racket.py and its Python payload. Keep PYTHONNOUSERSITE isolation enabled.\n")
    return report


def _native_execution_timeouts(timeout: float) -> dict[str, float]:
    """Leave time for native TERM/KILL and terminal receipts before caller expiry."""
    margin = min(20.0, float(timeout) * .2)
    budget = float(timeout) - margin
    return {"controller_seconds": float(timeout), "native_budget_seconds": budget,
            "native_kill_grace_max_seconds": min(10.0, budget * .1)}


def check(catalog: Catalog, task_id: str, *, stage: str = "lint", timeout: float = 330,
          output: Path | None = None, full_battery: bool = False,
          phase: str | None = None, on_output: Callable[[str], None] | None = None,
          resume: bool = False, require_rotations_identifiable: bool = False,
          compact_results: bool = False, full_results: bool = False,
          schedule_census: Path | None = None, schedule_seed: int = 0,
          enumerate_schedule_period: bool = False) -> dict[str, Any]:
    """Resume only exact-source battery checkpoints, serialized per output."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("The check timeout must be finite and positive")
    if phase is not None and phase not in CHECK_PHASES:
        raise ValueError(f"Unknown check phase: {phase}")
    if stage == "audit":
        if phase not in (None, "audit") or full_battery or resume:
            raise ValueError("The audit preset requires phase audit, without --battery or --resume")
        phase = "audit"
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("The audit timeout must be finite and positive")
    if type(require_rotations_identifiable) is not bool:
        raise ValueError("require_rotations_identifiable must be a boolean")
    if type(schedule_seed) is not int or not 0 <= schedule_seed < 2**32:
        raise ValueError('schedule_seed must be a uint32 integer (not bool)')
    if schedule_census is not None and (stage == 'task_tests' or (not full_battery and stage not in ('semantic_gate', 'audit'))):
        raise ValueError('--schedule-census requires --stage semantic_gate, audit or --battery')
    if type(enumerate_schedule_period) is not bool:
        raise ValueError('enumerate_schedule_period must be a boolean')
    if enumerate_schedule_period and (schedule_census is not None or stage == 'task_tests'
            or (not full_battery and stage not in ('semantic_gate', 'audit'))):
        raise ValueError('--enumerate-schedule-period requires semantic_gate, audit or battery, without --schedule-census')
    if schedule_census is None and not enumerate_schedule_period and schedule_seed != 0:
        raise ValueError('--schedule-seed requires --schedule-census or --enumerate-schedule-period')
    if require_rotations_identifiable and (stage == "task_tests" or (not full_battery and stage not in ("semantic_gate", "audit"))):
        raise ValueError("--require-rotations-identifiable requires --stage semantic_gate, audit or --battery")
    if full_results and compact_results:
        raise ValueError("full_results and compact_results are mutually exclusive")
    if full_results and (stage == "task_tests" or (not full_battery and stage != "override")):
        raise ValueError("--full-results requires --stage override or --battery")
    if type(full_results) is not bool:
        raise ValueError("full_results must be a boolean")
    if type(compact_results) is not bool:
        raise ValueError("compact_results must be a boolean")
    if compact_results and (stage == "task_tests" or (not full_battery and stage != "override")):
        raise ValueError("--compact-results requires --stage override or --battery")
    if resume and (not full_battery or output is None):
        raise ValueError("--resume requires --battery and --out EXISTING")
    schedule_input = read_receipt(schedule_census) if schedule_census is not None else None
    kwargs = dict(stage=stage, timeout=timeout, output=output, full_battery=full_battery,
                  phase=phase, on_output=on_output, resume=resume,
                  require_rotations_identifiable=require_rotations_identifiable,
                  compact_results=compact_results, full_results=full_results,
                  schedule_census=schedule_census, schedule_seed=schedule_seed,
                  enumerate_schedule_period=enumerate_schedule_period,
                  schedule_input=schedule_input)
    if output is None:
        with _check_signals():
            return _check(catalog, task_id, **kwargs)
    # flock survives no dead PID state, and excludes a still-running writer.
    # Keep the lock inode in place: unlinking it would race waiting writers.
    import fcntl
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with (output.parent / f".{output.name}.check.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(f"Check output has an active writer: {output}") from exc
        with _check_signals():
            return _check(catalog, task_id, **kwargs)


def _run_audit(root: Path, result: dict, tests: list[str], preflight_errors: list[dict],
               timeout: float, options: dict, output: Path | None) -> dict:
    """Two explicit stages, one staged source and one execution-time allowance."""
    semantic = ["bash", "scripts/run_generator_battery.sh", result["task_id"], "audit",
                "semantic_gate", "--fresh"]
    if result["settings"]["require_rotations_identifiable"]:
        semantic.append("--require-rotations-identifiable")
    if result['settings'].get('schedule_census_sha256'):
        semantic.extend(['--schedule-census', 'checks/schedule-census-input.json',
                         '--schedule-seed', str(result['settings']['schedule_seed'])])
    if result['settings'].get('enumerate_schedule_period'):
        semantic.extend(['--enumerate-schedule-period', '--schedule-seed', str(result['settings']['schedule_seed'])])
    commands = {"task_tests": result["command"], "semantic_gate": semantic}
    outcomes = result["audit_stages"] = {
        name: {"status": "pending", "passed": None, "command": command}
        for name, command in commands.items()}
    deadline = time.monotonic() + timeout

    def checkpoint():
        if output is not None:
            _save_check_checkpoint(root, output, result)

    def finish(status="completed", changed=None):
        runs = list(outcomes.values())
        timed_out = any(run.get("timed_out", False) for run in runs)
        passed = status == "completed" and all(run.get("passed") is True for run in runs)
        return {"command": list(commands.values()), "status": status, "passed": passed,
                "exit_code": 0 if passed else 124 if timed_out else 1,
                "timed_out": timed_out,
                "stdout": "".join(run.get("stdout", "") for run in runs),
                "stderr": "".join(run.get("stderr", "") for run in runs),
                "changed_runtime_sources": changed or []}

    for name, command in commands.items():
        remaining = deadline - time.monotonic()
        if remaining <= 0 or (name == "semantic_gate" and outcomes["task_tests"].get("timed_out")):
            outcomes[name].update(status="not_run", passed=False, timed_out=True,
                                  reason="shared execution allowance exhausted")
            return finish()
        if name == "semantic_gate":
            limits = _native_execution_timeouts(remaining)
            command.extend(['--time-budget', format(limits['native_budget_seconds'], '.12g')])
            outcomes[name]['execution_timeouts'] = limits
        outcomes[name].update(status="running")
        result["active_audit_stage"] = name
        checkpoint()
        if name == "task_tests" and preflight_errors:
            run = {"command": command, "exit_code": 2, "timed_out": False, "stdout": "",
                   "stderr": "Task-test preflight failed before pytest:\n" + "\n".join(
                       f"{d['path']}:{d['line']}: {d['message']}" for d in preflight_errors)}
        elif name == "task_tests" and not tests:
            run = {"command": command, "exit_code": 5, "timed_out": False,
                   "stdout": "No task-local or selected frozen tests found.\n", "stderr": ""}
        else:
            stage_options = dict(options)
            if name == "semantic_gate":
                # Preserve the native gate's existing import environment.
                env = {key: value for key, value in options.get("extra_env", {}).items()
                       if key not in ("PYTHONPATH", "ARCPUZZLES_HOME")}
                stage_options["extra_env"] = env
            run = run_process(command, root, timeout=remaining, **stage_options)
        outcomes[name].update(run, status="completed",
                              passed=run["exit_code"] == 0 and not run["timed_out"])
        if name == "task_tests":
            counts = _task_test_counts(root / "checks/task_tests.xml")
            outcomes[name].update(test_paths=tests,
                                  test_status="preflight_failed" if preflight_errors else
                                  "no_tests" if run["exit_code"] == 5 else "executed",
                                  test_counts=counts)
            if outcomes[name]["passed"] and (counts is None or counts["passed"] < 1):
                outcomes[name].update(passed=False, test_status="no_executed_tests")
        else:
            summary = root / f"checks/{result['task_id']}_audit_battery_summary.json"
            record = {}
            if summary.is_file():
                with suppress(json.JSONDecodeError, TypeError, AttributeError):
                    record = json.loads(summary.read_text()).get("stages", {}).get("semantic_gate", {})
            semantic_status = record.get("status", "missing")
            outcomes[name]['timed_out'] = bool(outcomes[name].get('timed_out') or record.get('timed_out'))
            outcomes[name].update(semantic_status=semantic_status, battery_stage=record,
                                  passed=outcomes[name]["passed"] and semantic_status == "green")
        changed = [item["runtime_path"] for item in result["runtime_manifest"]["files"]
                   if (source := local_path(root, item["runtime_path"])).is_symlink()
                   or not source.is_file() or sha256(source) != item["sha256"]]
        checkpoint()
        if changed:
            if name == "task_tests":
                outcomes["semantic_gate"].update(status="not_run", passed=False,
                                                reason="staged source changed during task tests")
            return finish("source_changed", changed)
    result["active_audit_stage"] = None
    return finish()


def _check(catalog: Catalog, task_id: str, *, stage: str = "lint", timeout: float = 330,
          output: Path | None = None, full_battery: bool = False,
          phase: str | None = None, on_output: Callable[[str], None] | None = None,
          resume: bool = False, require_rotations_identifiable: bool = False,
          compact_results: bool = False, full_results: bool = False,
          schedule_census: Path | None = None, schedule_seed: int = 0,
          schedule_input: dict | None = None,
          enumerate_schedule_period: bool = False) -> dict[str, Any]:
    """Run an inherited check and retain its real warnings/failures."""
    if stage not in STAGES and stage not in ("task_tests", "audit"):
        raise ValueError(f"Unknown stage: {stage}")
    if full_battery and stage == "task_tests":
        raise ValueError("task_tests is separate from the twelve-stage battery")
    previous = None
    if resume:
        previous = json.loads((output / "result.json").read_text())
        if previous.get('status') in ('running', 'interrupted') and not check_status(output)['resumable']:
            raise ValueError('Checkpoint has unclean or unknown child liveness; inspect with check-status --out before starting a fresh output')
        if previous.get("task_id") != catalog.resolve(task_id) or previous.get("stage") != "battery":
            raise ValueError("Resume task/stage does not match saved battery")
        if phase is not None and phase != previous.get("phase"):
            raise ValueError("Phase differs from saved battery")
        phase = previous["phase"]
    phase = phase or "before"
    if phase not in CHECK_PHASES:
        raise ValueError(f"Unknown check phase: {phase}")
    if output is not None and output.exists() and not resume:
        raise FileExistsError(f"Check output already exists: {output}")
    tid = catalog.resolve(task_id)
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-check-") as directory:
        root = Path(directory)
        prerequisites = _task_test_prerequisites(root, timeout) if stage in ("task_tests", "audit") else None
        if prerequisites is not None and not prerequisites["passed"]:
            missing = prerequisites["missing_dependencies"]
            result = {"schema": "arcpuzzles-check-v1", "task_id": tid,
                      "stage": stage, "phase": phase, "passed": False,
                      "status": "infrastructure_failed", "command": prerequisites["command"],
                      "exit_code": prerequisites["exit_code"], "timed_out": prerequisites["timed_out"],
                      "stdout": "", "stderr": prerequisites["setup_message"],
                      "test_status": "dependency_missing" if missing else "prerequisite_failed",
                      "test_interpreter": sys.executable, "test_counts": None, "test_paths": None,
                      "test_prerequisite_preflight": prerequisites, "runtime_manifest": None,
                      "runtime_path": None, "battery_summary": None, "resumed": False,
                      "settings": _check_settings(root)}
            _write_audit_summary(root, result)
            if missing:
                result["missing_dependency"] = missing[0]
            if output is not None:
                output.mkdir(parents=True)
                _save_check_checkpoint(root, output, result)
            if on_output is not None:
                on_output(result["stderr"])
            return result
        receipt = prepare_runtime(catalog, root, tid)
        settings = _check_settings(root)
        settings["require_rotations_identifiable"] = require_rotations_identifiable
        settings["compact_results"] = compact_results
        settings["full_results"] = full_results
        settings['enumerate_schedule_period'] = enumerate_schedule_period
        if enumerate_schedule_period:
            settings['schedule_seed'] = schedule_seed
        if schedule_census is not None:
            source = schedule_input if schedule_input is not None else read_receipt(schedule_census)
            raw = source['raw']
            target = root / 'checks/schedule-census-input.json'
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(raw)
            settings.update(schedule_census_sha256=hashlib.sha256(raw).hexdigest(),
                            schedule_seed=schedule_seed)
            if source['transport'] is not None:
                settings['schedule_census_transport'] = source['transport']
                for name, content in source['transport_files'].items():
                    retained = root / 'checks/schedule-census-source' / name
                    retained.parent.mkdir(parents=True, exist_ok=True)
                    retained.write_bytes(content)
        invalidated = []
        if previous is not None:
            if previous.get("runtime_manifest") != receipt:
                raise ValueError("Source/authority snapshot differs; start a new --out")
            if previous.get("settings") != settings:
                raise ValueError("Settings differ or old checkpoint has no settings; start a new --out")
            invalidated = _restore_check(root, output, previous)
            attempts = output / "attempts"
            attempts.mkdir(exist_ok=True)
            index = 1
            while (attempts / f"{index:04d}").exists():
                index += 1
            archive = attempts / f"{index:04d}"
            archive.mkdir()
            for name in ("result.json", "RUNTIME_MANIFEST.json", "progress.log", "checks"):
                source = output / name
                if source.is_dir():
                    shutil.copytree(source, archive / name, symlinks=True)
                elif source.is_file():
                    shutil.copy2(source, archive / name)
        tests = None
        if stage in ("task_tests", "audit"):
            tests = _task_test_snapshot(catalog, root, receipt, tid)
            command = [sys.executable, "-m", "pytest", "--import-mode=importlib", *tests, "-q",
                       "--junitxml=checks/task_tests.xml"]
        elif full_battery:
            command = ["bash", "scripts/run_generator_battery.sh", tid, phase, "--resume" if resume else "--fresh", "--keep-going"]
        else:
            # The original battery owns the exact settings and advisory rules.
            command = ["bash", "scripts/run_generator_battery.sh", tid, phase, stage, "--fresh"]
        execution_timeouts = None
        if stage not in ('task_tests', 'audit'):
            execution_timeouts = _native_execution_timeouts(timeout)
            command.extend(['--time-budget', format(execution_timeouts['native_budget_seconds'], '.12g')])
        if require_rotations_identifiable and stage != "audit":
            command.append("--require-rotations-identifiable")
        if schedule_census is not None and stage != 'audit':
            command.extend(['--schedule-census', 'checks/schedule-census-input.json',
                            '--schedule-seed', str(schedule_seed)])
        if enumerate_schedule_period and stage != 'audit':
            command.extend(['--enumerate-schedule-period', '--schedule-seed', str(schedule_seed)])
        if compact_results:
            command.append("--compact-results")
        if full_results:
            command.append("--full-results")
        result = {"schema": "arcpuzzles-check-v1", "task_id": tid,
                  "stage": "battery" if full_battery else stage, "phase": phase,
                  "passed": None, "status": "running", "command": command,
                  "settings": settings, "resumed": resume, "invalidated_stages": invalidated,
                  "runtime_manifest": receipt, "runtime_path": str(root), "battery_summary": None}
        if execution_timeouts is not None:
            result['execution_timeouts'] = execution_timeouts
        result['controller'] = _process_identity(os.getpid())
        if full_battery and output is not None:
            # The retained schedule input survives deletion/movement of the
            # original input. All policy flags remain bound by resume checks.
            environment = ['PYTHONPATH=' + str(Path(__file__).resolve().parent.parent),
                           'RACKET_PATH=' + settings['racket_path']]
            # Several inherited gates resolve the standard executable name
            # through PATH, even when runner uses explicit RACKET_PATH. Keep
            # the original PATH and its selected executable directory so a
            # copied argv can resume from a different caller environment.
            racket = shutil.which(settings['racket_path'])
            inherited_path = os.environ.get('PATH', os.defpath)
            if racket:
                inherited_path = os.pathsep.join(filter(None, (
                    str(Path(racket).absolute().parent), inherited_path)))
            environment.append('PATH=' + inherited_path)
            for name, value in (('PYTHONHASHSEED', settings['pythonhashseed']), ('SYNC_PATCH', settings['sync_patch'])):
                if value is not None and value != '':
                    environment.append(name + '=' + value)
            argv = ['env', *environment, sys.executable, '-m', 'arcpuzzles', '--library', str(catalog.root.resolve()),
                    'check', tid, '--battery', '--resume', '--phase', phase,
                    '--timeout', str(timeout), '--out', str(output.resolve())]
            for enabled, flag in ((require_rotations_identifiable, '--require-rotations-identifiable'),
                                  (compact_results, '--compact-results'), (full_results, '--full-results')):
                if enabled:
                    argv.append(flag)
            if schedule_census is not None:
                argv.extend(['--schedule-census', str(output.resolve() / 'checks/schedule-census-input.json'),
                             '--schedule-seed', str(schedule_seed)])
            if enumerate_schedule_period:
                argv.extend(['--enumerate-schedule-period', '--schedule-seed', str(schedule_seed)])
            result['resume_argv'] = argv
        def started(identity):
            result['child_process'] = identity
            if output is not None:
                _save_check_checkpoint(root, output, result)
        if prerequisites is not None:
            result.update(test_prerequisite_preflight=prerequisites, test_interpreter=sys.executable)
        options = {'on_start': started}
        if on_output is not None:
            options['on_output'] = on_output
        extra_env = {}
        if tests is not None:
            extra_env.update(PYTHONPATH=os.pathsep.join((str(root / "src"), str(root))), ARCPUZZLES_HOME=str(root))
            result['test_import_diagnostics'] = _task_test_import_diagnostics(root, tests)
            if on_output is not None:
                for diagnostic in result['test_import_diagnostics']:
                    on_output(f"{diagnostic['path']}:{diagnostic['line']}: {diagnostic['message']}\n")
        if output is not None:
            output = output.resolve()
            output.mkdir(parents=True, exist_ok=resume)
            (output / "RUNTIME_MANIFEST.json").write_text(json.dumps(receipt, indent=2) + "\n")
            # Print evidence paths where the caller will find them, not in this temporary runtime.
            extra_env["BATTERY_DISPLAY_ROOT"] = f"{output}/"
            _save_check_checkpoint(root, output, result)
            def progress(chunk: str) -> None:
                _save_check_checkpoint(root, output, result)
                with (output / "progress.log").open("a") as stream:
                    stream.write(chunk)
                if on_output is not None:
                    on_output(chunk)
            options["on_output"] = progress
        if extra_env:
            options["extra_env"] = extra_env
        preflight_errors = [d for d in result.get('test_import_diagnostics', []) if d['severity'] == 'error']
        try:
            run = (_run_audit(root, result, tests, preflight_errors, timeout, options, output)
                   if stage == "audit" else
                   {'command': command, 'exit_code': 2, 'timed_out': False, 'stdout': '',
                    'stderr': 'Task-test preflight failed before pytest:\n' + '\n'.join(
                        f"{d['path']}:{d['line']}: {d['message']}" for d in preflight_errors)}
                   if preflight_errors else
                   run_process(command, root, timeout=timeout, **options) if tests != [] else
                   {"command": command, "exit_code": 5, "timed_out": False,
                    "stdout": "No task-local or selected frozen tests found.\n", "stderr": ""})
        except BaseException as exc:
            result.update(status="interrupted", interruption=type(exc).__name__)
            result['interruption_signal'] = getattr(exc, 'signum', None)
            result['child_cleanup'] = getattr(exc, 'child_cleanup', {'session_empty': False})
            for outcome in result.get('audit_stages', {}).values():
                if outcome['status'] == 'running':
                    outcome.update(status='interrupted', passed=None)
            _write_audit_summary(root, result)
            if output is not None:
                _save_check_checkpoint(root, output, result)
            exc.check_result = result
            raise
        result.update(run, status=run.get("status", "completed"),
                      passed=run.get("passed", run["exit_code"] == 0 and not run["timed_out"]))
        if tests is not None and stage != "audit":
            result.update(test_paths=tests, test_status="preflight_failed" if preflight_errors else "no_tests" if run["exit_code"] == 5 else "executed")
            result['test_counts'] = _task_test_counts(root / 'checks/task_tests.xml')
            if run['exit_code'] != 0 and 'No module named pytest' in run.get('stderr', ''):
                result.update(test_status='dependency_missing', missing_dependency='pytest',
                              test_interpreter=sys.executable)
        summary = root / f"checks/{tid}_{phase}_battery_summary.json"
        result["battery_summary"] = json.loads(summary.read_text()) if summary.is_file() else None
        native_summary = result['battery_summary'] or {}
        if native_summary.get('budget_exhausted') or any(
                row.get('timed_out') for row in native_summary.get('stages', {}).values()):
            result['timed_out'] = True
            result['passed'] = False
        _write_audit_summary(root, result)
        if output is not None:
            _save_check_checkpoint(root, output, result)
        return result
