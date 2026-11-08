"""Runnable prototype for a bounded ``stamp_mask`` rule parameter.

This module never changes the selected production generator or canonical rule.
It instantiates two exact Racket programs, samples the parameter once per
lesson, labels all examples with the protected Racket verifier, and emits a
public challenge whose query answer and chosen parameter remain hidden.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "0f5fbe0de38e"
STAMP_MASKS = ("fill_cells", "template_holes")
DEFAULT_STAMP_MASK = "fill_cells"
EPISODE_SEEDS = (0, 1)
N_TRAIN = 3
N_TEST = 1

_CANONICAL_MASK_BLOCK = """     (define fill-cells
       (filter (lambda (p) (= (third p) fill-color)) template-cells))"""
_HOLE_MASK_BLOCK = """     (define fill-cells
       (for*/list ((r (range 0 th))
                   (c (range 0 tw))
                   #:when (not (for/or ((p (in-list template-cells)))
                                (and (= (first p) r)
                                     (= (second p) c)))))
         (list r c fill-color)))"""

# These cases retain the original roles and placement reasoning while covering
# unit/scaled, single/multiple, same/opposite/mixed D4 placements.
_FIXTURE_CASES: tuple[dict[str, Any], ...] = (
    {
        "grid_h": 22,
        "grid_w": 22,
        "bg_color": 0,
        "fill_color": 8,
        "marker_a_color": 2,
        "marker_b_color": 6,
        "template_profile": "ring6_anti",
        "lesson_profile": "unit_single",
        "orientation_profile": "same",
    },
    {
        "grid_h": 22,
        "grid_w": 22,
        "bg_color": 9,
        "fill_color": 1,
        "marker_a_color": 4,
        "marker_b_color": 7,
        "template_profile": "wedge5_main",
        "lesson_profile": "scaled2_single",
        "orientation_profile": "opposite",
    },
    {
        "grid_h": 22,
        "grid_w": 22,
        "bg_color": 5,
        "fill_color": 3,
        "marker_a_color": 1,
        "marker_b_color": 8,
        "template_profile": "plus5_main",
        "lesson_profile": "mixed_1_2",
        "orientation_profile": "mixed",
    },
    {
        "grid_h": 22,
        "grid_w": 22,
        "bg_color": 0,
        "fill_color": 8,
        "marker_a_color": 2,
        "marker_b_color": 6,
        "template_profile": "cross4_anti",
        "lesson_profile": "mixed_1_2_3",
        "orientation_profile": "mixed",
    },
)

LIMITATIONS = (
    "Prototype only: neither variant approval nor training approval is implied.",
    "Two settings and two complete lessons are exercised; this is not an exhaustive induction proof.",
    "Inputs use the selected generator's documented 3x3 sparse-template domain.",
    "The alternative paints only background holes inside the template bbox; marker ports remain anchors.",
)


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return _sha_bytes(payload.encode())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def canonical_program(root: Path | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root)
    matches: list[dict[str, Any]] = []
    with canonical_path(root).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}, found {len(matches)}")
    program = matches[0].get("program_solution")
    if not isinstance(program, str) or not program.strip():
        raise ValueError("canonical row lacks a nonempty program_solution")
    return program


def instantiate(program: str, stamp_mask: str = DEFAULT_STAMP_MASK) -> str:
    """Instantiate one exact Racket rule while preserving the canonical default."""
    if stamp_mask not in STAMP_MASKS:
        raise ValueError(f"unsupported stamp_mask {stamp_mask!r}; expected one of {STAMP_MASKS}")
    if program.count(_CANONICAL_MASK_BLOCK) != 1:
        raise ValueError("canonical fill-cell block changed or is not unique")
    if stamp_mask == DEFAULT_STAMP_MASK:
        return program
    return program.replace(_CANONICAL_MASK_BLOCK, _HOLE_MASK_BLOCK, 1)


def retained_rule_path(stamp_mask: str) -> Path:
    if stamp_mask not in STAMP_MASKS:
        raise ValueError(f"unsupported stamp_mask {stamp_mask!r}; expected one of {STAMP_MASKS}")
    return Path(__file__).resolve().parent / "rules" / f"stamp-mask-{stamp_mask}.rkt"


def choose_stamp_mask(seed: int) -> str:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    # One draw for the entire lesson; never redrawn for demos or query.
    return random.Random(seed).choice(STAMP_MASKS)


def fixture_inputs(seed: int, root: Path | None = None) -> tuple[list[list[list[int]]], list[dict[str, Any]], str]:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    root = find_root(__file__) if root is None else Path(root)
    generator, _path, generator_sha = load_selected_generator(TASK_ID, root=root)
    grids: list[list[list[int]]] = []
    provenance: list[dict[str, Any]] = []
    for pair_index, overrides in enumerate(_FIXTURE_CASES):
        draw_seed = 710_000 + seed * 100 + pair_index
        sample_index = 80 + pair_index
        grid = generator.generate(
            draw_seed,
            sample_index,
            difficulty="hard",
            **overrides,
        )
        errors = generator.self_check(grid)
        if errors:
            raise ValueError(
                f"selected generator rejected prototype input seed={seed} pair={pair_index}: {errors}"
            )
        observed = generator.observe_overrides(grid)
        if observed != overrides:
            raise ValueError(
                f"prototype override drift seed={seed} pair={pair_index}: {observed!r} != {overrides!r}"
            )
        grids.append(grid)
        provenance.append(
            {
                "episode_seed": seed,
                "pair_index": pair_index,
                "generator_seed": draw_seed,
                "sample_index": sample_index,
                "difficulty": "hard",
                "overrides": overrides,
                "input_sha256": _json_sha(grid),
            }
        )
    return grids, provenance, generator_sha


def _execution_canary(root: Path) -> list[list[int]]:
    """A no-marker input on which both settings are intentionally the identity."""
    generator, _path, _sha = load_selected_generator(TASK_ID, root=root)
    return generator.generate(799_999, 0, difficulty="easy", texture="no_markers")


def execute_program(program: str, inputs: list[list[list[int]]], *, root: Path) -> dict[str, Any]:
    """Execute an exact proposed program through the public Racket-only verifier."""
    from arc_repl.isolated_verifier import Limits, verify_candidate

    if not inputs:
        raise ValueError("at least one prototype input is required")
    canary = _execution_canary(root)
    task = {
        "train": [{"input": canary, "output": canary}],
        "test": [{"input": grid} for grid in inputs],
    }
    receipt = verify_candidate(
        task,
        program,
        racket_path=os.environ.get("RACKET_PATH", ""),
        limits=Limits(
            wall_seconds=120.0,
            step_seconds=12.0,
            cpu_seconds=90,
            memory_mb=2048,
            max_source_bytes=32768,
            max_output_bytes=4 * 1024 * 1024,
            max_grid_side=64,
            max_pairs=32,
        ),
    )
    if receipt.get("status") != "pass" or receipt.get("backend") != "racket":
        raise RuntimeError(
            "Racket execution failed: " + json.dumps(receipt, sort_keys=True, allow_nan=False)
        )
    outputs = receipt.get("test_outputs")
    if not isinstance(outputs, list) or len(outputs) != len(inputs):
        raise RuntimeError("Racket receipt returned an incomplete output batch")
    return receipt


def public_challenge(private: dict[str, Any]) -> dict[str, Any]:
    """Whitelist projection: hide parameter, program, seed, and query output."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in private["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in private["test"]],
    }


