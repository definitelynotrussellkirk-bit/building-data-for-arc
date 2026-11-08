#!/usr/bin/env python3
"""Proposed task-local mirror-side episodes; never canonical production API.

The original/default program appends the horizontal reflection on the right.
The one alternative prepends the same reflection on the left.  Inputs are drawn
independently of the hidden rule, and every output label is produced by the
included Racket verifier rather than a Python mirror.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random

from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "19158f03ecb2"
VERSION = "prototype-1"
MIRROR_SIDES = ("right", "left")
DEFAULT_MIRROR_SIDE = "right"
N_TRAIN = 3
N_TEST = 1

LEFT_PROGRAM = "(rule! (lambda (g) (hconcat (flip-lr g) g)))"


def sha256(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def grid_hash(grid) -> str:
    return sha256(json.dumps(grid, separators=(",", ":")))


def validate_mirror_side(mirror_side: str) -> str:
    if type(mirror_side) is not str or mirror_side not in MIRROR_SIDES:
        raise ValueError("mirror_side must be exactly 'right' or 'left'")
    return mirror_side


def _rng(seed: int, stream: str) -> random.Random:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    return random.Random(int(sha256(f"{TASK_ID}/{VERSION}/{seed}/{stream}"), 16))


def choose_mirror_side(seed: int, mirror_side: str | None = None) -> str:
    """Choose the hidden rule once per episode from an independent stream."""
    if mirror_side is not None:
        return validate_mirror_side(mirror_side)
    return _rng(seed, "hidden-rule").choice(MIRROR_SIDES)


def canonical_program(*, root: Path) -> str:
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one unambiguous canonical program, found {len(programs)}")
    return programs.pop()


def rule_program(
    mirror_side: str = DEFAULT_MIRROR_SIDE,
    *,
    root: Path,
) -> str:
    validate_mirror_side(mirror_side)
    return canonical_program(root=root) if mirror_side == "right" else LEFT_PROGRAM


def _is_lr_symmetric(grid) -> bool:
    return all(row == list(reversed(row)) for row in grid)


def sample_input(seed: int, pair_index: int):
    """Return a dense, asymmetric grid shared by both parameter settings.

    The bounded sampler deliberately makes every pair a distinguishing witness:
    left-first and right-first concatenation differ whenever the source is not
    horizontally symmetric.  This is prototype evidence, not a production
    distribution claim.
    """
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer (not bool)")
    rng = _rng(seed, f"input/{pair_index}")
    h = rng.randint(3, 9)
    w = rng.randint(3, 9)
    palette_size = rng.randint(2, min(6, h * w))
    palette = rng.sample(range(10), palette_size)
    grid = [[rng.choice(palette) for _ in range(w)] for _ in range(h)]

    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    for color, (r, c) in zip(palette, cells):
        grid[r][c] = color

    if _is_lr_symmetric(grid):
        old = grid[0][-1]
        grid[0][-1] = next(color for color in palette if color != grid[0][0])
        # Keep every sampled color present if the changed cell was its sole use.
        if old not in {value for row in grid for value in row}:
            r, c = cells[-1]
            grid[r][c] = old
        if _is_lr_symmetric(grid):
            grid[-1][0] = next(color for color in palette if color != grid[-1][-1])
    return grid


def validate_input(grid) -> list[str]:
    try:
        grid = normalize_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (3 <= h <= 9 and 3 <= w <= 9):
        errors.append(f"prototype dimensions must be 3..9, got {h}x{w}")
    colors = {value for row in grid for value in row}
    if not (2 <= len(colors) <= 6):
        errors.append(f"prototype palette must contain 2..6 colors, got {len(colors)}")
    if _is_lr_symmetric(grid):
        errors.append("prototype inputs must be LR-asymmetric to distinguish mirror placement")
    return errors


def execute_program(program: str, inputs: list, *, train_pairs: list | None = None) -> dict:
    """Execute exact Racket source through the public isolated verifier API."""
    from arc_repl.isolated_verifier import Limits, verify_candidate

    if not 1 <= len(inputs) <= 120:
        raise ValueError("execution batch must contain 1..120 inputs")
    labeled = (
        train_pairs
        if train_pairs is not None
        else [{"input": [[0]], "output": [[0, 0]]}]
    )
    task = {"train": deepcopy(labeled), "test": [{"input": deepcopy(g)} for g in inputs]}
    return verify_candidate(
        task,
        program,
        racket_path=os.environ.get("RACKET_PATH", ""),
        limits=Limits(max_pairs=128),
    )


def _require_outputs(receipt: dict) -> list:
    if receipt.get("status") != "pass":
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt["test_outputs"]


def assemble_episode(seed: int, mirror_side: str, inputs: list, outputs: list, program: str) -> dict:
    validate_mirror_side(mirror_side)
    if len(inputs) != N_TRAIN + N_TEST or len(outputs) != len(inputs):
        raise ValueError("an episode requires exactly three demonstrations and one query")
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(inputs, outputs)
    ]
    return {
        "train": pairs[:N_TRAIN],
        "test": pairs[N_TRAIN:],
        "program": program,
        "meta": {
            "status": "prototype",
            "task_id": TASK_ID,
            "version": VERSION,
            "seed": seed,
            "parameters": {"mirror_side": mirror_side},
            "program_sha256": sha256(program),
            "label_backend": "racket",
            "demonstration_count": N_TRAIN,
            "query_count": N_TEST,
        },
    }


def generate_episode(
    seed: int,
    *,
    mirror_side: str | None = None,
    root: Path | None = None,
):
    root = find_root(__file__) if root is None else Path(root)
    selected = choose_mirror_side(seed, mirror_side)
    inputs = [sample_input(seed, index) for index in range(N_TRAIN + N_TEST)]
    program = rule_program(selected, root=root)
    receipt = execute_program(program, inputs)
    episode = assemble_episode(seed, selected, inputs, _require_outputs(receipt), program)
    return episode, receipt


def public_challenge(episode: dict) -> dict:
    """Whitelist projection: omit seed, parameter, source, and query output."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def parameter_teachability(outputs: dict[str, list], selected: str) -> dict:
    """Check the complete declared two-setting rival set and all holdouts."""
    validate_mirror_side(selected)
    if set(outputs) != set(MIRROR_SIDES) or any(len(values) != 4 for values in outputs.values()):
        raise ValueError("teachability needs both settings on the same four inputs")
    truth = outputs[selected]
    rivals = []
    for alternative in MIRROR_SIDES:
        if alternative == selected:
            continue
        refuting = [
            index
            for index, (expected, rival) in enumerate(zip(truth, outputs[alternative]))
            if expected != rival
        ]
        rivals.append(
            {"mirror_side": alternative, "refuting_pair_indices": refuting}
        )
    rotations = []
    for query_index in range(4):
        demonstrations = [index for index in range(4) if index != query_index]
        survivors = [
            rival["mirror_side"]
            for rival in rivals
            if not set(demonstrations) & set(rival["refuting_pair_indices"])
        ]
        rotations.append(
            {
                "query_index": query_index,
                "demonstration_indices": demonstrations,
                "surviving_parameter_rivals": survivors,
                "identifiable": not survivors,
            }
        )
    return {
        "selected_mirror_side": selected,
        "rivals": rivals,
        "production": rotations[3],
        "rotations": rotations,
    }


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build_evidence(out: Path, *, seeds: int = 8) -> dict:
    if type(seeds) is not int or not 1 <= seeds <= 24:
        raise ValueError("seeds must be an integer in 1..24")
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)

    inputs = [pair["input"] for pair in canonical]
    identities = [
        {
            "origin": "canonical",
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
        }
        for pair in canonical
    ]
    for seed in range(seeds):
        for pair_index in range(4):
            grid = sample_input(seed, pair_index)
            errors = validate_input(grid)
            if errors:
                raise ValueError(f"seed {seed}, pair {pair_index}: {errors}")
            inputs.append(grid)
            identities.append(
                {"origin": "prototype", "seed": seed, "pair_index": pair_index}
            )

    executions = {
        "schema": "mirror-side-racket-executions-v1",
        "status": "prototype",
        "inputs": [
            {**identity, "input": grid, "input_sha256": grid_hash(grid)}
            for identity, grid in zip(identities, inputs)
        ],
        "programs": {},
    }
    programs: dict[str, str] = {}
    outputs: dict[str, list] = {}
    for side in MIRROR_SIDES:
        program = rule_program(side, root=root)
        programs[side] = program
        receipt = execute_program(program, inputs)
        executions["programs"][side] = {
            "parameters": {"mirror_side": side},
            "program": program,
            "program_sha256": sha256(program),
            "execution": receipt,
        }
        # Persist before requiring success so genuine runtime failures survive.
        _write_json(out / "racket-executions.private.json", executions)
        outputs[side] = _require_outputs(receipt)

    canonical_matches = [
        outputs[DEFAULT_MIRROR_SIDE][index] == pair["output"]
        for index, pair in enumerate(canonical)
    ]
    episodes = []
    lessons = []
    for seed in range(seeds):
        start = len(canonical) + seed * 4
        per_setting = {
            side: outputs[side][start : start + 4] for side in MIRROR_SIDES
        }
        for side in MIRROR_SIDES:
            lesson = parameter_teachability(per_setting, side)
            lessons.append({"seed": seed, **lesson})
            if seed == 0:
                episodes.append(
                    assemble_episode(
                        seed,
                        side,
                        inputs[start : start + 4],
                        per_setting[side],
                        programs[side],
                    )
                )

    _write_json(out / "episodes.private.json", episodes)
    for suffix, episode in zip(("right", "left"), episodes):
        _write_json(out / f"challenge-{suffix}.public.json", public_challenge(episode))

    source = Path(__file__).resolve()
    owned_files = [
        source,
        source.with_name("README.md"),
        root / "generators" / TASK_ID / "tests/test_parametric.py",
    ]
    report = {
        "schema": "mirror-side-prototype-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "parameters": {
            "mirror_side": {
                "allowed": list(MIRROR_SIDES),
                "default": DEFAULT_MIRROR_SIDE,
                "selection": "once per deterministic episode seed",
            }
        },
        "invariant_reasoning": [
            "reflect the complete input left-to-right",
            "concatenate the original and reflected grids horizontally",
            "infer from demonstrations which side receives the reflected copy",
        ],
        "input_constraints": {
            "shared_across_settings": True,
            "dimensions": "3..9 by 3..9",
            "palette": "2..6 ARC colors",
            "distinguishing_filter": "every input is LR-asymmetric",
        },
        "source_sha256": {
            path.relative_to(root).as_posix(): sha256(path.read_bytes())
            for path in owned_files
        },
        "canonical_rule_sha256": sha256(programs[DEFAULT_MIRROR_SIDE]),
        "program_sha256": {side: sha256(program) for side, program in programs.items()},
        "selected_generator_dependency": False,
        "canonical_reference_unchanged": True,
        "canonical_labeled_pairs": len(canonical),
        "canonical_matches": sum(canonical_matches),
        "racket_label_count": sum(len(values) for values in outputs.values()),
        "execution_canaries": len(MIRROR_SIDES),
        "census": {
            "seeds": list(range(seeds)),
            "settings_per_seed": len(MIRROR_SIDES),
            "episodes": len(lessons),
            "demonstrations_per_episode": N_TRAIN,
            "queries_per_episode": N_TEST,
            "production_identifiable": sum(
                lesson["production"]["identifiable"] for lesson in lessons
            ),
            "rotations": 4 * len(lessons),
            "rotations_identifiable": sum(
                rotation["identifiable"]
                for lesson in lessons
                for rotation in lesson["rotations"]
            ),
        },
        "seeded_parameter_draws": [
            {"seed": seed, "mirror_side": choose_mirror_side(seed)}
            for seed in range(seeds)
        ],
        "lessons": lessons,
        "distinct_settings_witness": {
            "input_index": len(canonical),
            "seed": 0,
            "pair_index": 0,
            "outputs_differ": outputs["right"][len(canonical)]
            != outputs["left"][len(canonical)],
        },
        "public_files": {
            "challenge-right.public.json": {"private_episode_index": 0},
            "challenge-left.public.json": {"private_episode_index": 1},
        },
        "evidence": [
            "racket-executions.private.json",
            "episodes.private.json",
            "challenge-right.public.json",
            "challenge-left.public.json",
        ],
        "limitations": [
            "Proposed task-local extension; not a production parametric API or approval.",
            "Measured only the declared left/right rival pair and bounded seeds.",
            "Every sampled input is deliberately asymmetric; unfiltered symmetric lessons cannot identify placement.",
            "The sampler is independent of the selected generator and does not claim its full distribution.",
            "The right setting uses byte-exact canonical source; left is a separate proposed rule.",
        ],
    }
    report["passed"] = (
        all(canonical_matches)
        and report["distinct_settings_witness"]["outputs_differ"]
        and report["census"]["production_identifiable"] == len(lessons)
        and report["census"]["rotations_identifiable"] == 4 * len(lessons)
    )
    _write_json(out / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seeds", type=int, default=8, help="bounded census seeds 0..N-1")
    args = parser.parse_args()
    report = build_evidence(args.out, seeds=args.seeds)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "canonical_matches": report["canonical_matches"],
                "racket_label_count": report["racket_label_count"],
                "census": report["census"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
