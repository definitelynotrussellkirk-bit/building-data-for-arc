"""Task-local parametric prototype for the sliding-window counting rule.

This module is deliberately separate from the selected production generator.
It chooses two hidden rule parameters once per episode, materializes the exact
Racket rule for that setting, and derives every label by executing Racket.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_path, find_root


TASK_ID = "2f7883fbd26f"
WINDOW_SIZES = (2, 3)
TARGET_COLORS = (1, 2)
SETTINGS = tuple((window_size, target_color) for window_size in WINDOW_SIZES for target_color in TARGET_COLORS)
DEFAULT_SETTING = (2, 1)
BAR_LENGTH = 5
PAIR_COUNT = 4
TRAIN_COUNT = 3


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def canonical_program(root: Path | None = None) -> str:
    """Read the one canonical program for this task from the packet."""
    root = find_root(__file__) if root is None else Path(root)
    matches: list[dict] = []
    with canonical_path(root).open() as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}, found {len(matches)}")
    program = matches[0].get("program_solution")
    if not isinstance(program, str) or not program.startswith("(rule!"):
        raise ValueError("canonical row has no usable rule! program")
    return program


def _validate_setting(window_size: int, target_color: int) -> tuple[int, int]:
    if window_size not in WINDOW_SIZES:
        raise ValueError(f"window_size must be one of {WINDOW_SIZES}, got {window_size!r}")
    if target_color not in TARGET_COLORS:
        raise ValueError(f"target_color must be one of {TARGET_COLORS}, got {target_color!r}")
    return int(window_size), int(target_color)


def _offset_expr(base: str, offset: int) -> str:
    return base if offset == 0 else f"(+ {base} {offset})"


def _render_variant(window_size: int, target_color: int) -> str:
    """Render a nearby rule variant; default bytes come from canonical_program."""
    window_size, target_color = _validate_setting(window_size, target_color)
    bound = window_size - 1
    comparisons = []
    for dr in range(window_size):
        for dc in range(window_size):
            comparisons.append(
                f"(= {target_color} (at g {_offset_expr('r', dr)} {_offset_expr('c', dc)}))"
            )
    comparison_text = "\n                                     ".join(comparisons)
    return (
        "(rule! (lambda (g)\n"
        "         (let* ((h (rows g))\n"
        "                (w (cols g)))\n"
        f"           (let* ((n (for*/sum ((r (range 0 (- h {bound}))) (c (range 0 (- w {bound}))))\n"
        "                               (if (and\n"
        f"                                     {comparison_text})\n"
        "                                   1\n"
        "                                   0))))\n"
        f"             (encode-bar n {BAR_LENGTH} 1)))))"
    )


def instantiate(
    canonical: str,
    *,
    window_size: int = DEFAULT_SETTING[0],
    target_color: int = DEFAULT_SETTING[1],
) -> str:
    """Materialize one exact episode rule while preserving the default bytes."""
    setting = _validate_setting(window_size, target_color)
    if not isinstance(canonical, str) or not canonical.startswith("(rule!"):
        raise ValueError("canonical must be a rule! program string")
    if setting == DEFAULT_SETTING:
        return canonical
    return _render_variant(*setting)


def parameters(seed: int) -> dict[str, int]:
    """Draw a single rule setting once for an entire episode."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    window_size, target_color = random.Random(seed).choice(SETTINGS)
    return {"window_size": window_size, "target_color": target_color}


def first_seed_for_setting(setting: tuple[int, int]) -> int:
    """Return the first small seed selecting a requested setting."""
    if setting not in SETTINGS:
        raise ValueError(f"setting must be one of {SETTINGS}, got {setting!r}")
    for seed in range(10_000):
        params = parameters(seed)
        if (params["window_size"], params["target_color"]) == setting:
            return seed
    raise RuntimeError(f"could not find a seed for setting {setting!r}")


def _place_rectangle(
    grid: list[list[int]],
    *,
    top: int,
    left: int,
    height: int,
    width: int,
    color: int,
) -> None:
    if height < 1 or width < 1:
        raise ValueError("rectangle dimensions must be positive")
    for row in range(top, top + height):
        for col in range(left, left + width):
            if grid[row][col] != 0:
                raise ValueError("fixture rectangles must remain disjoint")
            grid[row][col] = color


