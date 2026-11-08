#!/usr/bin/env python3
"""Task-local, unapproved frame-row lookup variants for ARC a61246736c26.

Outputs always come from the shared protected Racket bridge.  The canonical
program and selected generator remain authoritative and are never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
RUNTIME = ROOT / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

# The repository keeps legacy scripts/ modules in shared/tools.  Bind that
# namespace in place for direct authoring; the relocated runtime already has it.
if importlib.util.find_spec("scripts") is None:
    _scripts_spec = importlib.machinery.ModuleSpec("scripts", loader=None, is_package=True)
    _scripts_spec.submodule_search_locations[:] = [str(ROOT / "shared/tools")]
    sys.modules["scripts"] = importlib.util.module_from_spec(_scripts_spec)

from puzzle_generators.base import gen_ctx
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "a61246736c26"
VERSION = "1.0.0"
SCHEMA = "arcpuzzles-parametric-prototype-v1"
ALLOWED_OFFSETS = (0, 1, 2)
DEFAULT_OFFSET = 0
CANONICAL_RULE_HASH = "08238424436c"
LOOKUP = "(frame (list-ref row-colors (first solid)))"
PROFILES = ("row_cycle_012", "permuted_frames", "four_columns_reverse", "zero_frame_all")
PARAMETER_SPEC = {
    "frame_row_offset": {
        "allowed_values": list(ALLOWED_OFFSETS),
        "default": DEFAULT_OFFSET,
        "meaning": "Select row-colors[(solid-row + offset) modulo 3] for each output frame.",
        "scope": "One value per episode; fixed across every demonstration and query.",
        "input_constraints": "Three distinct row swatches; original duplicated patterns and one solid per column.",
    }
}
SOURCE_PATHS = (
    "generators/a61246736c26/workspace/parametric/prototype.py",
    "generators/a61246736c26/workspace/parametric/README.md",
    "generators/a61246736c26/tests/test_parametric_a61246736c26.py",
    "generators/a61246736c26/generator.py",
    "shared/runtime/puzzle_generators/base.py",
    "shared/runtime/puzzle_generators/rule_wrap.py",
    "shared/tools/comment_solutions.py",
)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def normalized_rule_hash(program):
    return sha256(" ".join(program.split()).encode())[:12]


def source_hashes():
    return {relative: sha256((ROOT / relative).read_bytes()) for relative in SOURCE_PATHS}


@lru_cache(maxsize=1)
def canonical_record():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise ValueError(f"Canonical task {TASK_ID} is absent from {path}")


@lru_cache(maxsize=1)
def generator_module():
    spec = importlib.util.spec_from_file_location(
        "a61246736c26_canonical_generator", ROOT / f"generators/{TASK_ID}/generator.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_offset(offset):
    if type(offset) is not int or offset not in ALLOWED_OFFSETS:
        raise ValueError("frame_row_offset must be an integer in {0, 1, 2}")
    return offset


def choose_offset(seed, requested=DEFAULT_OFFSET):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if requested == "sampled":
        ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION, task_id=TASK_ID + "_parametric")
        return ctx.draw_choice("episode.frame_row_offset", ALLOWED_OFFSETS)
    return valid_offset(requested)


def materialize_program(frame_row_offset=DEFAULT_OFFSET):
    offset = valid_offset(frame_row_offset)
    source = canonical_record()["program_solution"]
    if normalized_rule_hash(source) != CANONICAL_RULE_HASH or source.count(LOOKUP) != 1:
        raise ValueError("Canonical rule changed; re-review this prototype before materializing variants")
    if offset == 0:
        return source  # Preserve the exact canonical bytes, including whitespace.
    replacement = (
        "(frame (list-ref row-colors "
        f"(modulo (+ (first solid) {offset}) (length row-colors))))"
    )
    return source.replace(LOOKUP, replacement, 1)


def validate_grid(grid):
    if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
        raise ValueError("Grid must have 1..30 rows")
    if not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= 30:
        raise ValueError("Grid must have 1..30 columns")
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        raise ValueError("Grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("Grid cells must be integer ARC colors")


def collect_inputs(seed, n_train=3, n_test=1):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(n_train) is not int or not 1 <= n_train <= 8:
        raise ValueError("n_train must be 1..8")
    if type(n_test) is not int or not 1 <= n_test <= 4:
        raise ValueError("n_test must be 1..4")
    generator = generator_module()
    pairs = []
    for index in range(n_train + n_test):
        profile = PROFILES[index % len(PROFILES)]
        grid = generator.generate(seed, index, difficulty="medium", scene_profile=profile)
        validate_grid(grid)
        errors = generator.self_check(grid)
        if errors:
            raise ValueError(f"Canonical input contract failed for pair {index}: {errors}")
        pairs.append({"sample_index": index, "scene_profile": profile, "difficulty": "medium", "input": grid})
    return pairs


def execute_outputs(bridge, pairs):
    """Execute every declared rival on every pair, without a Python label path."""
    for offset in ALLOWED_OFFSETS:
        callable_source = wrap_rule(materialize_program(offset))
        bridge.eval_text(f"(define __a612_frame_{offset} {callable_source})")
    outputs = {str(offset): [] for offset in ALLOWED_OFFSETS}
    for pair in pairs:
        validate_grid(pair["input"])
        bridge.define_grid("__a612_input", pair["input"])
        for offset in ALLOWED_OFFSETS:
            output = bridge.eval_text(f"(__a612_frame_{offset} __a612_input)")
            validate_grid(output)
            outputs[str(offset)].append(output)
    return outputs


def canonical_checks(bridge):
    """Execute the exact default against all three recorded canonical pairs."""
    checks = []
    record = canonical_record()
    for index, pair in enumerate(record["train"] + record["test"]):
        bridge.define_grid("__a612_input", pair["input"])
        output = bridge.eval_text("(__a612_frame_0 __a612_input)")
        validate_grid(output)
        checks.append({"pair_index": index, "input": pair["input"], "expected_output": pair["output"],
                       "executed_output": output, "passed": output == pair["output"]})
    if not all(row["passed"] for row in checks):
        raise ValueError("Default program failed a canonical example")
    return checks


def identifiability_report(outputs, chosen, n_train):
    chosen = valid_offset(chosen)
    expected = outputs[str(chosen)]
    count = len(expected)
    if not 1 <= n_train < count or any(len(outputs[str(offset)]) != count for offset in ALLOWED_OFFSETS):
        raise ValueError("Need demonstrations, queries, and equally sized rival output vectors")

    def survivors(indices):
        indices = tuple(indices)  # Reuse the same demonstration indices for every rival.
        return [offset for offset in ALLOWED_OFFSETS
                if all(outputs[str(offset)][index] == expected[index] for index in indices)]

    surviving = survivors(range(n_train))
    changing = [offset for offset in surviving
                if any(outputs[str(offset)][index] != expected[index] for index in range(n_train, count))]
    rivals = []
    for offset in ALLOWED_OFFSETS:
        if offset == chosen:
            continue
        distinguishing = [index for index in range(n_train) if outputs[str(offset)][index] != expected[index]]
        rivals.append({"frame_row_offset": offset, "distinguishing_demonstrations": distinguishing,
                       "query_disagreements": [index - n_train for index in range(n_train, count)
                                               if outputs[str(offset)][index] != expected[index]]})
    rotations = []
    for query in range(count):
        remaining = survivors(index for index in range(count) if index != query)
        query_changing = [offset for offset in remaining if outputs[str(offset)][query] != expected[query]]
        rotations.append({"query_pair_index": query, "surviving_offsets": remaining,
                          "query_changing_survivors": query_changing,
                          "passed": remaining == [chosen] and not query_changing})
    return {"surviving_offsets": surviving, "query_changing_survivors": changing,
            "rivals": rivals, "query_rotations": rotations,
            "passed": surviving == [chosen] and not changing and all(row["passed"] for row in rotations)}


def public_projection(bundle, episode):
    outputs = bundle["executed_outputs"][str(episode["parameters"]["frame_row_offset"])]
    n_train = bundle["n_train"]
    return {"train": [{"input": pair["input"], "output": outputs[index]}
                      for index, pair in enumerate(bundle["pairs"][:n_train])],
            "test": [{"input": pair["input"]} for pair in bundle["pairs"][n_train:]]}


def create_bundle(bridge, *, seed, frame_row_offset=DEFAULT_OFFSET, all_settings=False, n_train=3, n_test=1):
    before = source_hashes()
    # Choose one rule value for each episode before any input or output draw.
    offsets = list(ALLOWED_OFFSETS) if all_settings else [choose_offset(seed, frame_row_offset)]
    selection = "enumerated" if all_settings else "seeded" if frame_row_offset == "sampled" else "explicit"
    pairs = collect_inputs(seed, n_train, n_test)
    outputs = execute_outputs(bridge, pairs)
    episodes = []
    for index, offset in enumerate(offsets):
        report = identifiability_report(outputs, offset, n_train)
        if not report["passed"]:
            raise ValueError(f"Offset {offset} is not identifiable: {report}")
        episodes.append({"index": index, "parameters": {"frame_row_offset": offset}, "selection": selection,
                         "public_path": f"public/episode-{index:03d}.json", "identifiability": report})
    programs = {str(offset): {"source": materialize_program(offset),
                              "sha256": sha256(materialize_program(offset).encode()),
                              "normalized_rule_hash": normalized_rule_hash(materialize_program(offset))}
                for offset in ALLOWED_OFFSETS}
    witness_count = len({json.dumps(outputs[str(offset)][0]) for offset in ALLOWED_OFFSETS})
    bundle = {"schema": SCHEMA, "status": "prototype", "task_id": TASK_ID, "seed": seed,
              "parameter_spec": PARAMETER_SPEC, "n_train": n_train, "n_test": n_test,
              "source_hashes": before, "runtime_identity": bridge.runtime_identity,
              "canonical_rule_hash": CANONICAL_RULE_HASH,
              "canonical_record_sha256": sha256(json_bytes(canonical_record())),
              "programs": programs, "pairs": pairs, "executed_outputs": outputs, "episodes": episodes,
              "canonical_checks": canonical_checks(bridge),
              "witness": {"pair_index": 0, "distinct_output_count": witness_count},
              "limitations": ["A task-local proposed extension; no production parametric API or approval.",
                              "Identifiability is checked only against the declared offsets 0, 1, 2.",
                              "Query rotations exchange demonstration/query roles; they do not spatially rotate grids.",
                              "Retained execution evidence covers the recorded seed and stable medium profiles only."]}
    if source_hashes() != before:
        raise ValueError("Source changed during generation; rerun after edits finish")
    validate_bundle(bundle)
    return bundle


def validate_bundle(bundle):
    if bundle.get("schema") != SCHEMA or bundle.get("task_id") != TASK_ID or bundle.get("status") != "prototype":
        raise ValueError("Wrong prototype schema, task, or status")
    if bundle.get("source_hashes") != source_hashes():
        raise ValueError("Recorded source hashes differ from current sources")
    if bundle.get("parameter_spec") != PARAMETER_SPEC or bundle.get("canonical_rule_hash") != CANONICAL_RULE_HASH:
        raise ValueError("Parameter specification or canonical rule binding differs")
    if bundle.get("canonical_record_sha256") != sha256(json_bytes(canonical_record())):
        raise ValueError("Canonical record changed")
    expected_pairs = collect_inputs(bundle["seed"], bundle["n_train"], bundle["n_test"])
    if bundle["pairs"] != expected_pairs:
        raise ValueError("Input draws do not reproduce from their recorded seed")
    if set(bundle["programs"]) != {str(offset) for offset in ALLOWED_OFFSETS}:
        raise ValueError("Missing or extra parameter programs")
    if set(bundle["executed_outputs"]) != set(bundle["programs"]):
        raise ValueError("Missing rival execution outputs")
    for offset in ALLOWED_OFFSETS:
        source = materialize_program(offset)
        expected = {"source": source, "sha256": sha256(source.encode()),
                    "normalized_rule_hash": normalized_rule_hash(source)}
        if bundle["programs"][str(offset)] != expected:
            raise ValueError("Recorded program differs from the materialized parameter rule")
        outputs = bundle["executed_outputs"][str(offset)]
        if len(outputs) != len(bundle["pairs"]):
            raise ValueError("Wrong output count")
        for output in outputs:
            validate_grid(output)
    if len(bundle["episodes"]) not in (1, len(ALLOWED_OFFSETS)):
        raise ValueError("Expected one episode or the declared setting sweep")
    if len(bundle["episodes"]) == len(ALLOWED_OFFSETS):
        if [episode["parameters"]["frame_row_offset"] for episode in bundle["episodes"]] != list(ALLOWED_OFFSETS):
            raise ValueError("Setting sweep must enumerate each declared offset exactly once")
        if any(episode["selection"] != "enumerated" for episode in bundle["episodes"]):
            raise ValueError("Setting sweep must record enumerated selection")
    for index, episode in enumerate(bundle["episodes"]):
        if set(episode["parameters"]) != {"frame_row_offset"}:
            raise ValueError("Unexpected parameters")
        offset = valid_offset(episode["parameters"]["frame_row_offset"])
        if episode["index"] != index or episode["public_path"] != f"public/episode-{index:03d}.json":
            raise ValueError("Unexpected episode identity")
        if episode["selection"] not in ("enumerated", "explicit", "seeded"):
            raise ValueError("Unknown parameter selection mode")
        if episode["selection"] == "seeded" and offset != choose_offset(bundle["seed"], "sampled"):
            raise ValueError("Parameter selection does not reproduce from the episode seed")
        report = identifiability_report(bundle["executed_outputs"], offset, bundle["n_train"])
        if episode["identifiability"] != report or not report["passed"]:
            raise ValueError("Unidentified or inconsistent parameter rivals")
    if bundle["witness"] != {"pair_index": 0, "distinct_output_count": 3}:
        raise ValueError("Missing lawful distinguishing witness")


def write_bundle(out, bundle, *, command):
    validate_bundle(bundle)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "programs").mkdir()
    for episode in bundle["episodes"]:
        (out / episode["public_path"]).write_bytes(json_bytes(public_projection(bundle, episode)))
    for offset in ALLOWED_OFFSETS:
        (out / f"programs/frame-offset-{offset}.rkt").write_bytes(bundle["programs"][str(offset)]["source"].encode())
    (out / "private.json").write_bytes(json_bytes(bundle))
    files = ["private.json"] + [f"programs/frame-offset-{offset}.rkt" for offset in ALLOWED_OFFSETS]
    files += [episode["public_path"] for episode in bundle["episodes"]]
    manifest = {"schema": SCHEMA + "-manifest", "status": "prototype", "task_id": TASK_ID,
                "generator_sha256": bundle["source_hashes"][f"generators/{TASK_ID}/generator.py"],
                "canonical_rule_hash": CANONICAL_RULE_HASH, "parameters": PARAMETER_SPEC,
                "command": command, "cwd": str(Path.cwd()),
                "files": [{"path": name, "sha256": sha256((out / name).read_bytes()),
                           "bytes": (out / name).stat().st_size} for name in files]}
    (out / "manifest.json").write_bytes(json_bytes(manifest))
    return manifest


def check_bundle(out, bridge):
    out = Path(out)
    manifest = json.loads((out / "manifest.json").read_text())
    bundle = json.loads((out / "private.json").read_text())
    validate_bundle(bundle)
    if (manifest.get("schema") != SCHEMA + "-manifest" or manifest.get("task_id") != TASK_ID
            or manifest.get("status") != "prototype" or manifest.get("parameters") != PARAMETER_SPEC
            or manifest.get("canonical_rule_hash") != CANONICAL_RULE_HASH
            or manifest.get("generator_sha256") != bundle["source_hashes"][f"generators/{TASK_ID}/generator.py"]):
        raise ValueError("Manifest identity, parameters, or source binding differs")
    expected_files = {"private.json"} | {f"programs/frame-offset-{offset}.rkt" for offset in ALLOWED_OFFSETS}
    expected_files |= {episode["public_path"] for episode in bundle["episodes"]}
    if {item["path"] for item in manifest["files"]} != expected_files or len(manifest["files"]) != len(expected_files):
        raise ValueError("Evidence inventory differs")
    for item in manifest["files"]:
        raw = (out / item["path"]).read_bytes()
        if sha256(raw) != item["sha256"] or len(raw) != item["bytes"]:
            raise ValueError(f"Evidence hash/size mismatch: {item['path']}")
    for offset in ALLOWED_OFFSETS:
        if (out / f"programs/frame-offset-{offset}.rkt").read_bytes() != materialize_program(offset).encode():
            raise ValueError("Materialized Racket file differs")
    for episode in bundle["episodes"]:
        public = json.loads((out / episode["public_path"]).read_text())
        if public != public_projection(bundle, episode):
            raise ValueError("Public challenge differs or discloses private metadata/query answers")
    actual = execute_outputs(bridge, bundle["pairs"])
    if actual != bundle["executed_outputs"]:
        raise ValueError("Racket replay differs from retained execution outputs")
    checks = canonical_checks(bridge)
    if checks != bundle["canonical_checks"]:
        raise ValueError("Canonical replay differs from retained execution outputs")
    validate_bundle(bundle)
    return {"schema": SCHEMA + "-check", "status": "prototype", "passed": True,
            "episode_count": len(bundle["episodes"]), "pairs_per_episode": len(bundle["pairs"]),
            "unique_input_count": len(bundle["pairs"]),
            "executed_rule_pair_count": len(ALLOWED_OFFSETS) * len(bundle["pairs"]) + len(checks),
            "canonical_pair_count": len(checks),
            "parameter_rival_checks": len(bundle["episodes"]) * (len(ALLOWED_OFFSETS) - 1),
            "query_rotation_checks": len(bundle["episodes"]) * len(bundle["pairs"]),
            "source_hashes": source_hashes(), "runtime_identity": bridge.runtime_identity,
            "manifest_sha256": sha256((out / "manifest.json").read_bytes()),
            "private_sha256": sha256((out / "private.json").read_bytes()),
            "program_sha256": {key: value["sha256"] for key, value in bundle["programs"].items()}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="Write new public challenges and private executed evidence")
    generate.add_argument("--seed", type=int, default=1701)
    choice = generate.add_mutually_exclusive_group()
    choice.add_argument("--frame-row-offset", choices=("0", "1", "2", "sampled"), default="0")
    choice.add_argument("--all-settings", action="store_true")
    generate.add_argument("--n-train", type=int, default=3)
    generate.add_argument("--n-test", type=int, default=1)
    generate.add_argument("--out", type=Path, required=True)
    check = commands.add_parser("check", help="Re-execute all parameter rivals and validate the retained bundle")
    check.add_argument("--bundle", type=Path, required=True)
    check.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as bridge:
        if args.command == "generate":
            requested = args.frame_row_offset if args.frame_row_offset == "sampled" else int(args.frame_row_offset)
            bundle = create_bundle(bridge, seed=args.seed, frame_row_offset=requested,
                                   all_settings=args.all_settings, n_train=args.n_train, n_test=args.n_test)
            manifest = write_bundle(args.out, bundle, command=[sys.executable, *sys.argv])
            result = {"status": "prototype", "episode_count": len(bundle["episodes"]),
                      "out": str(args.out), "files": len(manifest["files"]),
                      "generator_sha256": manifest["generator_sha256"],
                      "private_sha256": sha256((args.out / "private.json").read_bytes())}
        else:
            result = check_bundle(args.bundle, bridge)
            result["command"] = [sys.executable, *sys.argv]
            result["cwd"] = str(Path.cwd())
            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                with args.report.open("x") as stream:
                    json.dump(result, stream, indent=2, sort_keys=True)
                    stream.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
