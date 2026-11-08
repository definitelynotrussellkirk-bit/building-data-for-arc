#!/usr/bin/env python3
"""Bounded prototype for a fixed-per-episode boundary-color palette.

The canonical/default rule uses color 1 for the zero-opposing-pair class
(corners and ends), color 4 for the exactly-one-opposing-pair class (edges),
and color 2 for the two-pair interior class.  The proposed variant swaps only
colors 1 and 4.  The setting is selected once from the episode seed and held
fixed across independently requested demonstrations and queries.

This module is deliberately isolated from the selected production generator.
The canonical rule, generator ``RULE_HASH``, and default behavior are unchanged.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "22d1f016cb3d"
ALLOWED_BOUNDARY_PALETTES = ("ends1_edges4", "ends4_edges1")
DEFAULT_BOUNDARY_PALETTE = "ends1_edges4"
PROTOTYPE_VERSION = "1.1.0"
DIFFICULTY = "medium"
DEFAULT_DEMO_COUNT = 4
DEFAULT_QUERY_COUNT = 1
EVIDENCE_DEMO_COUNT = 4
EVIDENCE_QUERY_COUNT = 4
PAIR_SCHEDULE = (
    ("single_rectangle", 0),
    ("hollow_frame", 1),
    ("orthogonal_shape", 2),
    ("mixed_shapes", 3),
    ("punctured_rectangle", 4),
    ("two_rectangles", 5),
    ("border_rectangles", 6),
    ("decoy_colors", 7),
    ("thin_rectangles", 8),
    ("many_rectangles", 9),
)
PROTOTYPE_DIR = Path(__file__).resolve().parent
RULE_DIR = PROTOTYPE_DIR / "racket"

_CANONICAL_END_CLAUSE = "((and (not h-both) (not v-both)) 1)"
_SWAPPED_END_CLAUSE = "((and (not h-both) (not v-both)) 4)"
_CANONICAL_EDGE_CLAUSE = "(else 4)"
_SWAPPED_EDGE_CLAUSE = "(else 1)"


def _validate_boundary_palette(boundary_palette: str) -> str:
    if (
        not isinstance(boundary_palette, str)
        or boundary_palette not in ALLOWED_BOUNDARY_PALETTES
    ):
        raise ValueError(
            "boundary_palette must be one of "
            f"{ALLOWED_BOUNDARY_PALETTES}, got {boundary_palette!r}"
        )
    return boundary_palette


def choose_boundary_palette(seed: int) -> str:
    """Choose one hidden setting for the complete episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return ALLOWED_BOUNDARY_PALETTES[seed % len(ALLOWED_BOUNDARY_PALETTES)]


def normalized_hash(source: str) -> str:
    """Return the repository's 12-hex whitespace-normalized rule hash."""
    return hashlib.sha256(" ".join(source.split()).encode("utf-8")).hexdigest()[:12]


def _canonical_source(*, root: Path) -> str:
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(f"{TASK_ID}: canonical program_solution not found")


def _swapped_source(canonical: str) -> str:
    replacements = (
        (_CANONICAL_END_CLAUSE, _SWAPPED_END_CLAUSE, "end-color clause"),
        (_CANONICAL_EDGE_CLAUSE, _SWAPPED_EDGE_CLAUSE, "edge-color clause"),
    )
    for old, new, label in replacements:
        count = canonical.count(old)
        if count != 1:
            raise ValueError(f"expected exactly one canonical {label}, found {count}")
        canonical = canonical.replace(old, new)
    return canonical


def racket_source(boundary_palette: str, *, root: Path | str) -> str:
    """Return one complete executable Racket rule for a bounded setting."""
    mode = _validate_boundary_palette(boundary_palette)
    canonical = _canonical_source(root=Path(root))
    return canonical if mode == DEFAULT_BOUNDARY_PALETTE else _swapped_source(canonical)


def racket_sha256(boundary_palette: str, *, root: Path | str) -> str:
    return hashlib.sha256(
        racket_source(boundary_palette, root=root).encode("utf-8")
    ).hexdigest()


def rule_path(boundary_palette: str) -> Path:
    return RULE_DIR / f"{_validate_boundary_palette(boundary_palette)}.rkt"