def fixture_inputs(seed: int) -> list[list[list[int]]]:
    """Create four controlled inputs whose setting signatures are diagnostic.

    Each grid has one solid color-1 rectangle and one disjoint solid color-2
    rectangle.  Their dimensions make the four (window size, target color)
    settings yield distinct demonstration vectors.  Seeded orientation and
    placement vary surface layout without changing those signatures.
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    # (color-1 rectangle, color-2 rectangle).  The first three are demos.
    specs = (
        ((2, 3), (3, 3)),  # setting outputs: 2, 4, 0, 1
        ((3, 3), (2, 4)),  # setting outputs: 4, 3, 1, 0
        ((2, 4), (2, 2)),  # setting outputs: 3, 1, 0, 0
        ((3, 3), (2, 3)),  # query outputs:   4, 2, 1, 0
    )
    inputs: list[list[list[int]]] = []
    for index, (shape_one, shape_two) in enumerate(specs):
        rng = random.Random((seed + 1) * 1_000_003 + index * 97)
        h, w = 11, 13
        grid = [[0] * w for _ in range(h)]
        one_h, one_w = shape_one
        two_h, two_w = shape_two
        if rng.randrange(2):
            one_h, one_w = one_w, one_h
        if rng.randrange(2):
            two_h, two_w = two_w, two_h

        # Place color 1 in a 5x6 northwest zone and color 2 in a disjoint
        # 5x6 southeast zone.  Every allowed rectangle fits either zone.
        one_top = rng.randint(0, 5 - one_h)
        one_left = rng.randint(0, 6 - one_w)
        two_top = 6 + rng.randint(0, 5 - two_h)
        two_left = 7 + rng.randint(0, 6 - two_w)
        _place_rectangle(
            grid,
            top=one_top,
            left=one_left,
            height=one_h,
            width=one_w,
            color=1,
        )
        _place_rectangle(
            grid,
            top=two_top,
            left=two_left,
            height=two_h,
            width=two_w,
            color=2,
        )
        inputs.append(grid)
    return inputs


def _grid_literal(grid: list[list[int]]) -> str:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(not isinstance(value, int) or isinstance(value, bool) for row in grid for value in row):
        raise ValueError("grid cells must be integers")
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return "'(" + rows + ")"


def execute(grid: list[list[int]], program: str, bridge: RacketBridge) -> list[list[int]]:
    """Execute the exact materialized rule through the bundled Racket bridge."""
    callable_rule = strip_rule_wrapper(strip_line_comments(program))
    output = bridge.eval_text(f"({callable_rule} {_grid_literal(grid)})")
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(not isinstance(row, list) or len(row) != len(output[0]) for row in output)
    ):
        raise ValueError(f"Racket returned a non-rectangular grid: {output!r}")
    return output


def _generate_episode(
    seed: int,
    *,
    canonical: str,
    bridge: RacketBridge,
) -> dict:
    params = parameters(seed)
    chosen = (params["window_size"], params["target_color"])
    programs = {
        setting: instantiate(
            canonical,
            window_size=setting[0],
            target_color=setting[1],
        )
        for setting in SETTINGS
    }
    inputs = fixture_inputs(seed)
    all_outputs = [
        {setting: execute(grid, program, bridge) for setting, program in programs.items()}
        for grid in inputs
    ]
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(outputs[chosen])}
        for grid, outputs in zip(inputs, all_outputs)
    ]

    rivals: list[dict] = []
    demonstrations_refute: list[dict[str, int]] = []
    for rival in SETTINGS:
        if rival == chosen:
            continue
        differences = [
            index
            for index in range(TRAIN_COUNT)
            if all_outputs[index][rival] != all_outputs[index][chosen]
        ]
        query_differs = all_outputs[TRAIN_COUNT][rival] != all_outputs[TRAIN_COUNT][chosen]
        status = "distinguished" if differences else "ambiguous"
        rivals.append(
            {
                "window_size": rival[0],
                "target_color": rival[1],
                "demo_differences": differences,
                "query_differs": query_differs,
                "status": status,
            }
        )
        if differences:
            demonstrations_refute.append(
                {"window_size": rival[0], "target_color": rival[1]}
            )
        if query_differs and not differences:
            raise ValueError(
                f"query depends on unresolved rule setting {rival!r} against {chosen!r}"
            )

    program = programs[chosen]
    return {
        "schema": "2f7883fbd26f-parametric-window-rule-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": params,
        "program": program,
        "program_sha256": _sha256(program.encode()),
        "canonical_program_sha256": _sha256(canonical.encode()),
        "default_program_exact": chosen != DEFAULT_SETTING or program == canonical,
        "train": pairs[:TRAIN_COUNT],
        "test": pairs[TRAIN_COUNT:],
        "rivals": rivals,
        "demonstrations_refute": demonstrations_refute,
        "label_authority": "bundled Racket bridge executing the exact materialized rule",
        "executed_setting_outputs": PAIR_COUNT * len(SETTINGS),
    }


def generate_episode(
    seed: int,
    *,
    canonical: str | None = None,
    bridge: RacketBridge | None = None,
) -> dict:
    """Generate one complete episode with one hidden setting drawn from seed."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    canonical = canonical_program() if canonical is None else canonical
    if bridge is not None:
        return _generate_episode(seed, canonical=canonical, bridge=bridge)
    with RacketBridge() as own_bridge:
        return _generate_episode(seed, canonical=canonical, bridge=own_bridge)