def _source_hashes(root: Path) -> dict[str, str]:
    here = Path(__file__).resolve()
    paths = [
        here,
        here.with_name("README.md"),
        root / "generators" / TASK_ID / "tests" / "test_parametric_stamp_mask.py",
        root / "generators" / TASK_ID / "generator.py",
        *(retained_rule_path(mask) for mask in STAMP_MASKS),
    ]
    return {
        path.relative_to(root).as_posix(): _sha_bytes(path.read_bytes())
        for path in paths
    }


def materialize(output: Path) -> dict[str, Any]:
    """Build two complete, source-bound episodes and retain exact Racket evidence."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    canonical = canonical_program(root)
    source_hashes = _source_hashes(root)

    programs: dict[str, str] = {}
    for stamp_mask in STAMP_MASKS:
        expected = instantiate(canonical, stamp_mask)
        retained = retained_rule_path(stamp_mask).read_text(encoding="utf-8")
        if retained != expected:
            raise ValueError(f"retained Racket source drift for stamp_mask={stamp_mask}")
        programs[stamp_mask] = retained
        rule_out = output / "private" / "rules" / f"stamp-mask-{stamp_mask}.rkt"
        rule_out.parent.mkdir(parents=True, exist_ok=True)
        rule_out.write_text(retained, encoding="utf-8")

    episode_inputs: list[list[list[int]]] = []
    episode_rows: list[dict[str, Any]] = []
    generator_hashes: set[str] = set()
    for seed in EPISODE_SEEDS:
        grids, provenance, generator_sha = fixture_inputs(seed, root)
        offset = len(episode_inputs)
        episode_inputs.extend(grids)
        episode_rows.append(
            {
                "seed": seed,
                "stamp_mask": choose_stamp_mask(seed),
                "offset": offset,
                "inputs": grids,
                "input_provenance": provenance,
            }
        )
        generator_hashes.add(generator_sha)
    if len(generator_hashes) != 1:
        raise ValueError(f"prototype inputs came from multiple generator hashes: {generator_hashes}")

    running_report: dict[str, Any] = {
        "schema": "stamp-mask-parametric-prototype-v1",
        "status": "running",
        "task_id": TASK_ID,
        "parameter": {
            "name": "stamp_mask",
            "allowed": list(STAMP_MASKS),
            "default": DEFAULT_STAMP_MASK,
            "selection": "one deterministic draw per complete episode",
        },
        "source_sha256": source_hashes,
        "selected_generator_sha256": next(iter(generator_hashes)),
        "canonical_program_sha256": _sha_bytes(canonical.encode()),
        "program_sha256": {
            stamp_mask: _sha_bytes(program.encode())
            for stamp_mask, program in programs.items()
        },
        "limitations": list(LIMITATIONS),
    }
    _write_json(output / "report.json", running_report)

    predictions: dict[str, list[list[list[int]]]] = {}
    receipts: dict[str, dict[str, Any]] = {}
    for stamp_mask in STAMP_MASKS:
        receipt = execute_program(programs[stamp_mask], episode_inputs, root=root)
        receipts[stamp_mask] = receipt
        predictions[stamp_mask] = receipt["test_outputs"]
        _write_json(
            output / "private" / "racket" / f"stamp-mask-{stamp_mask}.json",
            {
                "stamp_mask": stamp_mask,
                "program_sha256": _sha_bytes(programs[stamp_mask].encode()),
                "input_sha256": [_json_sha(grid) for grid in episode_inputs],
                "receipt": receipt,
            },
        )

    private_episodes: list[dict[str, Any]] = []
    for episode_index, row in enumerate(episode_rows):
        chosen = row["stamp_mask"]
        rival = next(mask for mask in STAMP_MASKS if mask != chosen)
        offset = row["offset"]
        chosen_outputs = predictions[chosen][offset : offset + N_TRAIN + N_TEST]
        rival_outputs = predictions[rival][offset : offset + N_TRAIN + N_TEST]
        pairs = [
            {"input": deepcopy(grid), "output": deepcopy(label)}
            for grid, label in zip(row["inputs"], chosen_outputs, strict=True)
        ]
        demo_differences = [
            index
            for index in range(N_TRAIN)
            if chosen_outputs[index] != rival_outputs[index]
        ]
        query_differs = chosen_outputs[N_TRAIN] != rival_outputs[N_TRAIN]
        rival_row = {
            "stamp_mask": rival,
            "status": "distinguished" if demo_differences else "ambiguous",
            "demo_differences": demo_differences,
            "query_differs": query_differs,
        }
        if not demo_differences:
            raise ValueError(
                f"episode seed={row['seed']} leaves rival {rival!r} ambiguous in demonstrations"
            )
        if not query_differs:
            raise ValueError(
                f"episode seed={row['seed']} query does not exercise stamp_mask distinction"
            )
        program_path = f"private/rules/stamp-mask-{chosen}.rkt"
        private = {
            "schema": "stamp-mask-private-episode-v1",
            "task_id": TASK_ID,
            "episode_index": episode_index,
            "seed": row["seed"],
            "parameters": {"stamp_mask": chosen},
            "parameter_sampling_unit": "episode",
            "program": programs[chosen],
            "program_path": program_path,
            "program_sha256": _sha_bytes(programs[chosen].encode()),
            "selected_generator_sha256": next(iter(generator_hashes)),
            "source_sha256": source_hashes,
            "label_authority": "arc_repl.isolated_verifier.verify_candidate; backend=racket",
            "input_provenance": row["input_provenance"],
            "train": pairs[:N_TRAIN],
            "test": pairs[N_TRAIN:],
            "rivals": [rival_row],
            "cross_setting_outputs": {
                mask: deepcopy(predictions[mask][offset : offset + N_TRAIN + N_TEST])
                for mask in STAMP_MASKS
            },
        }
        private_episodes.append(private)
        _write_json(output / "private" / f"episode-{episode_index}.json", private)
        _write_json(output / "public" / f"episode-{episode_index}.json", public_challenge(private))

    witness_outputs = {
        mask: predictions[mask][0]
        for mask in STAMP_MASKS
    }
    witness = {
        "input": episode_inputs[0],
        "input_sha256": _json_sha(episode_inputs[0]),
        "outputs": witness_outputs,
        "output_sha256": {mask: _json_sha(value) for mask, value in witness_outputs.items()},
        "outputs_distinct": witness_outputs[STAMP_MASKS[0]] != witness_outputs[STAMP_MASKS[1]],
    }
    if not witness["outputs_distinct"]:
        raise ValueError("cross-setting witness does not distinguish the declared parameter")
    _write_json(output / "private" / "cross-setting-witness.json", witness)
    _write_json(
        output / "private" / "execution-inputs.json",
        [
            {
                "input_index": index,
                "input": grid,
                "input_sha256": _json_sha(grid),
            }
            for index, grid in enumerate(episode_inputs)
        ],
    )

    settings_seen = sorted({episode["parameters"]["stamp_mask"] for episode in private_episodes})
    final_report = {
        **running_report,
        "status": "prototype",
        "default_program_exact": programs[DEFAULT_STAMP_MASK] == canonical,
        "canonical_reference_unchanged": True,
        "episode_count": len(private_episodes),
        "demonstrations_per_episode": N_TRAIN,
        "queries_per_episode": N_TEST,
        "settings_seen": settings_seen,
        "racket_label_count": len(private_episodes) * (N_TRAIN + N_TEST),
        "racket_rival_label_count": len(private_episodes) * (N_TRAIN + N_TEST),
        "racket_output_count": len(STAMP_MASKS) * len(episode_inputs),
        "execution_canary_count": len(STAMP_MASKS),
        "production_lessons_identifiable": sum(
            all(rival["status"] == "distinguished" for rival in episode["rivals"])
            for episode in private_episodes
        ),
        "query_distinctions": sum(
            all(rival["query_differs"] for rival in episode["rivals"])
            for episode in private_episodes
        ),
        "runtime": {
            "backend": "racket",
            "public_api": "arc_repl.isolated_verifier.verify_candidate",
            "racket_path": receipts[STAMP_MASKS[0]].get("binary"),
            "candidate_ids": {
                mask: receipts[mask].get("candidate_id") for mask in STAMP_MASKS
            },
        },
        "evidence": {
            "public": [f"public/episode-{index}.json" for index in range(len(private_episodes))],
            "private": [f"private/episode-{index}.json" for index in range(len(private_episodes))],
            "rules": [f"private/rules/stamp-mask-{mask}.rkt" for mask in STAMP_MASKS],
            "racket_receipts": [f"private/racket/stamp-mask-{mask}.json" for mask in STAMP_MASKS],
            "witness": "private/cross-setting-witness.json",
        },
        "scope": "two complete lessons, four pairs each, both proposed settings, exact Racket labels",
    }
    _write_json(output / "report.json", final_report)
    return final_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(materialize(args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