def materialize_rules(*, root: Path | str) -> dict[str, str]:
    """Write exact complete sources and return their raw SHA-256 hashes."""
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for mode in ALLOWED_BOUNDARY_PALETTES:
        source = racket_source(mode, root=root)
        rule_path(mode).write_text(source, encoding="utf-8")
        hashes[mode] = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return hashes


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty rectangular list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def python_transform(
    grid: list[list[int]], boundary_palette: str
) -> list[list[int]]:
    """Independent assertion mirror; exact Racket execution remains authority."""
    height, width = _validate_grid(grid)
    mode = _validate_boundary_palette(boundary_palette)
    end_color, edge_color = (1, 4) if mode == "ends1_edges4" else (4, 1)
    output = copy.deepcopy(grid)
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5:
                continue
            horizontal = (
                col > 0
                and col + 1 < width
                and grid[row][col - 1] == grid[row][col + 1] == 5
            )
            vertical = (
                row > 0
                and row + 1 < height
                and grid[row - 1][col] == grid[row + 1][col] == 5
            )
            if horizontal and vertical:
                output[row][col] = 2
            elif not horizontal and not vertical:
                output[row][col] = end_color
            else:
                output[row][col] = edge_color
    return output


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC literal: {value!r}")
    return str(value)


def _callable_racket_source(source: str) -> str:
    stripped = source.strip()
    prefix = "(rule! "
    if not stripped.startswith(prefix) or not stripped.endswith(")"):
        raise ValueError("expected a plain (rule! <lambda>) program")
    callable_source = stripped[len(prefix) : -1].strip()
    if not callable_source.startswith("(lambda "):
        raise ValueError("prototype rule body must be a lambda")
    return callable_source


def _racket_outputs(
    source: str, grids: list[list[list[int]]]
) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketBridge

    callable_source = _callable_racket_source(source)
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define prototype-rule {callable_source})")
        result = bridge.eval_text(f"(map prototype-rule '{_racket_literal(grids)})")
    if not isinstance(result, list) or len(result) != len(grids):
        raise RuntimeError("unexpected Racket result shape")
    return result


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_pair_counts(demo_count: Any, query_count: Any) -> tuple[int, int]:
    for name, value in (("demo_count", demo_count), ("query_count", query_count)):
        if type(value) is not int:
            raise TypeError(f"{name} must be a literal integer (not bool)")
        if value < 1:
            raise ValueError(f"{name} must be positive")
    requested = demo_count + query_count
    if requested > len(PAIR_SCHEDULE):
        raise ValueError(
            f"requested {requested} pairs but only {len(PAIR_SCHEDULE)} "
            "distinct schedule rows are available"
        )
    return demo_count, query_count