def public_challenge(private_episode: dict) -> dict:
    """Strip rule metadata and query labels from an authoring episode."""
    return {
        "train": deepcopy(private_episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in private_episode["test"]],
    }


def materialize(output: Path) -> dict:
    """Write one complete episode per setting plus a shared differing witness."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    canonical = canonical_program(root)
    prototype_dir = Path(__file__).resolve().parent
    source_paths = [
        prototype_dir / "prototype.py",
        prototype_dir / "README.md",
        prototype_dir.parents[1] / "tests" / "test_parametric_window_rule.py",
    ]
    source_sha256 = {
        str(path.relative_to(root)): _sha256(path.read_bytes())
        for path in source_paths
        if path.is_file()
    }

    episodes: list[dict] = []
    with RacketBridge() as bridge:
        for setting in SETTINGS:
            seed = first_seed_for_setting(setting)
            episode = generate_episode(seed, canonical=canonical, bridge=bridge)
            observed = (
                episode["parameters"]["window_size"],
                episode["parameters"]["target_color"],
            )
            if observed != setting:
                raise AssertionError(f"seed {seed} selected {observed}, expected {setting}")
            episode["prototype_source_sha256"] = source_sha256
            episode["runtime_identity"] = bridge.runtime_identity
            episodes.append(episode)

        witness_input = fixture_inputs(17)[0]
        witness_outputs = {
            f"window_size={window_size},target_color={target_color}": execute(
                witness_input,
                instantiate(
                    canonical,
                    window_size=window_size,
                    target_color=target_color,
                ),
                bridge,
            )
            for window_size, target_color in SETTINGS
        }
        runtime_identity = bridge.runtime_identity

    if len({json.dumps(value, sort_keys=True) for value in witness_outputs.values()}) != len(SETTINGS):
        raise AssertionError("shared witness does not distinguish every setting")

    for index, episode in enumerate(episodes):
        _write_json(output / "public" / f"episode-{index}.json", public_challenge(episode))
        _write_json(output / "private" / f"episode-{index}.json", episode)
        (output / "private" / f"episode-{index}.rkt").write_text(episode["program"])

    witness = {
        "input": witness_input,
        "outputs": witness_outputs,
        "settings": [
            {"window_size": window_size, "target_color": target_color}
            for window_size, target_color in SETTINGS
        ],
        "label_authority": "bundled Racket bridge",
    }
    _write_json(output / "private" / "witness.json", witness)

    report = {
        "status": "prototype",
        "task_id": TASK_ID,
        "parameters": {
            "window_size": list(WINDOW_SIZES),
            "target_color": list(TARGET_COLORS),
        },
        "default": {
            "window_size": DEFAULT_SETTING[0],
            "target_color": DEFAULT_SETTING[1],
        },
        "default_program_exact": instantiate(canonical) == canonical,
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": TRAIN_COUNT, "test": PAIR_COUNT - TRAIN_COUNT},
        "executed_rule_applications": len(episodes) * PAIR_COUNT * len(SETTINGS) + len(SETTINGS),
        "all_labels_and_rivals_executed_in_racket": True,
        "all_demonstrations_refute_other_declared_settings": all(
            len(episode["demonstrations_refute"]) == len(SETTINGS) - 1
            for episode in episodes
        ),
        "canonical_program_sha256": _sha256(canonical.encode()),
        "source_sha256": source_sha256,
        "runtime_identity": runtime_identity,
        "limitations": [
            "Two window sizes and two target colors only; output remains a length-five color-1 bar.",
            "Controlled 11x13 zero-background fixtures with one solid rectangle of each candidate color.",
            "Four retained seeds and one query per episode; finite evidence against the three declared settings.",
            "Separate authoring prototype only; it does not modify or approve the production generator.",
        ],
    }
    _write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = materialize(args.out)
    print(
        json.dumps(
            {
                "status": report["status"],
                "complete_episodes": report["complete_episodes"],
                "executed_rule_applications": report["executed_rule_applications"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
