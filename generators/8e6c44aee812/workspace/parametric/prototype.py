#!/usr/bin/env python3
"""Native episode-level output-scale prototype for ARC task 8e6c44aee812.

The selected production task remains fixed at output scale 2.  This separate
prototype chooses ``output_scale`` once per complete episode and preserves the
same diagonal extraction, padding removal, periodic sequence, and max-axis
staircase continuation.  A constructive two-example teaching core preserves
contiguous multiplicity and separated reappearances of both color roles.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any


HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
GENERATOR_PATH = TASK_DIR / "generator.py"
TASK_ID = "8e6c44aee812"

ALLOWED_OUTPUT_SCALES = (2, 3)
DEFAULT_OUTPUT_SCALE = 2
SETTINGS = ALLOWED_OUTPUT_SCALES
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

# Exact Catalog source, including comments and whitespace.  The alternative
# changes the two output multipliers while retaining the sequence dependency.
CANONICAL_PROGRAM = """(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; Each nested L-band is named by the main-diagonal cell it crosses.
         (diag (for/list ((i (range 0 (min h w))))
                 (at g i i)))
         ;; Trailing zero bands are padding; the nonzero prefix is the period.
         (active-diag
          (let loop ((d diag))
            (if (or (empty? d) (!= (last d) 0))
                d
                (loop (take d (- (length d) 1))))))
         (period (length active-diag))
         (oh (* h 2))
         (ow (* w 2)))
    ;; Continue the staircase in both axes by cycling the active diagonal.
    (build-grid oh ow (r c)
      (nth active-diag (remainder (max r c) period))))))"""


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "parametric_base_8e6c44aee812", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load selected generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GEN = _load_generator()


def _validate_output_scale(output_scale: int) -> None:
    if type(output_scale) is not int or output_scale not in ALLOWED_OUTPUT_SCALES:
        raise ValueError(
            f"output_scale must be one of {ALLOWED_OUTPUT_SCALES}, got {output_scale!r}"
        )


def _active_diagonal(grid: list[list[int]]) -> list[int]:
    diagonal = [grid[index][index] for index in range(min(len(grid), len(grid[0])))]
    while diagonal and diagonal[-1] == 0:
        diagonal.pop()
    return diagonal



def program_for(output_scale: int = DEFAULT_OUTPUT_SCALE) -> str:
    """Return the exact executable Racket rule for one proposed setting."""
    _validate_output_scale(output_scale)
    return (CANONICAL_PROGRAM.replace("(oh (* h 2))", f"(oh (* h {output_scale}))")
            .replace("(ow (* w 2))", f"(ow (* w {output_scale}))"))


def _settings(settings: Any) -> int:
    if type(settings) is not dict or set(settings) != {"output_scale"}:
        raise ValueError("settings must contain only output_scale")
    _validate_output_scale(settings["output_scale"])
    return settings["output_scale"]


def program(settings: dict[str, int]) -> str:
    """Native adapter program entry point; default source is byte-exact."""
    return program_for(_settings(settings))


def normalized_program_hash(output_scale: int = DEFAULT_OUTPUT_SCALE) -> str:
    normalized = " ".join(program_for(output_scale).split()).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _build_from_sequence(
    grid: list[list[int]],
    sequence: list[int],
    *,
    output_scale: int,
    metric: str = "max",
) -> list[list[int]]:
    out_h = output_scale * len(grid)
    out_w = output_scale * len(grid[0])

    def sequence_index(row: int, col: int) -> int:
        if metric == "max":
            return max(row, col)
        if metric == "row":
            return row
        if metric == "column":
            return col
        raise ValueError(f"unsupported metric: {metric!r}")

    return [
        [sequence[sequence_index(row, col) % len(sequence)] for col in range(out_w)]
        for row in range(out_h)
    ]


def _run_lengths(values: list[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    for value in values:
        if runs and runs[-1][0] == value:
            prior, count = runs[-1]
            runs[-1] = (prior, count + 1)
        else:
            runs.append((value, 1))
    return runs


def solve(grid: list[list[int]], *, output_scale: int = DEFAULT_OUTPUT_SCALE) -> list[list[int]]:
    """Independent Python mirror for one proposed output-scale setting."""
    _validate_output_scale(output_scale)
    errors = _GEN.self_check(grid)
    if errors:
        raise ValueError(f"input is outside the selected staircase grammar: {errors}")
    sequence = _active_diagonal(grid)
    return _build_from_sequence(grid, sequence, output_scale=output_scale)


def select_setting(seed: int) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal Python integer")
    return SETTINGS[seed % len(SETTINGS)]


def _rng(seed: int, difficulty: str, split: str, index: int, attempt: int) -> random.Random:
    payload = f"{TASK_ID}/native-v1/{seed}/{difficulty}/{split}/{index}/{attempt}"
    return random.Random(int.from_bytes(hashlib.sha256(payload.encode()).digest(), "big"))


def _staircase(active: list[int], padded: bool) -> list[list[int]]:
    diagonal = active + ([0] if padded else [])
    return [[diagonal[max(row, col)] for col in range(len(diagonal))]
            for row in range(len(diagonal))]


def _rich_sequence(rng: random.Random, period: int) -> list[int]:
    """Both first/later colors recur, with first/final contiguous runs."""
    colors = rng.sample(range(1, 10), period - 4)
    first, later = colors[:2]
    middle = [first, *colors[2:]]
    rng.shuffle(middle)
    # Runs are first^2, later, a nonempty distinct middle containing first,
    # then later^2. This stays inside the admitted complex-repeat grammar.
    return [first, first, later, *middle, later, later]


def _input_candidate(seed: int, difficulty: str, split: str, index: int,
                     attempt: int) -> list[list[int]]:
    rng = _rng(seed, difficulty, split, index, attempt)
    palette = rng.sample(range(1, 10), 9)
    if split == "train" and index == 0:
        # Canonical-size, unpadded; both color roles recur in distinct runs.
        a, b, c = palette[:3]
        return _staircase([a, b, a, c, b], False)
    if split == "train" and index == 1:
        # Padded plus actual contiguous multiplicity; its recovered period
        # cannot be inferred from either the input side or unique colors.
        return _staircase(_rich_sequence(rng, rng.randint(7, 9)), True)
    if split == "train" and index == 2:
        return _staircase(palette[:4], True)
    if split == "train" and index == 3:
        period = rng.randint(6, 9)
        run = rng.randint(2, period - 2)
        return _staircase([palette[0]] * run + palette[1:period - run + 1], False)
    if split == "train" and index == 4:
        period = rng.randint(6, 9)
        return _staircase([*palette[:period - 2], *palette[:2]], bool(rng.randrange(2)))
    if split == "train" and index == 5:
        return _staircase(palette[:rng.randint(4, 8)], bool(rng.randrange(2)))
    if split == "test" and index == 0:
        a, b, c = palette[:3]
        return _staircase([a, b, a, c], True)
    if split == "test" and index == 1:
        period = rng.randint(6, 9)
        run = rng.randint(2, period - 3)
        sequence = [palette[0]] * run + palette[1:period - run]
        sequence.insert(rng.randint(run + 1, len(sequence)), palette[0])
        return _staircase(sequence, False)
    if split == "test" and index == 2:
        period = rng.randint(6, 9)
        if rng.randrange(2):
            sequence = [palette[0], palette[0], *palette[1:period - 3],
                        palette[period - 3], palette[period - 3]]
        else:
            sequence = [*palette[:period - 2], *palette[:2]]
        return _staircase(sequence, bool(rng.randrange(2)))
    if split == "test" and index == 3:
        return _staircase(_rich_sequence(rng, 9), True)
    raise ValueError("unknown fixed-bank slot")


def _input_bank(seed: int, difficulty: str) -> dict[str, list[list[list[int]]]]:
    bank: dict[str, list[list[list[int]]]] = {"train": [], "test": []}
    seen: set[str] = set()
    # Materializing the bounded bank before slicing makes every prefix stable
    # even when a candidate duplicates an unrequested demonstration.
    for split, count in (("train", 6), ("test", 4)):
        for index in range(count):
            for attempt in range(64):
                grid = _input_candidate(seed, difficulty, split, index, attempt)
                errors = _GEN.self_check(grid)
                if errors:
                    raise RuntimeError(f"constructed invalid {split} slot {index}: {errors}")
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    seen.add(key)
                    bank[split].append(grid)
                    break
            else:
                raise RuntimeError(f"could not find distinct {split} slot {index} in 64 draws")
    return bank


def generate_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    output_scale: int | None = None,
    demo_count: int = 3,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one complete episode with a single fixed output scale."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal Python integer")
    selected = select_setting(seed) if output_scale is None else output_scale
    _validate_output_scale(selected)
    if type(demo_count) is not int or not DEMO_LIMITS[0] <= demo_count <= DEMO_LIMITS[1]:
        raise ValueError("demo_count must be a literal Python integer in 2..6")
    if type(query_count) is not int or not QUERY_LIMITS[0] <= query_count <= QUERY_LIMITS[1]:
        raise ValueError("query_count must be a literal Python integer in 1..4")
    if type(difficulty) is not str or difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium or hard")
    bank = _input_bank(seed, difficulty)
    pairs = {
        split: [{"input": deepcopy(grid), "output": solve(grid, output_scale=selected)}
                for grid in bank[split][:count]]
        for split, count in (("train", demo_count), ("test", query_count))
    }
    rule = program_for(selected)
    return {
        "train": pairs["train"],
        "test": pairs["test"],
        "parameters": {"output_scale": selected},
        "program": rule,
        "meta": {
            "prototype": True,
            "status": "proposed_not_selected",
            "task_id": TASK_ID,
            "seed": seed,
            "difficulty": difficulty,
            "selection_scope": "once_per_episode",
            "demo_count": demo_count,
            "query_count": query_count,
            "canonical_default": DEFAULT_OUTPUT_SCALE,
            "allowed_output_scales": list(ALLOWED_OUTPUT_SCALES),
            "program_sha256": hashlib.sha256(rule.encode("utf-8")).hexdigest(),
            "normalized_program_sha256": normalized_program_hash(selected),
            "input_constraint": (
                "lawful input side is at most 10, so output_scale 3 stays within "
                "the ARC 30x30 bound"
            ),
        },
    }


def generate(seed: int, settings: dict[str, int], demos: int = 3,
             queries: int = 4) -> dict[str, Any]:
    """Native claims; protected Racket independently supplies accepted labels."""
    scale = _settings(settings)
    episode = generate_episode(seed, output_scale=scale, demo_count=demos,
                               query_count=queries)
    return {"train": episode["train"], "test": episode["test"],
            "program_solution": episode["program"]}



def _rival_outputs(grid: list[list[int]], *, output_scale: int) -> dict[str, list[list[int]]]:
    active = _active_diagonal(grid)
    raw_diagonal = [grid[index][index] for index in range(len(grid))]

    deduplicated: list[int] = []
    for value in active:
        if value not in deduplicated:
            deduplicated.append(value)

    first_run_per_color: list[int] = []
    seen: set[int] = set()
    for value, count in _run_lengths(active):
        if value not in seen:
            first_run_per_color.extend([value] * count)
        seen.add(value)

    def role_runs(exempt_first: bool) -> list[int]:
        seen: set[int] = set()
        sequence: list[int] = []
        for value, count in _run_lengths(active):
            if ((value == active[0]) == exempt_first) or value not in seen:
                sequence.extend([value] * count)
            seen.add(value)
        return sequence

    alternate_scale = next(scale for scale in ALLOWED_OUTPUT_SCALES if scale != output_scale)
    height, width = len(grid), len(grid[0])
    return {
        "alternate_output_scale": solve(grid, output_scale=alternate_scale),
        "tile_whole_input": [
            [grid[row % height][col % width] for col in range(output_scale * width)]
            for row in range(output_scale * height)
        ],
        "row_period_only": _build_from_sequence(
            grid, active, output_scale=output_scale, metric="row"
        ),
        "column_period_only": _build_from_sequence(
            grid, active, output_scale=output_scale, metric="column"
        ),
        "keep_terminal_zero_in_period": _build_from_sequence(
            grid, raw_diagonal, output_scale=output_scale
        ),
        "always_drop_last_diagonal": _build_from_sequence(
            grid, raw_diagonal[:-1], output_scale=output_scale
        ),
        "deduplicate_active_diagonal": _build_from_sequence(
            grid, deduplicated, output_scale=output_scale
        ),
        "first_run_per_color": _build_from_sequence(
            grid, first_run_per_color, output_scale=output_scale
        ),
        "first_color_exempt_first_run": _build_from_sequence(
            grid, role_runs(True), output_scale=output_scale
        ),
        "other_colors_exempt_first_run": _build_from_sequence(
            grid, role_runs(False), output_scale=output_scale
        ),
        "compress_contiguous_runs": _build_from_sequence(
            grid, [color for color, _ in _run_lengths(active)], output_scale=output_scale
        ),
        "fixed_period_four": _build_from_sequence(
            grid, active[:4], output_scale=output_scale
        ),
    }


RIVAL_NAMES = (
    "alternate_output_scale",
    "tile_whole_input",
    "row_period_only",
    "column_period_only",
    "keep_terminal_zero_in_period",
    "always_drop_last_diagonal",
    "deduplicate_active_diagonal",
    "first_run_per_color",
    "first_color_exempt_first_run",
    "other_colors_exempt_first_run",
    "compress_contiguous_runs",
    "fixed_period_four",
)


def lesson_identifiable(
    demos: list[dict[str, Any]],
    query: dict[str, Any],
    *,
    output_scale: int,
) -> list[str]:
    """Check the fixed setting and core staircase rule from demonstrations only."""
    _validate_output_scale(output_scale)
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not DEMO_LIMITS[0] <= len(demos) <= DEMO_LIMITS[1]:
        return ["need 2..6 demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    valid_demos: list[dict[str, Any]] = []
    observed: list[dict[str, object]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = _GEN.self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the lawful staircase grammar")
            continue
        if demo["output"] != solve(demo["input"], output_scale=output_scale):
            reasons.append(f"demo {index} output does not use output_scale={output_scale}")
            continue
        valid_demos.append(demo)
        observed.append(_GEN.observe_overrides(demo["input"]))

    query_errors = _GEN.self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the lawful staircase grammar")
    elif "output" in query and query["output"] != solve(
        query["input"], output_scale=output_scale
    ):
        reasons.append(f"query output does not use output_scale={output_scale}")

    if valid_demos:
        padding_seen = {str(item["padding"]) for item in observed}
        size_classes = {len(demo["input"]) == 5 for demo in valid_demos}
        periods = {int(item["period"]) for item in observed}
        if padding_seen != {"none", "one"}:
            reasons.append("demonstrations must cover both padding branches")
        if size_classes != {False, True}:
            reasons.append("demonstrations must include canonical and generalized sizes")
        if not any(period > 5 for period in periods):
            reasons.append("demonstrations must include a period above five")

        if not query_errors:
            authoritative_query = solve(query["input"], output_scale=output_scale)
            query_rivals = _rival_outputs(query["input"], output_scale=output_scale)
            for rival_name in RIVAL_NAMES:
                survives_demos = all(
                    _rival_outputs(demo["input"], output_scale=output_scale)[rival_name]
                    == demo["output"]
                    for demo in valid_demos
                )
                if survives_demos and query_rivals[rival_name] != authoritative_query:
                    reasons.append(
                        f"named rival {rival_name!r} survives demonstrations and changes the query answer"
                    )
    return reasons


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only visible demonstrations and answer-masked query inputs."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }



def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--output-scale", type=int, choices=ALLOWED_OUTPUT_SCALES)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    episode = generate_episode(
        args.seed,
        difficulty=args.difficulty,
        output_scale=args.output_scale,
        demo_count=args.demos,
        query_count=args.queries,
    )
    if args.public:
        from reviewer_support import public_challenge_bytes

        data = public_challenge_bytes(public_challenge(episode))
    else:
        data = (json.dumps(episode, indent=2, sort_keys=True) + "\n").encode("utf-8")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(data)
    else:
        import sys

        sys.stdout.buffer.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
