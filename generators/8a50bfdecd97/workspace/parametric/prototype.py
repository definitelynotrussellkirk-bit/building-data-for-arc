"""Evidence builder for a proposed source-action rule parameter.

The canonical/default setting ``move`` relocates the colored bitmap and erases
its source.  The nearby ``copy`` setting uses the same bracket interpretation,
destination, and transparent bitmap, but retains the source.  This module is a
separate prototype; it never changes the selected production Racket rule.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any


TASK_ID = "8a50bfdecd97"
PROTOTYPE_VERSION = "source-action-prototype-v1"
SOURCE_ACTIONS = ("move", "copy")
DEFAULT_SOURCE_ACTION = "move"
PAIR_COUNT = 4
TRAIN_COUNT = 3
INPUT_PROFILES = (
    "public_train_1",
    "pattern_hollow3",
    "pattern_cross",
    "pattern_stair",
)
DIFFICULTIES = ("easy", "medium", "hard", "medium")
ERASURE_BRANCH = "(if (= v sc) 7 v)"

TASK_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"

LIMITATIONS = [
    "Task-local prototype only; it does not alter the production generator, canonical rule, catalog, or approval state.",
    "source_action is limited to move and copy; bracket interpretation, destination alignment, colors, and transparent bitmap semantics remain unchanged.",
    "The hidden setting is chosen once per episode and is not present in public challenge JSON.",
    "The default move source is byte-for-byte canonical after outer whitespace is stripped; copy changes only the final source-erasure branch.",
    "Evidence covers two retained episodes, one per setting, four query rotations per episode, and the single declared rival setting.",
    "Finite rival checks establish the declared move/copy distinction only; they do not prove identification against arbitrary programs or training admission.",
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _validate_action(source_action: Any) -> str:
    if source_action not in SOURCE_ACTIONS or type(source_action) is not str:
        raise ValueError(
            f"source_action must be one of {SOURCE_ACTIONS}, got {source_action!r}"
        )
    return source_action


@lru_cache(maxsize=1)
def production_generator():
    """Load the selected generator in both portable and source-tree layouts."""
    try:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError:
        source = TASK_ROOT / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"source_action_production_{TASK_ID}", source
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load production generator from {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def source_identity() -> dict[str, Any]:
    generator_path = TASK_ROOT / "generator.py"
    return {
        "task_id": TASK_ID,
        "production_generator_version": production_generator().VERSION,
        "production_generator_sha256": _sha256_bytes(generator_path.read_bytes()),
        "prototype_source_sha256": _sha256_bytes(Path(__file__).read_bytes()),
    }


@lru_cache(maxsize=1)
def canonical_rule_source() -> str:
    sources = []
    for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and row.get("program_solution"):
            sources.append(str(row["program_solution"]).strip())
    if not sources:
        raise FileNotFoundError(f"no canonical rule source for {TASK_ID}")
    if len(set(sources)) != 1:
        raise RuntimeError(f"canonical rows disagree on rule source for {TASK_ID}")
    return sources[0]


def rule_source(source_action: Any) -> str:
    action = _validate_action(source_action)
    source = canonical_rule_source()
    if action == "move":
        return source
    if source.count(ERASURE_BRANCH) != 1:
        raise RuntimeError(
            "canonical source no longer has exactly one source-erasure branch"
        )
    return source.replace(ERASURE_BRANCH, "v", 1)


def source_action_for_seed(seed: Any) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    digest = hashlib.sha256(
        f"{PROTOTYPE_VERSION}:rule:{seed}".encode()
    ).digest()
    return SOURCE_ACTIONS[digest[0] % len(SOURCE_ACTIONS)]


def sample_inputs(seed: Any) -> list[list[list[int]]]:
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    gen = production_generator()
    inputs = []
    for index, (profile, difficulty) in enumerate(
        zip(INPUT_PROFILES, DIFFICULTIES, strict=True)
    ):
        derived = int.from_bytes(
            hashlib.sha256(
                f"{PROTOTYPE_VERSION}:input:{seed}:{index}".encode()
            ).digest()[:8],
            "big",
        )
        grid = gen.generate(
            derived,
            index,
            difficulty=difficulty,
            scene_profile=profile,
        )
        if gen.self_check(grid):
            raise RuntimeError(f"prototype input {index} left the production domain")
        inputs.append(grid)
    return inputs


def sample_episode(seed: Any, *, source_action: Any | None = None) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    action = (
        source_action_for_seed(seed)
        if source_action is None
        else _validate_action(source_action)
    )
    inputs = sample_inputs(seed)
    episode_id = "episode-" + _sha256_bytes(_json_bytes(inputs))[:16]
    return {
        "episode_id": episode_id,
        "seed": seed,
        "parameters": {"source_action": action},
        "program": rule_source(action),
        "inputs": inputs,
        "train_count": TRAIN_COUNT,
    }


def python_mirror(grid: list[list[int]], source_action: Any) -> list[list[int]]:
    action = _validate_action(source_action)
    gen = production_generator()
    analysis = gen._analysis(deepcopy(grid))
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = [row[:] for row in analysis["output"]]
    if action == "copy":
        color = analysis["shape_color"]
        for row, col in analysis["shape_cells"]:
            output[row][col] = color
    return output


def public_challenge(
    pairs: list[dict[str, Any]], query_index: int = TRAIN_COUNT
) -> dict[str, Any]:
    if (
        type(query_index) is not int
        or len(pairs) != PAIR_COUNT
        or not 0 <= query_index < PAIR_COUNT
    ):
        raise ValueError(f"query_index must select one of exactly {PAIR_COUNT} pairs")
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for index, pair in enumerate(pairs)
            if index != query_index
        ],
        "test": [{"input": deepcopy(pairs[query_index]["input"])}],
    }


def select_seeds(base_seed: Any) -> dict[str, Any]:
    if type(base_seed) is not int:
        raise TypeError("base_seed must be a literal Python integer")
    found: dict[str, int] = {}
    examined = 0
    for seed in range(base_seed, base_seed + 1000):
        examined += 1
        found.setdefault(source_action_for_seed(seed), seed)
        if set(found) == set(SOURCE_ACTIONS):
            break
    if set(found) != set(SOURCE_ACTIONS):
        raise RuntimeError("could not find one deterministic seed per setting")
    return {
        "base_seed": base_seed,
        "examined_seeds": examined,
        "by_source_action": {action: found[action] for action in SOURCE_ACTIONS},
        "seeds": [found[action] for action in SOURCE_ACTIONS],
    }


def _executed_predictions(
    inputs: list[list[list[int]]], source_action: str, racket_path: str
) -> tuple[list[list[list[int]]], dict[str, Any]]:
    from arc_repl.isolated_verifier import verify_candidate

    expected = [python_mirror(grid, source_action) for grid in inputs]
    request = {
        "train": [{"input": inputs[0], "output": expected[0]}],
        "test": [{"input": grid} for grid in inputs[1:]],
    }
    receipt = verify_candidate(
        request,
        rule_source(source_action),
        racket_path=racket_path,
    )
    if receipt.get("status") != "pass":
        raise RuntimeError(
            f"Racket verification failed for {source_action}: {receipt.get('error')}"
        )
    outputs = receipt["train_outputs"] + receipt["test_outputs"]
    if outputs != expected:
        raise RuntimeError(
            f"Racket/Python disagreement for source_action={source_action}"
        )
    return outputs, receipt


def _rotation_results(
    predictions: dict[str, list[list[list[int]]]], chosen: str
) -> list[dict[str, Any]]:
    rival = next(action for action in SOURCE_ACTIONS if action != chosen)
    rows = []
    for query_index in range(PAIR_COUNT):
        demos = [index for index in range(PAIR_COUNT) if index != query_index]
        mismatches = [
            index
            for index in demos
            if predictions[rival][index] != predictions[chosen][index]
        ]
        query_disagrees = (
            predictions[rival][query_index] != predictions[chosen][query_index]
        )
        status = (
            "refuted_by_demonstrations"
            if mismatches
            else "ambiguous_query"
            if query_disagrees
            else "survived_all"
        )
        rows.append(
            {
                "query_index": query_index,
                "rival_source_action": rival,
                "status": status,
                "demonstration_mismatches": mismatches,
                "query_disagrees": query_disagrees,
            }
        )
    return rows


def build_evidence(out: Path, *, base_seed: int, racket_path: str) -> dict[str, Any]:
    out = out.resolve()
    if out.exists():
        raise FileExistsError(f"refusing to overwrite evidence directory: {out}")
    (out / "public").mkdir(parents=True)
    (out / "private").mkdir()
    (out / "receipts").mkdir()

    selection = select_seeds(base_seed)
    episodes = []
    for action in SOURCE_ACTIONS:
        seed = selection["by_source_action"][action]
        episode = sample_episode(seed, source_action=action)
        predictions: dict[str, list[list[list[int]]]] = {}
        receipt_paths = {}
        for candidate in SOURCE_ACTIONS:
            outputs, receipt = _executed_predictions(
                episode["inputs"], candidate, racket_path
            )
            predictions[candidate] = outputs
            receipt_rel = f"receipts/{episode['episode_id']}-{candidate}.json"
            _write_json(out / receipt_rel, receipt)
            receipt_paths[candidate] = receipt_rel

        actual = predictions[action]
        pairs = [
            {"input": deepcopy(grid), "output": deepcopy(output)}
            for grid, output in zip(episode["inputs"], actual, strict=True)
        ]
        rotations = _rotation_results(predictions, action)
        if any(row["status"] != "refuted_by_demonstrations" for row in rotations):
            raise RuntimeError("a retained episode failed declared-rival identifiability")

        public_rel = f"public/{episode['episode_id']}.json"
        private_rel = f"private/{episode['episode_id']}.json"
        _write_json(out / public_rel, public_challenge(pairs))
        _write_json(
            out / private_rel,
            {
                "episode_id": episode["episode_id"],
                "seed": seed,
                "parameters": episode["parameters"],
                "program": episode["program"],
                "program_sha256": _sha256_bytes(episode["program"].encode()),
                "pairs": pairs,
                "predictions_by_setting": predictions,
                "query_rotations": rotations,
                "receipt_paths": receipt_paths,
            },
        )
        episodes.append(
            {
                "episode_id": episode["episode_id"],
                "seed": seed,
                "source_action": action,
                "public_path": public_rel,
                "public_sha256": _sha256_bytes((out / public_rel).read_bytes()),
                "private_path": private_rel,
                "private_sha256": _sha256_bytes((out / private_rel).read_bytes()),
                "receipt_paths": receipt_paths,
                "query_rotations": rotations,
            }
        )

    witness_input = sample_inputs(selection["seeds"][0])[0]
    witness_outputs = {
        action: python_mirror(witness_input, action) for action in SOURCE_ACTIONS
    }
    if witness_outputs["move"] == witness_outputs["copy"]:
        raise RuntimeError("cross-setting witness does not distinguish move and copy")

    report = {
        "schema": "arcpuzzles-parametric-prototype-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "pass",
        "parameter": {
            "name": "source_action",
            "allowed_values": list(SOURCE_ACTIONS),
            "default": DEFAULT_SOURCE_ACTION,
            "episode_scope": "chosen once and fixed for all demonstrations and query",
            "invariant_reasoning": [
                "identify the movable bitmap color and bounding box",
                "use the same-side bracket for row alignment",
                "use the opposite-side bracket interior for column alignment",
                "copy only occupied bitmap cells transparently",
            ],
            "varying_step": "erase the source for move; retain it for copy",
        },
        "canonical_default_exact": rule_source("move") == canonical_rule_source(),
        "canonical_rule_sha256": _sha256_bytes(canonical_rule_source().encode()),
        "rules": {
            action: {
                "sha256": _sha256_bytes(rule_source(action).encode()),
                "source": rule_source(action),
            }
            for action in SOURCE_ACTIONS
        },
        "seed_selection": selection,
        "episodes": episodes,
        "cross_setting_witness": {
            "input": witness_input,
            "outputs": witness_outputs,
            "distinguishes": True,
        },
        "source_identity": source_identity(),
        "racket_path": str(Path(racket_path).resolve()),
        "limitations": LIMITATIONS,
    }
    _write_json(out / "report.json", report)
    _write_json(
        out / "manifest.json",
        {
            "schema": "arcpuzzles-parametric-prototype-manifest-v1",
            "task_id": TASK_ID,
            "report": "report.json",
            "report_sha256": _sha256_bytes((out / "report.json").read_bytes()),
            "public_challenges": [row["public_path"] for row in episodes],
            "private_evidence": [row["private_path"] for row in episodes],
            "receipts": [
                path
                for row in episodes
                for path in row["receipt_paths"].values()
            ],
        },
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--base-seed", type=int, default=500)
    parser.add_argument(
        "--racket-path",
        default=os.environ.get("RACKET_PATH"),
        help="explicit Racket executable (defaults to activated RACKET_PATH)",
    )
    args = parser.parse_args(argv)
    if not args.racket_path:
        parser.error("--racket-path or RACKET_PATH is required")
    report = build_evidence(
        args.out,
        base_seed=args.base_seed,
        racket_path=args.racket_path,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "episodes": len(report["episodes"]),
                "out": str(args.out.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