def build_episode(
    *,
    root: Path | str,
    seed: int,
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Build one fixed-setting episode with independent train/test counts."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    demo_count, query_count = _validate_pair_counts(demo_count, query_count)
    root = Path(root).resolve()
    mode = choose_boundary_palette(seed)
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    profile_indices = PAIR_SCHEDULE[: demo_count + query_count]
    pairs = []
    for profile, index in profile_indices:
        grid = module.generate(
            seed,
            index,
            difficulty=DIFFICULTY,
            scene_profile=profile,
        )
        pairs.append(
            {
                "scene_profile": profile,
                "sample_index": index,
                "input": copy.deepcopy(grid),
                "output": python_transform(grid, mode),
            }
        )
    return {
        "schema": "arcpuzzles-parametric-boundary-palette-episode-v2",
        "status": "prototype",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": DIFFICULTY,
        "parameter": {"boundary_palette": mode},
        "selected_generator_path": str(source_path.relative_to(root)),
        "selected_generator_sha256": source_sha,
        "demo_count": demo_count,
        "query_count": query_count,
        "pair_schedule_capacity": len(PAIR_SCHEDULE),
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Retain demonstrations but hide the parameter, source, and query answer."""
    return {
        "schema": "arcpuzzles-parametric-boundary-palette-public-v1",
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def plan_public_exports(
    challenges: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return a duplicate-safe public write plan sorted by visible-content ID."""
    if type(challenges) is not dict or not challenges:
        raise ValueError("challenges must be a nonempty private-key mapping")
    rows: list[dict[str, Any]] = []
    seen_ids: dict[str, str] = {}
    for private_key, challenge in challenges.items():
        if type(private_key) is not str or not private_key:
            raise ValueError("public export private keys must be nonempty strings")
        payload = public_challenge_bytes(challenge)
        public_id = public_challenge_id(challenge)
        previous = seen_ids.get(public_id)
        if previous is not None:
            raise ValueError(
                "duplicate public payload for private keys "
                f"{previous!r} and {private_key!r}"
            )
        seen_ids[public_id] = private_key
        rows.append(
            {
                "private_key": private_key,
                "public_id": public_id,
                "filename": f"challenge-{public_id}.json",
                "payload": payload,
            }
        )
    return sorted(rows, key=lambda row: row["public_id"])


def write_public_exports(
    directory: Path | str,
    challenges: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Write a complete batch only after duplicate-safe sorted planning."""
    plan = plan_public_exports(challenges)
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    for row in plan:
        (destination / row["filename"]).write_bytes(row["payload"])
    return plan


def _racket_runtime_metadata() -> dict[str, Any]:
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError(
            "racket executable not found; run through review.py run or run_with_racket.py"
        )
    path = Path(executable).resolve()
    return {
        "executable": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def build_report(
    *,
    root: Path | str,
    seeds: dict[str, int] | None = None,
    demo_count: int = EVIDENCE_DEMO_COUNT,
    query_count: int = EVIDENCE_QUERY_COUNT,
) -> dict[str, Any]:
    """Execute both exact Racket settings and retain bounded evidence."""
    root = Path(root).resolve()
    demo_count, query_count = _validate_pair_counts(demo_count, query_count)
    seeds = dict(seeds or {"ends1_edges4": 18, "ends4_edges1": 19})
    if set(seeds) != set(ALLOWED_BOUNDARY_PALETTES):
        raise ValueError(
            f"seeds must have exactly keys {ALLOWED_BOUNDARY_PALETTES}"
        )
    for mode, seed in seeds.items():
        selected = choose_boundary_palette(seed)
        if selected != mode:
            raise ValueError(f"seed {seed} selects {selected!r}, not {mode!r}")

    module, selected_path, selected_sha = load_selected_generator(TASK_ID, root=root)
    sources = {
        mode: racket_source(mode, root=root)
        for mode in ALLOWED_BOUNDARY_PALETTES
    }
    if sources[DEFAULT_BOUNDARY_PALETTE] != _canonical_source(root=root):
        raise AssertionError("default setting is not byte-exact canonical source")
    if normalized_hash(sources[DEFAULT_BOUNDARY_PALETTE]) != module.RULE_HASH:
        raise AssertionError("default prototype no longer matches selected RULE_HASH")
    for mode, source in sources.items():
        retained = rule_path(mode).read_text(encoding="utf-8")
        if retained != source:
            raise AssertionError(f"retained {mode}.rkt differs from materialized rule")

    settings: dict[str, Any] = {}
    public: dict[str, Any] = {}
    all_pairs_disagree = True
    for mode in ALLOWED_BOUNDARY_PALETTES:
        alternative = (
            "ends4_edges1" if mode == "ends1_edges4" else "ends1_edges4"
        )
        episode = build_episode(
            root=root,
            seed=seeds[mode],
            demo_count=demo_count,
            query_count=query_count,
        )
        pairs = [*episode["train"], *episode["test"]]
        inputs = [pair["input"] for pair in pairs]
        racket_outputs = _racket_outputs(sources[mode], inputs)
        alternative_outputs = _racket_outputs(sources[alternative], inputs)
        python_outputs = [python_transform(grid, mode) for grid in inputs]
        if racket_outputs != python_outputs:
            raise AssertionError(f"{mode}: Python/Racket output mismatch")

        executed_pairs = []
        for offset, (pair, actual, rival) in enumerate(
            zip(pairs, racket_outputs, alternative_outputs)
        ):
            if actual != pair["output"]:
                raise AssertionError(f"{mode}: episode label mismatch at pair {offset}")
            disagreement = actual != rival
            all_pairs_disagree &= disagreement
            split = "train" if offset < len(episode["train"]) else "test"
            pair_index = offset if split == "train" else offset - len(episode["train"])
            executed_pairs.append(
                {
                    "split": split,
                    "pair_index": pair_index,
                    "scene_profile": pair["scene_profile"],
                    "sample_index": pair["sample_index"],
                    "input": pair["input"],
                    "racket_output": actual,
                    "alternative_boundary_palette": alternative,
                    "alternative_racket_output": rival,
                    "settings_disagree": disagreement,
                    "input_sha256": _digest(pair["input"]),
                    "output_sha256": _digest(actual),
                }
            )

        demo_disagreements = [
            row["settings_disagree"]
            for row in executed_pairs
            if row["split"] == "train"
        ]
        query_disagreements = [
            row["settings_disagree"]
            for row in executed_pairs
            if row["split"] == "test"
        ]
        if not demo_disagreements or not all(demo_disagreements):
            raise AssertionError(f"{mode}: not every retained demo refutes {alternative}")
        if not query_disagreements or not all(query_disagreements):
            raise AssertionError(f"{mode}: retained query does not require the parameter")

        settings[mode] = {
            "boundary_palette": mode,
            "is_canonical_default": mode == DEFAULT_BOUNDARY_PALETTE,
            "seed": seeds[mode],
            "difficulty": DIFFICULTY,
            "demo_count": demo_count,
            "query_count": query_count,
            "demonstration_profiles": [
                pair["scene_profile"] for pair in episode["train"]
            ],
            "query_profiles": [
                pair["scene_profile"] for pair in episode["test"]
            ],
            "racket_path": str(rule_path(mode).relative_to(root)),
            "racket_text": sources[mode],
            "racket_sha256": hashlib.sha256(sources[mode].encode("utf-8")).hexdigest(),
            "racket_rule_hash": normalized_hash(sources[mode]),
            "episode": episode,
            "executed_pairs": executed_pairs,
            "all_pairs_match_python_and_racket": True,
            "every_demo_refutes_alternative_setting": all(demo_disagreements),
            "query_requires_setting": all(query_disagreements),
        }
        public[mode] = public_challenge(episode)

    if not all_pairs_disagree:
        raise AssertionError("at least one retained pair does not distinguish palettes")

    return {
        "schema": "arcpuzzles-parametric-boundary-palette-evidence-v2",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "boundary_palette",
            "allowed_values": list(ALLOWED_BOUNDARY_PALETTES),
            "canonical_default": DEFAULT_BOUNDARY_PALETTE,
            "selection": "ALLOWED_BOUNDARY_PALETTES[seed % 2], once per episode",
            "input_constraints": (
                "Same lawful 22d1f016cb3d inputs; every retained pair contains "
                "both zero-pair and exactly-one-pair cells so the settings differ."
            ),
        },
        "invariants_across_settings": [
            "input scene, color-5 source cells, and all non-5 cells are unchanged",
            "the both-opposing-pairs interior class remains color 2",
            "only colors assigned to the zero-pair and exactly-one-pair classes swap",
            "one palette is fixed across all demonstrations and queries",
        ],
        "prototype_source_path": str(Path(__file__).resolve().relative_to(root)),
        "prototype_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "selected_generator_path": str(selected_path.relative_to(root)),
        "selected_generator_sha256": selected_sha,
        "racket_runtime": _racket_runtime_metadata(),
        "settings": settings,
        "public_challenges": public,
        "demo_count": demo_count,
        "query_count": query_count,
        "all_retained_pairs_distinguish_settings": all_pairs_disagree,
        "limits": [
            (
                f"Bounded evidence for canonical seed 18 and swapped seed 19 with "
                f"{demo_count} demonstrations and {query_count} queries per setting, "
                "not production approval."
            ),
            "The selected generator and canonical authority remain fixed to ends1_edges4.",
            "The retained demonstrations distinguish only the declared two-value palette rival.",
            "This prototype does not claim that every undeclared semantic rival is excluded.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    parser.add_argument("--canonical-seed", type=int, default=18)
    parser.add_argument("--swapped-seed", type=int, default=19)
    parser.add_argument("--demo-count", type=int, default=EVIDENCE_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=EVIDENCE_QUERY_COUNT)
    args = parser.parse_args()

    root = find_root(__file__)
    materialize_rules(root=root)
    report = build_report(
        root=root,
        seeds={
            "ends1_edges4": args.canonical_seed,
            "ends4_edges1": args.swapped_seed,
        },
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    report["execution"] = {"argv": list(sys.argv), "cwd": os.getcwd()}

    if args.write_public is not None:
        export_plan = write_public_exports(
            args.write_public,
            report["public_challenges"],
        )
        report["public_exports"] = [
            {
                "private_key": row["private_key"],
                "public_id": row["public_id"],
                "filename": row["filename"],
                "sha256": hashlib.sha256(row["payload"]).hexdigest(),
                "bytes": len(row["payload"]),
            }
            for row in export_plan
        ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "status": report["status"],
                "parameter": report["parameter"],
                "all_retained_pairs_distinguish_settings": report[
                    "all_retained_pairs_distinguish_settings"
                ],
                "settings": {
                    mode: {
                        "seed": setting["seed"],
                        "racket_sha256": setting["racket_sha256"],
                        "racket_rule_hash": setting["racket_rule_hash"],
                        "every_demo_refutes_alternative_setting": setting[
                            "every_demo_refutes_alternative_setting"
                        ],
                        "query_requires_setting": setting["query_requires_setting"],
                    }
                    for mode, setting in report["settings"].items()
                },
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
