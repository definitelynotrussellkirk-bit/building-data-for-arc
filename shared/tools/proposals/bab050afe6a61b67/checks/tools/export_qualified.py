#!/usr/bin/env python3
"""Project source-bound native qualification evidence into single-query turns.

Run through the packet launcher, for example (paths after python are relative
to WORK/repo):

  python3 ../checks/tools/export_qualified.py \
    --qualification ../checks/TASK/qualification/qualification.json \
    --task-id TASK --out ../checks/TASK/qualified-export --seed 17

Only actor/<sha256>.json is actor-visible, one current file at a time. The
manifest, directory inventory, controllers, answers, future query inputs,
settings, seeds, source identities and programs all remain controller-private.

This is external reviewer evidence tooling. Neither adapter may import it.
It does not import a generator/adapter, evaluate a program, accept a family or
admit training data. Hashes bind reported evidence; they do not authenticate a
reviewer's execution claim. Owner acceptance must replay native qualification.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys


SCHEMA = "arc-qualified-single-query-export-v1"
CONTROLLER_SCHEMA = "arc-qualified-single-query-controller-v1"
STATUS = "qualified_owner_acceptance_pending"
EXECUTORS = ("parametric_promotion.py", "parametric_worker.py", "catalog.py",
             "runtime.py", "parametric_priority.py")


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _object(value, name, keys=None):
    if type(value) is not dict or (keys is not None and set(value) != set(keys)):
        raise ValueError(f"Invalid {name} object or keys")
    return value


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("Grids require rectangular 1..30 dimensions and exact integer colors 0..9")


def _normalized(path):
    path = Path(path).absolute()
    # Check the supplied traversal before removing '..': link/../file must not
    # hide a symlink, while ordinary repo/../checks paths are supported.
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError(f"Path must not contain symlinks: {path}")
    path = Path(os.path.abspath(path))
    if path.resolve() != path:
        raise ValueError(f"Path must not resolve through symlinks: {path}")
    return path


def _local(path, within, *, file=True):
    path = _normalized(path)
    if (not path.is_relative_to(within)
            or (file and not path.is_file())):
        raise ValueError(f"Path must be a regular local path without symlinks: {path}")
    return path


def _json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def constant(value):
        raise ValueError(f"Non-finite JSON value: {value}")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def _module(name, path, *, package=False):
    spec = importlib.util.spec_from_file_location(
        name, path, submodule_search_locations=[str(path.parent)] if package else None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def _packet_modules(root):
    """Use isolated package names; never borrow modules from another checkout."""
    token = _hash(str(root).encode())[:20]
    native_name = "_arc_export_native_" + token
    runtime_name = "_arc_export_runtime_" + token
    support_name = "_arc_export_support_" + token
    names = (native_name, runtime_name, support_name)
    if any(name in sys.modules for name in names):
        raise ValueError("An export from this root is already active")
    before = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        for filename in ("__init__.py", *EXECUTORS):
            _local(root / "src/arcpuzzles" / filename, root)
        _module(native_name, root / "src/arcpuzzles/__init__.py", package=True)
        promotion = importlib.import_module(native_name + ".parametric_promotion")
        catalog = importlib.import_module(native_name + ".catalog")
        runtime = root / "shared/runtime"
        for filename in ("arc_repl/__init__.py", "arc_repl/racket_bridge.py",
                         "arc_repl/security.py", "arc_repl/parser.py", "reviewer_support.py"):
            _local(runtime / filename, root)
        _module(runtime_name, runtime / "arc_repl/__init__.py", package=True)
        bridge = importlib.import_module(runtime_name + ".racket_bridge")
        security = importlib.import_module(runtime_name + ".security")
        support = _module(support_name, runtime / "reviewer_support.py")
        yield promotion, catalog.Catalog, bridge, security, support
    finally:
        for name in list(sys.modules):
            if any(name == prefix or name.startswith(prefix + ".") for prefix in names):
                del sys.modules[name]
        sys.dont_write_bytecode = before


def _runtime_identity(root, binary, bridge, security):
    runtime = root / "shared/runtime/arc_repl"
    return {
        "schema": "arc-protected-racket-runtime-v1", "backend": "racket", "protected": True,
        "binary_sha256": _hash(_local(binary, root.parent).read_bytes()),
        "bridge_sha256": _hash(_local(runtime / "racket_bridge.py", root).read_bytes()),
        "prelude_sha256": _hash(_local(runtime / "racket_prelude/arc-prelude.rkt", root).read_bytes()),
        "boot_script_sha256": _hash(bridge._BOOT_SCRIPT.encode()),
        "candidate_symbol_policy_sha256": security.policy_sha256(),
    }


def _validate_evidence(q, execution, *, task_id, contract, binding, promotion, identity):
    if (_raw(q.get("contract")) != _raw(contract)
            or _raw(q.get("source_binding")) != _raw(binding)):
        raise ValueError("Qualification differs from current native source binding or contract")
    _object(execution, "execution", {"episodes", "checks", "racket", "racket_evaluations"})
    if _raw(execution["racket"]) != _raw(identity):
        raise ValueError("Protected Racket execution identity differs from current packet runtime")
    space = promotion.settings_space(contract)
    settings_keys = {_raw(setting) for setting in space}
    jobs = q.get("jobs")
    if type(jobs) is not list or not 1 <= len(jobs) <= 128:
        raise ValueError("Qualification requires a bounded nonempty job list")
    episodes, checks = execution["episodes"], execution["checks"]
    if (type(episodes) is not list or type(checks) is not list
            or len(episodes) != len(jobs) or len(checks) != len(jobs)):
        raise ValueError("Execution episodes and checks must match every qualification job")
    coverage, evaluations = {}, 0
    for job, episode, check in zip(jobs, episodes, checks):
        _object(job, "job", {"seed", "settings", "demos", "queries"})
        seed = _integer(job["seed"], 0, 2**63 - 1, "job seed")
        demos = _integer(job["demos"], 2, 6, "job demonstrations")
        queries = _integer(job["queries"], 4, 32, "qualification queries")
        for key, number in (("demos", demos), ("queries", queries)):
            _integer(number, *contract["limits"][key], "contract " + key)
        setting = _raw(job["settings"])
        if setting not in settings_keys:
            raise ValueError("Job setting is not a typed declared setting")
        seen = coverage.setdefault(setting, set())
        if seed in seen:
            raise ValueError("Duplicate qualification job seed within a setting")
        seen.add(seed)
        _object(episode, "episode", {"task_id", "seed", "settings", "train", "test",
                                     "program", "program_sha256", "reference"})
        _object(check, "check", {"settings", "seed", "counts", "survivors", "label_count"})
        _integer(episode["seed"], 0, 2**63 - 1, "episode seed")
        _integer(check["seed"], 0, 2**63 - 1, "check seed")
        _integer(check["label_count"], 1, 64, "check label count")
        _object(check["counts"], "check counts", {"demos", "queries"})
        _integer(check["counts"]["demos"], 2, 6, "check demonstrations")
        _integer(check["counts"]["queries"], 4, 32, "check queries")
        if (episode["task_id"] != task_id or episode["seed"] != seed or check["seed"] != seed
                or _raw(episode["settings"]) != setting or _raw(check["settings"]) != setting
                or check["counts"] != {"demos": demos, "queries": queries}
                or check["label_count"] != demos + queries
                or _raw(check["survivors"]) != _raw([job["settings"]])
                or episode["reference"] != "accepted_parametric"):
            raise ValueError("Execution identity or demonstration certificate differs from its job")
        inputs = []
        for split, count in (("train", demos), ("test", queries)):
            pairs = episode[split]
            if type(pairs) is not list or len(pairs) != count:
                raise ValueError("Labeled pair counts differ from the qualification request")
            for pair in pairs:
                _object(pair, "labeled pair", {"input", "output"})
                _grid(pair["input"])
                _grid(pair["output"])
                inputs.append(_raw(pair["input"]))
        if len(inputs) != len(set(inputs)):
            raise ValueError("Demonstration and query inputs must be distinct")
        evaluations += len(space) * demos + queries
    if set(coverage) != settings_keys or any(not 2 <= len(seeds) <= 8 for seeds in coverage.values()):
        raise ValueError("Qualification must cover every setting with two to eight distinct seeds")
    _integer(execution["racket_evaluations"], 1, 131072, "Racket evaluation count")
    if execution["racket_evaluations"] != evaluations:
        raise ValueError("Racket evaluation count differs from native worker evaluation scope")
    programs = promotion._check_execution(execution, jobs, binding, contract)
    if (_raw(programs) != _raw(q.get("programs"))
            or set(programs) != {key.decode().strip() for key in settings_keys}):
        raise ValueError("Qualification program inventory differs from labeled execution")
    return coverage


def _public_bytes(support, train, query):
    challenge = {"train": train, "test": [{"input": query["input"]}]}
    data = support.public_challenge_bytes(challenge)
    public = _json(data)
    _object(public, "public turn", {"train", "test"})
    if (len(public["test"]) != 1 or set(public["test"][0]) != {"input"}
            or any(set(pair) != {"input", "output"} for pair in public["train"])
            or data != _raw(public)):
        raise ValueError("Public helper did not emit strict canonical single-query bytes")
    public_id = support.public_challenge_id(challenge)
    if public_id != _hash(data):
        raise ValueError("Public helper content ID differs from the exact visible bytes")
    return public_id, data


def _write_exclusive(path, data):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def export_qualified(qualification, output, *, root, task_id, queries=4,
                     seeds=None, racket_binary=None):
    """Export recorded labels only; return the private manifest committed last."""
    root = _normalized(root)
    if not root.is_dir():
        raise ValueError("Explicit repository root must be a local directory without symlinks")
    workspace = root.parent
    qualification = _local(qualification, workspace)
    if qualification.name != "qualification.json":
        raise ValueError("Use an explicit native qualification.json and its sibling execution.json")
    execution_path = _local(qualification.with_name("execution.json"), workspace)
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output = _local(output, workspace, file=False)
    if type(task_id) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", task_id) is None:
        raise ValueError("Use an exact task ID")
    _integer(queries, 1, 4, "controller queries")
    if seeds is not None:
        if type(seeds) is not list or not 1 <= len(seeds) <= 8:
            raise ValueError("Seed selection must be a nonempty list of up to eight qualified seeds")
        for seed in seeds:
            _integer(seed, 0, 2**63 - 1, "selected seed")
        if len(set(seeds)) != len(seeds):
            raise ValueError("Selected seeds must be distinct")
    binary = racket_binary if racket_binary is not None else os.environ.get("RACKET_PATH")
    if not binary:
        raise ValueError("Use the packet launcher or pass its explicit --racket-binary")
    binary = _local(binary, workspace)
    q_bytes, execution_bytes = qualification.read_bytes(), execution_path.read_bytes()
    q, execution = _object(_json(q_bytes), "qualification"), _json(execution_bytes)
    if (q.get("schema") != "arcpuzzles-parametric-qualification-v1"
            or q.get("status") != "qualified" or q.get("task_id") != task_id
            or q.get("training_admitted") is not False
            or q.get("owner_acceptance_reexecuted", False) is not False):
        raise ValueError("Expected an owner-pending native qualification for the exact task")
    source = _object(q.get("execution"), "execution source", {"path", "sha256"})
    if source["path"] != "execution.json" or source["sha256"] != _hash(execution_bytes):
        raise ValueError("Sibling execution bytes differ from qualification hash")
    with _packet_modules(root) as (promotion, Catalog, bridge, security, support):
        contract, binding = promotion._ready(Catalog(root), task_id)
        identity = _runtime_identity(root, binary, bridge, security)
        coverage = _validate_evidence(q, execution, task_id=task_id, contract=contract,
                                      binding=binding, promotion=promotion, identity=identity)
        if seeds is not None and any(not set(seeds) <= available for available in coverage.values()):
            raise ValueError("Selected seeds must be qualified for every declared setting")
        selected = [e for e in execution["episodes"] if seeds is None or e["seed"] in seeds]
        actors, controllers = {}, {}
        for episode in selected:
            if queries > len(episode["test"]):
                raise ValueError("Requested controller queries exceed recorded labeled queries")
            turns = []
            for index, query in enumerate(episode["test"][:queries]):
                public_id, data = _public_bytes(support, episode["train"], query)
                actor_path = f"actor/{public_id}.json"
                if actor_path in actors and actors[actor_path] != data:
                    raise ValueError("Public content ID collision")
                actors[actor_path] = data
                turns.append({"turn_index": index, "actor_path": actor_path, "public_id": public_id,
                              "input": query["input"], "output": query["output"]})
            controller = {
                "schema": CONTROLLER_SCHEMA, "status": STATUS, "accepted": False,
                "training_admitted": False, "task_id": task_id, "seed": episode["seed"],
                "settings": episode["settings"], "program": episode["program"],
                "program_sha256": episode["program_sha256"], "train": episode["train"],
                "queries": turns, "qualification_sha256": _hash(q_bytes),
                "execution_sha256": _hash(execution_bytes),
            }
            data = _raw(controller)
            controllers[f"private/controllers/{_hash(data)}.json"] = data
        files = {**actors, **controllers}
        manifest = {
            "schema": SCHEMA, "status": STATUS, "accepted": False, "training_admitted": False,
            "owner_acceptance": "pending", "task_id": task_id,
            "qualification_path": qualification.relative_to(workspace).as_posix(),
            "qualification_sha256": _hash(q_bytes), "execution_sha256": _hash(execution_bytes),
            "source_binding_sha256": _hash(_raw(binding)), "racket": identity,
            "controller_count": len(controllers), "controller_queries": queries,
            "actor_file_count": len(actors), "seeds": sorted({e["seed"] for e in selected}),
            "demos": sorted({len(e["train"]) for e in selected}),
            "files": [{"path": path, "sha256": _hash(data)} for path, data in sorted(files.items())],
            "exporter_sha256": _hash(Path(__file__).read_bytes()),
            "actor_boundary": "Expose only the current actor/<sha256>.json file; keep all other files and directory inventories private.",
            "evidence_scope": "Source-bound reported native qualification; no replay, owner acceptance, universal identifiability or training admission.",
        }

        def unchanged():
            if (qualification.read_bytes() != q_bytes or execution_path.read_bytes() != execution_bytes
                    or _raw(promotion._ready(Catalog(root), task_id)) != _raw((contract, binding))
                    or _runtime_identity(root, binary, bridge, security) != identity):
                raise ValueError("Qualification evidence or current source/runtime changed during export")

        unchanged()
        output.mkdir(parents=True, exist_ok=False, mode=0o700)
        (output / "actor").mkdir(mode=0o700)
        (output / "private").mkdir(mode=0o700)
        (output / "private/controllers").mkdir(mode=0o700)
        for path, data in sorted(files.items()):
            _write_exclusive(output / path, data)
        # Re-read payloads before publishing the completion marker. An I/O error
        # or stale source leaves an incomplete directory with no manifest.
        for path, data in files.items():
            if (output / path).read_bytes() != data:
                raise ValueError("Export payload changed before manifest commit")
        unchanged()
        _write_exclusive(output / "manifest.json", _raw(manifest))
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2] / "repo")
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--queries", type=int, default=4, help="One to four private controller queries; default four")
    parser.add_argument("--seed", type=int, action="append", dest="seeds", help="Select an already-qualified seed; repeatable")
    parser.add_argument("--racket-binary", type=Path, help="Packet binary to hash; defaults to launcher RACKET_PATH")
    args = parser.parse_args(argv)
    try:
        report = export_qualified(args.qualification, args.out, root=args.root, task_id=args.task_id,
                                   queries=args.queries, seeds=args.seeds, racket_binary=args.racket_binary)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps({"manifest": str((args.out / "manifest.json").resolve()),
                      "status": report["status"], "controller_count": report["controller_count"],
                      "controller_queries": report["controller_queries"],
                      "actor_file_count": report["actor_file_count"], "training_admitted": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
