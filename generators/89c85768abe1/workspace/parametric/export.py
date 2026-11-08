#!/usr/bin/env python3
"""Private-controller export and protected verification for this rule family.

Serve only a hash-named ``turns/`` file to a sequential solver. ``public/`` and
``public.jsonl`` are controller-side bulk challenges containing all query inputs.
Programs, settings, answers, counts, certificates, and turn mappings stay private.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "89c85768abe1"
MODES = ("all", "largest_component")
SCHEMA = "arcpuzzles-89c85768abe1-parametric-export-v1"
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _keys(value, names, name):
    if type(value) is not dict or set(value) != set(names):
        raise ValueError(f"Invalid {name} fields")


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_rectangle_export_adapter_" + _sha(str(path).encode())
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Task-local adapter is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def _runtime():
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            yield apply, identity
        finally:
            bridge.close()


def _public(episode):
    return {"train": [{"input": _grid(pair["input"]), "output": _grid(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": _grid(pair["input"])} for pair in episode["test"]]}


def _turn(episode, index):
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return _public({"train": episode["train"], "test": [episode["test"][index]]})


def _normalize_episode(episode, demos, queries, program):
    if type(episode) is not dict or episode.get("program_solution") != program:
        raise ValueError("Episode program_solution differs from the selected program")
    result = {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = episode.get(split)
        if type(pairs) is not list or len(pairs) != count:
            raise ValueError(f"Episode {split} count differs from the request")
        result[split] = []
        for pair in pairs:
            _keys(pair, ("input", "output"), split + " pair")
            result[split].append({"input": _grid(pair["input"]), "output": _grid(pair["output"])})
    inputs = [_raw(pair["input"]) for split in result.values() for pair in split]
    if len(set(inputs)) != len(inputs):
        raise ValueError("Duplicate input within an episode")
    return {**result, "program_solution": program}


def _program(adapter, settings):
    value = adapter.program(settings)
    if type(value) is not str or not value.strip() or len(value.encode()) > 100000:
        raise ValueError("Selected program must be bounded, nonempty Racket text")
    return value


def _labels(apply, episode, program):
    count = 0
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            if _grid(apply(program, pair["input"])) != pair["output"]:
                raise ValueError(f"Protected Racket label mismatch at {split}[{index}]")
            count += 1
    return count


def _teaching(adapter, episode, settings):
    report = adapter.teaching_report(episode, settings)
    if type(report) is not dict or report.get("accepted") is not True:
        raise ValueError("Episode failed the declared teaching check: " + str(report))
    _raw(report)
    return report


def export(output, *, seeds=None, demos=3, queries=4, modes=None):
    """Preflight every episode, execute labels, then publish with manifest last."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    _integer(demos, 1, 32, "demos")
    _integer(queries, 1, 32, "queries")
    seeds = [0, 17] if seeds is None else seeds
    modes = list(MODES) if modes is None else modes
    if not isinstance(seeds, (list, tuple)) or not seeds:
        raise ValueError("seeds must be a nonempty list")
    if not isinstance(modes, (list, tuple)) or not modes:
        raise ValueError("modes must be a nonempty list")
    for seed in seeds:
        _integer(seed, 0, 2**63 - 1, "seed")
    if any(type(mode) is not str or mode not in MODES for mode in modes):
        raise ValueError("Unknown mode")
    if len(set(seeds)) != len(seeds) or len(set(modes)) != len(modes):
        raise ValueError("Duplicate export request")
    adapter = _load_adapter()
    planned, turns, identifiers = [], {}, set()
    with _runtime() as (apply, identity):
        for mode in modes:
            for seed in seeds:
                settings = {"mode": mode}
                program = _program(adapter, settings)
                generated = adapter.generate(seed, settings, demos, queries)
                episode = _normalize_episode(generated, demos, queries, program)
                _labels(apply, episode, program)
                teaching = _teaching(adapter, episode, settings)
                visible = _public(episode)
                payload = _raw(visible)
                if _raw(adapter.public_challenge(generated)) != payload:
                    raise ValueError("Adapter public projection exposes private data or differs")
                identifier = _sha(payload)
                if identifier in identifiers:
                    raise ValueError("Duplicate visible challenge before publication")
                identifiers.add(identifier)
                mappings = []
                for index in range(queries):
                    turn_payload = _raw(_turn(episode, index))
                    if _raw(adapter.visible_turn(generated, index)) != turn_payload:
                        raise ValueError("Adapter turn projection exposes private or future data")
                    turn_id = _sha(turn_payload)
                    turns[turn_id] = turn_payload
                    mappings.append({"query_index": index, "turn_id": turn_id})
                private = {"episode_id": identifier, "task_id": TASK_ID, "seed": seed,
                           "settings": settings, "counts": {"demos": demos, "queries": queries},
                           "program": program, "train": episode["train"], "test": episode["test"],
                           "racket": identity, "teaching": teaching, "turns": mappings}
                planned.append((identifier, payload, {"episode_id": identifier, **visible}, private))
    planned.sort(key=lambda row: row[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".rectangle-export-", dir=output.parent) as directory:
        stage = Path(directory)
        (stage / "public").mkdir()
        (stage / "turns").mkdir()
        for identifier, payload, _, _ in planned:
            (stage / "public" / (identifier + ".json")).write_bytes(payload)
        for identifier, payload in sorted(turns.items()):
            (stage / "turns" / (identifier + ".json")).write_bytes(payload)
        (stage / "public.jsonl").write_bytes(b"".join(_raw(row[2]) for row in planned))
        (stage / "private.jsonl").write_bytes(b"".join(_raw(row[3]) for row in planned))
        manifest = {"schema": SCHEMA, "status": "complete", "task_id": TASK_ID,
                    "episodes": len(planned), "counts": {"demos": demos, "queries": queries},
                    "dataset_id": _sha(_raw([row[0] for row in planned])),
                    "training_admitted": False, "files": [
                        {"path": path.relative_to(stage).as_posix(), "bytes": path.stat().st_size,
                         "sha256": _sha(path.read_bytes())}
                        for path in sorted(stage.rglob("*"),
                                           key=lambda item: item.relative_to(stage).as_posix())
                        if path.is_file()]}
        (stage / "manifest.json").write_bytes(_raw(manifest))
        output.mkdir(exist_ok=False)
        for name in ("public", "turns", "public.jsonl", "private.jsonl", "manifest.json"):
            os.replace(stage / name, output / name)
    return verify(output)


def _json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def forbidden(value):
        raise ValueError("Nonfinite JSON number: " + value)
    return json.loads(data, object_pairs_hook=unique, parse_constant=forbidden)


def _jsonl(path):
    result = []
    for line in path.read_bytes().splitlines(keepends=True):
        value = _json(line)
        if _raw(value) != line:
            raise ValueError("JSONL row must use exact canonical bytes")
        result.append(value)
    return result


def _inventory(output):
    if output.is_symlink() or not output.is_dir():
        raise ValueError("Export must be a regular directory")
    actual = set()
    for path in output.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlinks are forbidden in an export")
        name = path.relative_to(output).as_posix()
        if path.is_file():
            actual.add(name)
        elif not path.is_dir() or name not in {"public", "turns"}:
            raise ValueError("Unexpected export directory or special file")
    manifest = _json((output / "manifest.json").read_bytes())
    _keys(manifest, ("schema", "status", "task_id", "episodes", "counts", "dataset_id",
                     "training_admitted", "files"), "manifest")
    if (manifest["schema"] != SCHEMA or manifest["status"] != "complete"
            or manifest["task_id"] != TASK_ID or manifest["training_admitted"] is not False):
        raise ValueError("Invalid or incomplete export manifest")
    _integer(manifest["episodes"], 1, 2**63 - 1, "episode count")
    _keys(manifest["counts"], ("demos", "queries"), "manifest counts")
    for name in ("demos", "queries"):
        _integer(manifest["counts"][name], 1, 32, name)
    if type(manifest["files"]) is not list:
        raise ValueError("Invalid manifest inventory")
    names = []
    for row in manifest["files"]:
        _keys(row, ("path", "bytes", "sha256"), "inventory row")
        name = row["path"]
        if (type(name) is not str or "\\" in name or ".." in PurePosixPath(name).parts
                or not re.fullmatch(r"(?:public\.jsonl|private\.jsonl|(?:public|turns)/[0-9a-f]{64}\.json)", name)):
            raise ValueError("Unsafe or unexpected export path")
        _integer(row["bytes"], 0, 2**63 - 1, "file bytes")
        payload = (output / name).read_bytes()
        if len(payload) != row["bytes"] or _sha(payload) != row["sha256"]:
            raise ValueError("Export file hash or size mismatch: " + name)
        names.append(name)
    if names != sorted(set(names)) or set(names) != actual - {"manifest.json"}:
        raise ValueError("Export inventory is duplicated, incomplete, or out of order")
    if not {"public.jsonl", "private.jsonl"} <= set(names):
        raise ValueError("Export JSONL files are missing")
    return manifest, set(names)


def verify(output):
    """Validate exact visible bytes, all projections, teaching, and Racket labels."""
    output = Path(output)
    manifest, inventory = _inventory(output)
    public = _jsonl(output / "public.jsonl")
    private = _jsonl(output / "private.jsonl")
    if len(public) != manifest["episodes"] or len(private) != len(public):
        raise ValueError("Export episode counts differ")
    for row in public:
        _keys(row, ("episode_id", "train", "test"), "public row")
    ids = [row["episode_id"] for row in public]
    if (any(type(identifier) is not str or not re.fullmatch("[0-9a-f]{64}", identifier) for identifier in ids)
            or ids != sorted(set(ids)) or manifest["dataset_id"] != _sha(_raw(ids))):
        raise ValueError("Public IDs or dataset identity differ")
    expected_files = {"public.jsonl", "private.jsonl"}
    requests, normalized, turn_ids = set(), [], set()
    adapter = _load_adapter()
    for visible, hidden in zip(public, private):
        _keys(hidden, ("episode_id", "task_id", "seed", "settings", "counts", "program",
                       "train", "test", "racket", "teaching", "turns"), "private row")
        if hidden["episode_id"] != visible["episode_id"] or hidden["task_id"] != TASK_ID:
            raise ValueError("Export public/private IDs differ")
        _integer(hidden["seed"], 0, 2**63 - 1, "private seed")
        _keys(hidden["settings"], ("mode",), "private settings")
        if type(hidden["settings"]["mode"]) is not str or hidden["settings"]["mode"] not in MODES:
            raise ValueError("Invalid private mode")
        request = (hidden["seed"], hidden["settings"]["mode"])
        if request in requests:
            raise ValueError("Duplicate private export request")
        requests.add(request)
        if _raw(hidden["counts"]) != _raw(manifest["counts"]):
            raise ValueError("Private counts differ from manifest")
        program = _program(adapter, hidden["settings"])
        if hidden["program"] != program:
            raise ValueError("Private program differs from the selected current adapter program")
        episode = _normalize_episode({"train": hidden["train"], "test": hidden["test"],
                                      "program_solution": hidden["program"]},
                                     manifest["counts"]["demos"], manifest["counts"]["queries"], program)
        payload = _raw(_public(episode))
        identifier = _sha(payload)
        public_path = "public/" + identifier + ".json"
        if (identifier != visible["episode_id"]
                or _raw({"episode_id": identifier, **_public(episode)}) != _raw(visible)
                or (output / public_path).read_bytes() != payload):
            raise ValueError("Public masked projection, identifier, or exact bytes differ")
        expected_files.add(public_path)
        mappings = hidden["turns"]
        if type(mappings) is not list or len(mappings) != manifest["counts"]["queries"]:
            raise ValueError("Private turn mapping count differs")
        for index, mapping in enumerate(mappings):
            _keys(mapping, ("query_index", "turn_id"), "turn mapping")
            if type(mapping["query_index"]) is not int or mapping["query_index"] != index:
                raise ValueError("Private turn order differs")
            turn_payload = _raw(_turn(episode, index))
            turn_id = _sha(turn_payload)
            turn_path = "turns/" + turn_id + ".json"
            if mapping["turn_id"] != turn_id or (output / turn_path).read_bytes() != turn_payload:
                raise ValueError("Turn visible prefix, private mapping, or exact bytes differ")
            expected_files.add(turn_path)
            turn_ids.add(turn_id)
        normalized.append((hidden, episode, program))
    if inventory != expected_files:
        raise ValueError("Export contains missing or unreferenced visible files")
    label_count = 0
    with _runtime() as (apply, identity):
        for hidden, episode, program in normalized:
            if _raw(hidden["racket"]) != _raw(identity):
                raise ValueError("Recorded protected Racket identity differs from this runtime")
            label_count += _labels(apply, episode, program)
            if _raw(_teaching(adapter, episode, hidden["settings"])) != _raw(hidden["teaching"]):
                raise ValueError("Saved teaching report differs from replay")
    return {"schema": SCHEMA + "-verification", "status": "verified", "task_id": TASK_ID,
            "episodes": len(private), "turns": len(turn_ids), "racket_labels": label_count,
            "racket": identity, "training_admitted": False, "output": str(output.resolve())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--out", type=Path)
    action.add_argument("--verify", type=Path)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--mode", choices=MODES, action="append")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    try:
        result = verify(args.verify) if args.verify is not None else export(
            args.out, seeds=args.seed, modes=args.mode, demos=args.demos, queries=args.queries)
    except (ValueError, OSError, RuntimeError, TypeError) as error:
        print(json.dumps({"status": "error", "error": type(error).__name__, "message": str(error)}),
              file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
