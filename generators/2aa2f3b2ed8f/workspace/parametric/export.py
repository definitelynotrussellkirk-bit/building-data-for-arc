"""Checked, task-local proposal export with one public query per reveal.

Run ``export.py --out NEW_PATH --seed 17`` to check and export both settings.
Run ``export.py verify PATH`` to check serialized integrity without executing
Racket again. Give a consumer only the next hash-named file selected from the
private ``reveal_ids`` list; the public directory is a controller-side pool.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "2aa2f3b2ed8f"
SETTINGS = ({"mover": "body"}, {"mover": "target"})
CONTROLLER_SCHEMA = "arcpuzzles-proposed-parametric-controller-v1"
MANIFEST_SCHEMA = "arcpuzzles-proposed-parametric-export-v1"
REFERENCE = "proposed_parametric"

# Use only this checkout's existing protected evaluator and public-byte helpers.
_before_path = list(sys.path)
try:
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
    from arcpuzzles import parametric_worker as _worker
    import reviewer_support as _support
finally:
    sys.path[:] = _before_path
if (Path(_worker.__file__).resolve() != ROOT / "src/arcpuzzles/parametric_worker.py"
        or Path(_support.__file__).resolve() != ROOT / "shared/runtime/reviewer_support.py"):
    raise ImportError("Export helpers must come from this checkout")
evaluate_contract = _worker.evaluate_contract


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Nonfinite JSON number")

    try:
        return json.loads(path.read_bytes(), object_pairs_hook=unique, parse_constant=invalid)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read export JSON: {path.name}") from error


def public_turn(episode, query_index):
    """Return exactly the demonstrations and one query input, with no metadata."""
    if not isinstance(episode, dict) or type(episode.get("test")) is not list:
        raise ValueError("An episode needs a query list")
    _worker._integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    challenge = {"train": episode.get("train"), "test": [episode["test"][query_index]]}
    return json.loads(_support.public_challenge_bytes(challenge))


def _request(seed, demos, queries):
    return {
        "seed": _worker._integer(seed, 0, 2**63 - 1, "seed"),
        "demos": _worker._integer(demos, 2, 6, "demos"),
        "queries": _worker._integer(queries, 1, 4, "queries"),
    }


def _no_symlinks(path):
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("Export paths must not contain symlinks")


def _check_controller(controller):
    """Validate serialized structure/certificates, not reference semantics."""
    expected = {"schema", "task_id", "reference", "request", "episodes", "checks",
                "racket", "racket_evaluations"}
    if type(controller) is not dict or set(controller) != expected:
        raise ValueError("Invalid private controller fields")
    if (controller["schema"] != CONTROLLER_SCHEMA or controller["task_id"] != TASK_ID
            or controller["reference"] != REFERENCE):
        raise ValueError("Invalid proposal identity")
    request = controller["request"]
    if type(request) is not dict or set(request) != {"seed", "demos", "queries"}:
        raise ValueError("Invalid request fields")
    _request(**request)
    seed, demos, queries = request["seed"], request["demos"], request["queries"]
    episodes, checks = controller["episodes"], controller["checks"]
    if type(episodes) is not list or type(checks) is not list or len(episodes) != 2 or len(checks) != 2:
        raise ValueError("Both parameter settings require an episode and teaching check")
    runtime = controller["racket"]
    if (type(runtime) is not dict or runtime.get("backend") != "racket"
            or runtime.get("protected") is not True):
        raise ValueError("Export requires protected Racket execution evidence")
    expected_evaluations = 4 * demos + 2 * queries
    _worker._integer(controller["racket_evaluations"], expected_evaluations,
                     expected_evaluations, "racket_evaluations")
    visible_files = {}
    paired_inputs = None
    for episode, check, setting in zip(episodes, checks, SETTINGS):
        fields = {"task_id", "seed", "settings", "train", "test", "program",
                  "program_sha256", "reference", "reveal_ids"}
        if type(episode) is not dict or set(episode) != fields:
            raise ValueError("Invalid private episode fields")
        _worker._integer(episode["seed"], seed, seed, "episode seed")
        _worker._settings(episode["settings"], {"mover": [setting["mover"]]})
        if episode["task_id"] != TASK_ID or episode["reference"] != REFERENCE:
            raise ValueError("Invalid private episode identity")
        program = episode["program"]
        if (type(program) is not str or not program.strip()
                or hashlib.sha256(program.encode()).hexdigest() != episode["program_sha256"]):
            raise ValueError("Program hash mismatch")
        inputs = []
        for split, count in (("train", demos), ("test", queries)):
            pairs = episode[split]
            if type(pairs) is not list or len(pairs) != count:
                raise ValueError("Episode counts do not match request")
            for pair in pairs:
                if type(pair) is not dict or set(pair) != {"input", "output"}:
                    raise ValueError("Private pairs require input and output only")
                _worker._grid(pair["input"])
                _worker._grid(pair["output"])
                inputs.append(_raw(pair["input"]))
        if len(set(inputs)) != len(inputs):
            raise ValueError("Demonstration and query inputs must be distinct")
        if paired_inputs is not None and inputs != paired_inputs:
            raise ValueError("Both settings must use the same ordered inputs")
        paired_inputs = inputs
        check_fields = {"settings", "seed", "counts", "survivors", "label_count"}
        if type(check) is not dict or set(check) != check_fields:
            raise ValueError("Invalid demonstration-only teaching check")
        _worker._settings(check["settings"], {"mover": [setting["mover"]]})
        _worker._integer(check["seed"], seed, seed, "check seed")
        _worker._integer(check["label_count"], demos + queries, demos + queries, "label_count")
        if (type(check["counts"]) is not dict or set(check["counts"]) != {"demos", "queries"}
                or check["survivors"] != [setting]):
            raise ValueError("Invalid finite-rival teaching certificate")
        _worker._integer(check["counts"]["demos"], demos, demos, "checked demos")
        _worker._integer(check["counts"]["queries"], queries, queries, "checked queries")
        ids = episode["reveal_ids"]
        if type(ids) is not list or len(ids) != queries:
            raise ValueError("Invalid private reveal mapping")
        for index, visible_id in enumerate(ids):
            challenge = public_turn(episode, index)
            data = _support.public_challenge_bytes(challenge)
            if type(visible_id) is not str or visible_id != _support.public_challenge_id(challenge):
                raise ValueError("Public projection hash mismatch")
            relative = f"public/{visible_id}.json"
            if relative in visible_files:
                raise ValueError("Duplicate visible payload in export batch")
            visible_files[relative] = data
    return visible_files


def export_episodes(output, *, seed, demos=3, queries=4):
    """Execute both proposed rules through native Racket, then publish the batch."""
    request = _request(seed, demos, queries)
    output = Path(output).absolute()
    _no_symlinks(output)
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    contract = _read_json(HERE / "promotion.json")
    jobs = [{**request, "settings": deepcopy(setting)} for setting in SETTINGS]
    # The native worker loads the exact adjacent adapter from the contract,
    # checks canonical-source equality, executes every label, and fits rivals
    # to demonstrations only. No Python-label-only publishing path is exposed.
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    episodes = deepcopy(result["episodes"])
    for episode in episodes:
        episode["reference"] = REFERENCE
        episode["reveal_ids"] = [
            _support.public_challenge_id(public_turn(episode, index))
            for index in range(len(episode["test"]))]
    controller = {
        "schema": CONTROLLER_SCHEMA, "task_id": TASK_ID, "reference": REFERENCE,
        "request": request, "episodes": episodes, "checks": result["checks"],
        "racket": result["racket"], "racket_evaluations": result["racket_evaluations"],
    }
    files = _check_controller(controller)
    files["private/controller.json"] = _raw(controller)
    manifest = {
        "schema": MANIFEST_SCHEMA, "task_id": TASK_ID,
        "files": [{"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                  for name, data in sorted(files.items())],
    }
    # All execution, shape validation and duplicate checks precede creation.
    output.mkdir(parents=True, exist_ok=False)
    (output / "private").mkdir()
    (output / "public").mkdir()
    for name, data in sorted(files.items()):
        (output / name).write_bytes(data)
    # A missing manifest denotes incomplete publication.
    (output / "private/manifest.json").write_bytes(_raw(manifest))
    return verify_export(output)


def verify_export(output):
    """Check byte hashes, strict grids, counts and projection; no Racket replay.

    This detects corruption relative to the manifest and internal inconsistency.
    An editable bundle is not signed authority: coherently rewriting labels and
    their hashes requires a fresh native export to establish semantic validity.
    """
    output = Path(output).absolute()
    _no_symlinks(output)
    if not output.is_dir():
        raise ValueError("Export directory is missing")
    _no_symlinks(output / "private/manifest.json")
    manifest = _read_json(output / "private/manifest.json")
    if (type(manifest) is not dict or set(manifest) != {"schema", "task_id", "files"}
            or manifest["schema"] != MANIFEST_SCHEMA or manifest["task_id"] != TASK_ID
            or type(manifest["files"]) is not list):
        raise ValueError("Invalid export manifest")
    inventory = {}
    for row in manifest["files"]:
        if type(row) is not dict or set(row) != {"path", "sha256", "bytes"}:
            raise ValueError("Invalid manifest file record")
        name = row["path"]
        if (type(name) is not str or not (name == "private/controller.json"
                or re.fullmatch(r"public/[0-9a-f]{64}\.json", name)) or name in inventory):
            raise ValueError("Unsafe or duplicate manifest path")
        if type(row["sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
            raise ValueError("Invalid file hash")
        _worker._integer(row["bytes"], 1, 10**8, "file bytes")
        path = output / name
        _no_symlinks(path)
        if not path.is_file():
            raise ValueError("Manifest file is missing")
        data = path.read_bytes()
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("Serialized file hash or byte count mismatch")
        inventory[name] = data
    actual = set()
    for path in output.rglob("*"):
        if path.is_symlink():
            raise ValueError("Export paths must not contain symlinks")
        relative = path.relative_to(output).as_posix()
        if path.is_file():
            actual.add(relative)
        elif relative not in {"public", "private"}:
            raise ValueError("Unexpected export directory")
    if actual != set(inventory) | {"private/manifest.json"}:
        raise ValueError("Export inventory does not match serialized files")
    if "private/controller.json" not in inventory:
        raise ValueError("Private controller is missing")
    controller = _read_json(output / "private/controller.json")
    expected_public = _check_controller(controller)
    if set(inventory) != set(expected_public) | {"private/controller.json"}:
        raise ValueError("Public file counts do not match controller")
    for name, expected in expected_public.items():
        if inventory[name] != expected:
            raise ValueError("Public bytes do not match the one-query projection")
    return {"status": "verified", "verification": "serialized_integrity",
            "racket_reexecuted": False, "reference": REFERENCE,
            "episodes": len(controller["episodes"]), "public_files": len(expected_public),
            "demos": controller["request"]["demos"], "queries": controller["request"]["queries"]}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "verify":
        parser = argparse.ArgumentParser(description="Verify serialized export integrity; no Racket replay")
        parser.add_argument("output", type=Path)
        parsed = parser.parse_args(args[1:])
        action = lambda: verify_export(parsed.output)
    else:
        parser = argparse.ArgumentParser(description="Export both proposed settings through protected Racket")
        parser.add_argument("--out", type=Path, required=True)
        parser.add_argument("--seed", type=int, required=True)
        parser.add_argument("--demos", type=int, default=3)
        parser.add_argument("--queries", type=int, default=4)
        parsed = parser.parse_args(args)
        action = lambda: export_episodes(parsed.out, seed=parsed.seed,
                                        demos=parsed.demos, queries=parsed.queries)
    try:
        print(json.dumps(action(), sort_keys=True, allow_nan=False))
    except (ValueError, OSError) as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
