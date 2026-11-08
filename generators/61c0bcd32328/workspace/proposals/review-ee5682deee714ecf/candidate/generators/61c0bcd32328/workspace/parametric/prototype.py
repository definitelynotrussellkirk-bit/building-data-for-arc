"""Racket-backed direction-parametric episodes for ARC task ``61c0bcd32328``.

This is an isolated proposed extension, not a production API or approved rule.
The canonical ``clockwise`` setting returns the exact ledger program byte for
byte.  The alternative ``counterclockwise`` setting changes only the corner
translation table; component extraction, corner detection, preservation, and
painting semantics remain identical.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "61c0bcd32328"
PROTOTYPE_VERSION = "1.0.0"
DIRECTIONS = ("clockwise", "counterclockwise")
DEFAULT_DIRECTION = "clockwise"
CANONICAL_RULE_SHA256 = "0dc3328fe8ad885a19f7c620a4d641ffc733e8cc641a331d01b3e88410c5f64e"

_CLOCKWISE_TRANSLATION_BLOCK = """(let* ((dr (cond
                                                                     ((eq? corner 'tl) 0)
                                                                     ((eq? corner 'tr) (- h 1 r2))
                                                                     ((eq? corner 'br) 0)
                                                                     ((eq? corner 'bl) (- 0 r1))))
                                                               (dc (cond
                                                                     ((eq? corner 'tl) (- w 1 c2))
                                                                     ((eq? corner 'tr) 0)
                                                                     ((eq? corner 'br) (- 0 c1))
                                                                     ((eq? corner 'bl) 0))))
                                                          """

_COUNTERCLOCKWISE_TRANSLATION_BLOCK = """(let* ((dr (cond
                                                                     ((eq? corner 'tl) (- h 1 r2))
                                                                     ((eq? corner 'tr) 0)
                                                                     ((eq? corner 'br) (- 0 r1))
                                                                     ((eq? corner 'bl) 0)))
                                                               (dc (cond
                                                                     ((eq? corner 'tl) 0)
                                                                     ((eq? corner 'tr) (- 0 c1))
                                                                     ((eq? corner 'br) 0)
                                                                     ((eq? corner 'bl) (- w 1 c2)))))
                                                          """

_PROFILE_SEQUENCE = (
    "single_tl",
    "single_tr",
    "single_br",
    "single_bl",
    "adjacent_top",
    "adjacent_right",
    "adjacent_bottom",
    "adjacent_left",
    "three_missing_tl",
    "three_missing_br",
)
_DIFFICULTIES = ("easy", "medium", "hard")


def _sha256(value: str | bytes) -> str:
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def grid_sha256(grid) -> str:
    return _sha256(_json_bytes(normalize_grid(grid)))


def _resolved_root(root=None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


@lru_cache(maxsize=4)
def _canonical_rule_for_root(root_text: str) -> str:
    root = Path(root_text)
    sources: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source:
                    raise ValueError("Canonical row is missing an exact program_solution.")
                sources.append(source)
    unique = set(sources)
    if not sources or len(unique) != 1:
        raise ValueError(
            f"Direction prototype requires one exact canonical rule; found "
            f"{len(sources)} rows and {len(unique)} unique sources."
        )
    source = sources[0]
    digest = _sha256(source)
    if digest != CANONICAL_RULE_SHA256:
        raise ValueError(
            "Canonical rule SHA changed; reassess the direction substitution "
            f"(expected {CANONICAL_RULE_SHA256}, found {digest})."
        )
    return source


def canonical_rule(*, root=None) -> str:
    """Return the one exact canonical Racket program for this task."""
    return _canonical_rule_for_root(str(_resolved_root(root)))


def validate_direction(direction) -> str:
    if type(direction) is not str or direction not in DIRECTIONS:
        raise ValueError(f"direction must be exactly one of {DIRECTIONS}")
    return direction


def _validate_seed(seed) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative Python int (not bool)")
    return seed


def _validate_count(name: str, value) -> int:
    if type(value) is not int or not 1 <= value <= len(_PROFILE_SEQUENCE):
        raise ValueError(f"{name} must be a Python int in 1..{len(_PROFILE_SEQUENCE)}")
    return value


def _validate_difficulty(difficulty) -> str:
    if type(difficulty) is not str or difficulty not in _DIFFICULTIES:
        raise ValueError(f"difficulty must be exactly one of {_DIFFICULTIES}")
    return difficulty


def choose_direction(seed) -> str:
    """Choose one rule setting once per episode without touching global RNG."""
    seed = _validate_seed(seed)
    return DIRECTIONS[seed % len(DIRECTIONS)]


def program_for_direction(direction=DEFAULT_DIRECTION, *, root=None, source=None) -> str:
    """Materialize the exact Racket authority for one proposed setting.

    ``clockwise`` is the byte-exact canonical program.  ``counterclockwise``
    makes one guarded replacement of the translation table and nothing else.
    """
    direction = validate_direction(direction)
    source = canonical_rule(root=root) if source is None else source
    if not isinstance(source, str):
        raise ValueError("source must be exact canonical Racket text")
    digest = _sha256(source)
    if digest != CANONICAL_RULE_SHA256:
        raise ValueError(
            "canonical source SHA mismatch; refusing to materialize a variant "
            f"(expected {CANONICAL_RULE_SHA256}, found {digest})."
        )
    if direction == DEFAULT_DIRECTION:
        return source
    if source.count(_CLOCKWISE_TRANSLATION_BLOCK) != 1:
        raise ValueError("Canonical translation block changed; reassess the variant.")
    return source.replace(
        _CLOCKWISE_TRANSLATION_BLOCK,
        _COUNTERCLOCKWISE_TRANSLATION_BLOCK,
        1,
    )


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None) -> list[list[int]]:
    """Execute one exact program on one normalized grid through real Racket."""
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("Expected this task's native Racket lambda.")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    context = RacketBridge() if bridge is None else nullcontext(bridge)
    with context as active:
        return normalize_grid(active.eval_text(f"({function} '{datum})"))


@lru_cache(maxsize=4)
def _selected_generator_for_root(root_text: str):
    return load_selected_generator(TASK_ID, root=Path(root_text))


def selected_generator(*, root=None):
    return _selected_generator_for_root(str(_resolved_root(root)))


def _shift(corner: str, bbox, height: int, width: int, direction: str) -> tuple[int, int]:
    r1, c1, r2, c2 = bbox
    if direction == "clockwise":
        return {
            "tl": (0, width - 1 - c2),
            "tr": (height - 1 - r2, 0),
            "br": (0, -c1),
            "bl": (-r1, 0),
        }[corner]
    return {
        "tl": (height - 1 - r2, 0),
        "tr": (0, -c1),
        "br": (-r1, 0),
        "bl": (0, width - 1 - c2),
    }[corner]


def python_mirror(
    grid,
    direction=DEFAULT_DIRECTION,
    *,
    root=None,
    generator=None,
    skip_singletons: bool = False,
) -> list[list[int]]:
    """Independent Python parity mirror and bounded singleton-noise rival."""
    direction = validate_direction(direction)
    if type(skip_singletons) is not bool:
        raise ValueError("skip_singletons must be a Python bool")
    normalized = normalize_grid(grid)
    if generator is None:
        generator, _, _ = selected_generator(root=root)
    info = generator._analysis(normalized)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    output = [row[:] for row in normalized]
    for corner, part in info["corner_parts"]:
        if skip_singletons and len(part["cells"]) == 1:
            continue
        dr, dc = _shift(corner, part["bbox"], info["height"], info["width"], direction)
        for row, col in part["cells"]:
            output[row + dr][col + dc] = part["color"]
    return output


def _generate_inputs(
    seed: int,
    count: int,
    difficulty: str,
    *,
    root=None,
) -> tuple[list[list[list[int]]], list[dict]]:
    """Generate setting-independent inputs; the first visibly teaches singleton copying."""
    seed = _validate_seed(seed)
    count = _validate_count("total pair count", count)
    difficulty = _validate_difficulty(difficulty)
    generator, _, _ = selected_generator(root=root)
    inputs: list[list[list[int]]] = []
    metadata: list[dict] = []
    seen: set[str] = set()
    for index in range(count):
        profile = _PROFILE_SEQUENCE[index]
        singleton_required = index == 0
        for attempt in range(512):
            candidate_seed = seed * 100_003 + index * 1_009 + attempt
            sample_index = seed * 7_919 + index * 97 + attempt
            grid = generator.generate(
                candidate_seed,
                sample_index,
                difficulty=difficulty,
                scene_profile=profile,
            )
            info = generator._analysis(grid)
            digest = grid_sha256(grid)
            corner_sizes = [len(part["cells"]) for _, part in info["corner_parts"]]
            if info["errors"] or generator.self_check(grid):
                continue
            if digest in seen:
                continue
            if singleton_required and 1 not in corner_sizes:
                continue
            clockwise = python_mirror(
                grid, "clockwise", generator=generator, root=root
            )
            counterclockwise = python_mirror(
                grid, "counterclockwise", generator=generator, root=root
            )
            if clockwise == counterclockwise:
                continue
            seen.add(digest)
            inputs.append(grid)
            metadata.append(
                {
                    "profile": profile,
                    "candidate_seed": candidate_seed,
                    "sample_index": sample_index,
                    "attempt": attempt,
                    "corner_component_sizes": corner_sizes,
                    "has_singleton_corner": 1 in corner_sizes,
                }
            )
            break
        else:
            raise RuntimeError(
                f"Could not sample a distinct direction-separating {profile} input."
            )
    return inputs, metadata


def _mismatch_indices(expected, rival) -> list[int]:
    return [index for index, (left, right) in enumerate(zip(expected, rival)) if left != right]


def make_episode(
    seed,
    *,
    direction=None,
    train_count=3,
    test_count=4,
    difficulty="medium",
    root=None,
    bridge: RacketBridge | None = None,
) -> dict:
    """Build one episode whose fixed setting labels every pair through Racket."""
    seed = _validate_seed(seed)
    train_count = _validate_count("train_count", train_count)
    test_count = _validate_count("test_count", test_count)
    if train_count + test_count > len(_PROFILE_SEQUENCE):
        raise ValueError(
            f"train_count + test_count must be at most {len(_PROFILE_SEQUENCE)}"
        )
    difficulty = _validate_difficulty(difficulty)
    chosen = choose_direction(seed) if direction is None else validate_direction(direction)
    rival = next(value for value in DIRECTIONS if value != chosen)
    root = _resolved_root(root)
    generator, generator_path, generator_sha256 = selected_generator(root=root)
    inputs, input_metadata = _generate_inputs(
        seed, train_count + test_count, difficulty, root=root
    )
    chosen_program = program_for_direction(chosen, root=root)
    rival_program = program_for_direction(rival, root=root)

    context = RacketBridge() if bridge is None else nullcontext(bridge)
    with context as active:
        outputs = [execute_rule(chosen_program, grid, bridge=active) for grid in inputs]
        rival_outputs = [execute_rule(rival_program, grid, bridge=active) for grid in inputs]

    for grid, output, rival_output in zip(inputs, outputs, rival_outputs):
        if output != python_mirror(grid, chosen, generator=generator, root=root):
            raise AssertionError("Chosen Racket program disagrees with Python parity mirror.")
        if rival_output != python_mirror(grid, rival, generator=generator, root=root):
            raise AssertionError("Rival Racket program disagrees with Python parity mirror.")

    singleton_rival_outputs = [
        python_mirror(
            grid,
            chosen,
            generator=generator,
            root=root,
            skip_singletons=True,
        )
        for grid in inputs
    ]
    pairs = [
        {
            "input": grid,
            "output": output,
            "direction": chosen,
            "input_sha256": grid_sha256(grid),
            **meta,
        }
        for grid, output, meta in zip(inputs, outputs, input_metadata)
    ]
    demo_outputs = outputs[:train_count]
    query_outputs = outputs[train_count:]
    parameter_demo_mismatches = _mismatch_indices(
        demo_outputs, rival_outputs[:train_count]
    )
    parameter_query_mismatches = _mismatch_indices(
        query_outputs, rival_outputs[train_count:]
    )
    singleton_demo_mismatches = _mismatch_indices(
        demo_outputs, singleton_rival_outputs[:train_count]
    )
    singleton_query_mismatches = _mismatch_indices(
        query_outputs, singleton_rival_outputs[train_count:]
    )
    ambiguities = []
    if not parameter_demo_mismatches:
        ambiguities.append("opposite direction survives every demonstration")
    if not singleton_demo_mismatches:
        ambiguities.append("ignore-singletons rival survives every demonstration")

    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "parameters": {"direction": chosen},
        "parameter_choice": (
            "seed_modulo_two" if direction is None else "explicit_once_per_episode"
        ),
        "counts": {"train": train_count, "test": test_count},
        "generator_source": str(generator_path.relative_to(root)),
        "generator_sha256": generator_sha256,
        "racket_program": chosen_program,
        "racket_sha256": _sha256(chosen_program),
        "train": pairs[:train_count],
        "test": pairs[train_count:],
        "parameter_rivals": [
            {
                "direction": rival,
                "racket_sha256": _sha256(rival_program),
                "status": (
                    "refuted_by_demonstrations"
                    if parameter_demo_mismatches
                    else "ambiguous_query"
                ),
                "demonstration_mismatch_indices": parameter_demo_mismatches,
                "query_mismatch_indices": parameter_query_mismatches,
            }
        ],
        "shortcut_rivals": [
            {
                "name": "ignore_singleton_corner_components",
                "status": (
                    "refuted_by_demonstrations"
                    if singleton_demo_mismatches
                    else "ambiguous_query"
                ),
                "demonstration_mismatch_indices": singleton_demo_mismatches,
                "query_mismatch_indices": singleton_query_mismatches,
            }
        ],
        "ambiguities": ambiguities,
    }


def public_challenge(episode: dict) -> dict:
    """Return only visible demonstrations and unlabeled query inputs."""
    return deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _private_id(index: int) -> str:
    return f"episode-{index:03d}"


def write_evidence(
    seeds,
    *,
    out,
    train_count=3,
    test_count=4,
    difficulty="medium",
    root=None,
) -> dict:
    """Create immutable private/public evidence for both proposed settings."""
    root = _resolved_root(root)
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite evidence directory: {out}")
    seed_list = [_validate_seed(seed) for seed in seeds]
    if not seed_list or len(seed_list) != len(set(seed_list)):
        raise ValueError("seeds must be a nonempty list of distinct integers")
    train_count = _validate_count("train_count", train_count)
    test_count = _validate_count("test_count", test_count)
    if train_count + test_count > len(_PROFILE_SEQUENCE):
        raise ValueError(
            f"train_count + test_count must be at most {len(_PROFILE_SEQUENCE)}"
        )
    difficulty = _validate_difficulty(difficulty)
    out.mkdir(parents=True)

    rule_rows: list[dict] = []
    rule_paths: dict[str, str] = {}
    for direction in DIRECTIONS:
        program = program_for_direction(direction, root=root)
        digest = _sha256(program)
        relative = f"private/rules/rule-{digest[:16]}.rkt"
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program, encoding="utf-8")
        rule_paths[direction] = relative
        rule_rows.append(
            {
                "direction": direction,
                "path": relative,
                "sha256": digest,
                "canonical_exact": direction == DEFAULT_DIRECTION,
            }
        )

    canonical_rows = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    episode_rows: list[dict] = []
    public_ids: set[str] = set()
    distinct_inputs: set[str] = set()
    max_sampler_attempt = 0
    racket_evaluations = 0
    witness = None

    with RacketBridge() as bridge:
        canonical_program = program_for_direction(DEFAULT_DIRECTION, root=root)
        for pair in canonical_rows:
            actual = execute_rule(canonical_program, pair["input"], bridge=bridge)
            racket_evaluations += 1
            if actual != pair["output"]:
                raise AssertionError(
                    f"Canonical default disagrees at variant {pair['variant']} "
                    f"{pair['split']} pair {pair['pair_index']}."
                )

        for index, seed in enumerate(seed_list):
            episode = make_episode(
                seed,
                train_count=train_count,
                test_count=test_count,
                difficulty=difficulty,
                root=root,
                bridge=bridge,
            )
            replay = make_episode(
                seed,
                train_count=train_count,
                test_count=test_count,
                difficulty=difficulty,
                root=root,
                bridge=bridge,
            )
            racket_evaluations += 4 * (train_count + test_count)
            if replay != episode:
                raise AssertionError("Same-seed episode replay changed.")
            if episode["ambiguities"]:
                raise AssertionError(f"Unresolved episode ambiguity: {episode['ambiguities']}")

            challenge = public_challenge(episode)
            public_bytes = public_challenge_bytes(challenge)
            public_id = public_challenge_id(challenge)
            if _sha256(public_bytes) != public_id:
                raise AssertionError("Public ID is not the SHA-256 of exact visible bytes.")
            if public_id in public_ids:
                raise ValueError("Duplicate visible public challenge payload.")
            public_ids.add(public_id)

            changed_private = deepcopy(episode)
            changed_private["seed"] += 100_000
            changed_private["parameters"]["direction"] = next(
                value for value in DIRECTIONS
                if value != episode["parameters"]["direction"]
            )
            changed_private["test"][0]["output"][0][0] = (
                changed_private["test"][0]["output"][0][0] + 1
            ) % 10
            if public_challenge_bytes(public_challenge(changed_private)) != public_bytes:
                raise AssertionError("Private metadata or query answer changed public bytes.")

            private = deepcopy(episode)
            private.pop("racket_program")
            private["racket_path"] = rule_paths[private["parameters"]["direction"]]
            private_name = _private_id(index)
            private_path = f"private/{private_name}.json"
            public_path = f"public/challenge-{public_id}.json"
            _write_json(out / private_path, private)
            (out / public_path).parent.mkdir(parents=True, exist_ok=True)
            (out / public_path).write_bytes(public_bytes)

            for pair in private["train"] + private["test"]:
                distinct_inputs.add(pair["input_sha256"])
                max_sampler_attempt = max(max_sampler_attempt, pair["attempt"])

            if witness is None:
                grid = private["train"][0]["input"]
                clockwise = execute_rule(
                    program_for_direction("clockwise", root=root), grid, bridge=bridge
                )
                counterclockwise = execute_rule(
                    program_for_direction("counterclockwise", root=root), grid, bridge=bridge
                )
                racket_evaluations += 2
                differences = [
                    [row, col, clockwise[row][col], counterclockwise[row][col]]
                    for row in range(len(grid))
                    for col in range(len(grid[0]))
                    if clockwise[row][col] != counterclockwise[row][col]
                ]
                witness = {
                    "input": grid,
                    "clockwise_output": clockwise,
                    "counterclockwise_output": counterclockwise,
                    "different_cells": differences,
                    "singleton_corner_component_sizes": private["train"][0][
                        "corner_component_sizes"
                    ],
                    "clockwise_racket_sha256": _sha256(
                        program_for_direction("clockwise", root=root)
                    ),
                    "counterclockwise_racket_sha256": _sha256(
                        program_for_direction("counterclockwise", root=root)
                    ),
                }

            episode_rows.append(
                {
                    "seed": seed,
                    "parameters": private["parameters"],
                    "public_id": public_id,
                    "public_path": public_path,
                    "private_path": private_path,
                    "racket_path": private["racket_path"],
                    "racket_sha256": private["racket_sha256"],
                    "deterministic_replay": True,
                    "parameter_rivals": private["parameter_rivals"],
                    "shortcut_rivals": private["shortcut_rivals"],
                }
            )

    if witness is None:
        raise AssertionError("No distinguishing witness was produced.")
    _write_json(out / "private/distinguishing-witness.json", witness)
    adversarial = {
        "sampler_boundary": {
            "pair_count": train_count + test_count,
            "profile_capacity": len(_PROFILE_SEQUENCE),
            "max_attempt_used": max_sampler_attempt,
            "all_inputs_distinct": len(distinct_inputs) == len(seed_list) * (train_count + test_count),
        },
        "parameter_racket_parity": {
            "all_episode_labels_checked": True,
            "both_settings_checked": set(row["parameters"]["direction"] for row in episode_rows) == set(DIRECTIONS),
        },
        "public_private_projection": {
            "ids_are_visible_byte_hashes": True,
            "private_metadata_and_query_answer_invariance_checked": True,
            "duplicate_visible_payloads_rejected": True,
        },
        "singleton_shortcut": {
            "first_demonstration_has_singleton_corner": 1 in witness["singleton_corner_component_sizes"],
            "refuted_in_every_episode": all(
                row["shortcut_rivals"][0]["status"] == "refuted_by_demonstrations"
                for row in episode_rows
            ),
        },
    }
    _write_json(out / "private/adversarial-checks.json", adversarial)

    prototype_path = Path(__file__).resolve()
    generator, generator_path, generator_sha256 = selected_generator(root=root)
    del generator
    files = [
        {
            "path": str(path.relative_to(out)),
            "sha256": _sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "direction",
            "allowed_values": list(DIRECTIONS),
            "original_default": DEFAULT_DIRECTION,
            "input_constraints_depend_on_parameter": False,
            "fixed_once_per_episode": True,
        },
        "reasoning_invariants": [
            "identify same-color 4-connected foreground components",
            "select components whose bounding boxes touch a canvas corner",
            "translate each selected component to one adjacent corner",
            "preserve every input cell and paint copied cells in the component color",
        ],
        "sources": {
            "prototype_path": str(prototype_path.relative_to(root)),
            "prototype_sha256": _sha256(prototype_path.read_bytes()),
            "generator_path": str(generator_path.relative_to(root)),
            "generator_sha256": generator_sha256,
            "canonical_path": str(canonical_path(root).relative_to(root)),
            "canonical_rule_sha256": CANONICAL_RULE_SHA256,
        },
        "rules": rule_rows,
        "episodes": episode_rows,
        "counts": {
            "episodes": len(episode_rows),
            "train_pairs": train_count * len(episode_rows),
            "query_pairs": test_count * len(episode_rows),
            "queries_per_episode": test_count,
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len(
                {row["parameters"]["direction"] for row in episode_rows}
            ),
            "canonical_pairs_checked": len(canonical_rows),
            "racket_evaluations_including_replays": racket_evaluations,
            "ambiguous_parameter_rivals": sum(
                rival["status"] != "refuted_by_demonstrations"
                for row in episode_rows
                for rival in row["parameter_rivals"]
            ),
        },
        "adversarial": adversarial,
        "files": files,
        "limitations": [
            "Proposed prototype only; it does not alter the production API, canonical rule, approval, or training admission.",
            "Evidence covers the recorded seeds, ten declared profile slots, and direction values clockwise/counterclockwise; it is not an all-input proof.",
            "The only parameter rival checked is the opposite direction; the separate singleton-noise shortcut is also checked because it was a retained source-bound audit.",
            "At most ten total pairs are supported by the fixed profile schedule; requests beyond that fail instead of cloning inputs.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--train", type=int, default=3, dest="train_count")
    parser.add_argument("--test", type=int, default=4, dest="test_count")
    parser.add_argument("--difficulty", choices=_DIFFICULTIES, default="medium")
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args(argv)
    report = write_evidence(
        args.seeds,
        out=args.out,
        train_count=args.train_count,
        test_count=args.test_count,
        difficulty=args.difficulty,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
