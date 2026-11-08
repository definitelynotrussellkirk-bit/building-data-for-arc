#!/usr/bin/env python3
"""Proposed episode-fixed rule variants for ARC generator 7b088f161470.

This task-local prototype is deliberately separate from the approved canonical
per-puzzle generator. Racket execution is the label authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "7b088f161470"
VERSION = "proposed-rung-width-alignment-v1"
ALLOWED_MIN_RUNG_WIDTHS = (3, 4, 5)
ALLOWED_BAR_ALIGNMENTS = ("left", "right")
DEFAULT_MIN_RUNG_WIDTH = 3
DEFAULT_BAR_ALIGNMENT = "left"
SETTINGS = tuple(
    (width, alignment)
    for width in ALLOWED_MIN_RUNG_WIDTHS
    for alignment in ALLOWED_BAR_ALIGNMENTS
)
CANONICAL_RAW_SHA256 = "5cb73bc4092b61cc885c0ad3c2ec1cf301bb02c288dcd3462aa4d85c370c4bfc"
_WIDTH_PATTERN = re.compile(r"\(>=\s+\(length\s+cells-of-color\)\s+3\)")
_CANONICAL_BAR = "(if (< c cnt) color 0)"
_RIGHT_BAR = "(if (>= c (- 3 cnt)) color 0)"
_RUN_LENGTHS = ((3, 4, 5), (4, 5), (5, 5))


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _validate_min_rung_width(value: int) -> int:
    if type(value) is not int or value not in ALLOWED_MIN_RUNG_WIDTHS:
        raise ValueError(
            f"min_rung_width must be one of {ALLOWED_MIN_RUNG_WIDTHS}, not {value!r}"
        )
    return value


def _validate_bar_alignment(value: str) -> str:
    if value not in ALLOWED_BAR_ALIGNMENTS:
        raise ValueError(
            f"bar_alignment must be one of {ALLOWED_BAR_ALIGNMENTS}, not {value!r}"
        )
    return value


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    return seed


def _validate_count(name: str, value: int) -> int:
    if type(value) is not int or not 1 <= value <= 128:
        raise ValueError(f"{name} must be an integer in 1..128 (not bool)")
    return value


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_RAW_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if len(_WIDTH_PATTERN.findall(source)) != 1:
        raise ValueError("canonical source does not contain one rung-width guard")
    if source.count(_CANONICAL_BAR) != 1 or _RIGHT_BAR in source:
        raise ValueError("canonical source does not contain the expected left-bar branch")
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    sources = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def materialize_rule(
    min_rung_width: int = DEFAULT_MIN_RUNG_WIDTH,
    bar_alignment: str = DEFAULT_BAR_ALIGNMENT,
    *,
    root: str | Path | None = None,
) -> str:
    """Return one exact proposed Racket rule; the default is unedited canonical text."""
    min_rung_width = _validate_min_rung_width(min_rung_width)
    bar_alignment = _validate_bar_alignment(bar_alignment)
    source = canonical_source(root=root)
    if min_rung_width != DEFAULT_MIN_RUNG_WIDTH:
        source, replacements = _WIDTH_PATTERN.subn(
            f"(>= (length cells-of-color) {min_rung_width})", source, count=1
        )
        if replacements != 1:
            raise AssertionError("rung-width replacement was not exact")
    if bar_alignment == "right":
        if source.count(_CANONICAL_BAR) != 1:
            raise AssertionError("bar-alignment replacement was not exact")
        source = source.replace(_CANONICAL_BAR, _RIGHT_BAR, 1)
    return source


def _grid_literal(grid: list[list[int]]) -> str:
    normalized = normalize_grid(grid)
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"


def execute_rule(
    source: str,
    grid: list[list[int]],
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute the exact materialized Racket rule; no Python labels are trusted."""
    callable_source = strip_rule_wrapper(source)
    expression = f"({callable_source} {_grid_literal(grid)})"
    if bridge is not None:
        return normalize_grid(bridge.eval_text(expression))
    status = racket_runtime_status()
    if not status["available"]:
        raise RuntimeError(status["reason"])
    with RacketBridge() as owned:
        return normalize_grid(owned.eval_text(expression))


def apply_python(
    grid: list[list[int]],
    min_rung_width: int = DEFAULT_MIN_RUNG_WIDTH,
    bar_alignment: str = DEFAULT_BAR_ALIGNMENT,
) -> list[list[int]]:
    """Independent Python mirror used only to cross-check Racket executions."""
    min_rung_width = _validate_min_rung_width(min_rung_width)
    bar_alignment = _validate_bar_alignment(bar_alignment)
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    floor_rows = [
        row
        for row in range(height)
        if grid[row][0] != 0 and all(grid[row][col] == grid[row][0] for col in range(1, width))
    ]
    if len(floor_rows) != 4:
        raise ValueError(f"expected four uniform floors, found {len(floor_rows)}")
    floor_colors = [grid[row][0] for row in floor_rows]
    rung_counts = []
    for index, color in enumerate(floor_colors[:-1]):
        count = 0
        for row in range(floor_rows[index] + 1, floor_rows[index + 1]):
            cells = [col for col in range(width) if grid[row][col] == color]
            if (
                len(cells) >= min_rung_width
                and cells[-1] - cells[0] == len(cells) - 1
            ):
                count += 1
        rung_counts.append(count)
    positive = [(count, index) for index, count in enumerate(rung_counts) if count > 0]
    gray_floor_index = min(positive, key=lambda item: (item[0], -item[1]))[1] if positive else 0
    has_gray = any(cell == 5 for row in grid for cell in row)
    output = []
    for row, (color, count) in enumerate(zip(floor_colors[:-1], rung_counts)):
        bar = []
        for col in range(3):
            active = col < count if bar_alignment == "left" else col >= 3 - count
            bar.append(color if active else 0)
        output.append(
            bar
            + [floor_colors[-1], 5 if has_gray and row == gray_floor_index else 0]
        )
    return output


def _stable_int(seed: int, label: str) -> int:
    return int.from_bytes(
        hashlib.sha256(f"{seed}:{label}".encode("utf-8")).digest()[:16], "big"
    )


def _select_setting(
    seed: int,
    min_rung_width: int | None,
    bar_alignment: str | None,
) -> tuple[int, str]:
    sampled = SETTINGS[_stable_int(seed, "setting") % len(SETTINGS)]
    width = sampled[0] if min_rung_width is None else _validate_min_rung_width(min_rung_width)
    alignment = sampled[1] if bar_alignment is None else _validate_bar_alignment(bar_alignment)
    return width, alignment


def _scene(seed: int, index: int) -> list[list[int]]:
    rng = random.Random(_stable_int(seed, f"scene:{index}"))
    width = rng.randint(12, 18)
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8], 3)
    grid = [[0] * width for _ in range(rng.randint(0, 2))]
    for color, run_lengths in zip(colors, _RUN_LENGTHS):
        grid.append([color] * width)
        band: list[list[int]] = []
        for run_length in run_lengths:
            row = [0] * width
            start = rng.randint(0, width - run_length)
            for col in range(start, start + run_length):
                row[col] = color
            band.append(row)
        for _ in range(2):
            row = [0] * width
            left = rng.randint(0, width - 3)
            right = rng.randint(left + 2, min(width - 1, left + 5))
            row[left] = color
            row[right] = color
            band.append(row)
        band.extend([[0] * width for _ in range(rng.randint(1, 2))])
        rng.shuffle(band)
        grid.extend(band)
    grid.append([9] * width)
    grid.extend([[0] * width for _ in range(rng.randint(0, 2))])
    empty = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
    ]
    row, col = rng.choice(empty)
    grid[row][col] = 5
    return grid


def _grid_key(grid: list[list[int]]) -> str:
    return _sha256(json.dumps(normalize_grid(grid), separators=(",", ":")))


def _demo_survivors(
    public: dict,
    *,
    bridge: RacketBridge,
) -> list[dict[str, int | str]]:
    survivors = []
    for width, alignment in SETTINGS:
        source = materialize_rule(width, alignment)
        if all(
            execute_rule(source, pair["input"], bridge=bridge) == pair["output"]
            for pair in public["train"]
        ):
            survivors.append(
                {"min_rung_width": width, "bar_alignment": alignment}
            )
    return survivors


def generate_episode(
    seed: int,
    *,
    min_rung_width: int | None = None,
    bar_alignment: str | None = None,
    n_train: int = 3,
    n_test: int = 4,
    bridge: RacketBridge | None = None,
) -> dict:
    """Generate one deterministic episode with one hidden setting fixed throughout."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    width, alignment = _select_setting(seed, min_rung_width, bar_alignment)
    needed = n_train + n_test
    inputs = []
    seen = set()
    for index in range(needed * 8):
        grid = _scene(seed, index)
        key = _grid_key(grid)
        if key in seen:
            continue
        seen.add(key)
        inputs.append(grid)
        if len(inputs) == needed:
            break
    if len(inputs) != needed:
        raise RuntimeError(f"could not draw {needed} distinct inputs")

    source = materialize_rule(width, alignment)

    def build(active_bridge: RacketBridge) -> dict:
        outputs = [execute_rule(source, grid, bridge=active_bridge) for grid in inputs]
        for grid, output in zip(inputs, outputs):
            mirrored = apply_python(grid, width, alignment)
            if mirrored != output:
                raise RuntimeError("Python mirror disagrees with executed Racket rule")
        public = {
            "train": [
                {"input": inputs[index], "output": outputs[index]}
                for index in range(n_train)
            ],
            "test": [
                {"input": inputs[index]}
                for index in range(n_train, needed)
            ],
        }
        public_id = public_challenge_id(public)
        survivors = _demo_survivors(public, bridge=active_bridge)
        expected_survivor = {
            "min_rung_width": width,
            "bar_alignment": alignment,
        }
        if survivors != [expected_survivor]:
            raise RuntimeError(
                f"demonstrations do not identify the selected setting: {survivors}"
            )
        private = {
            "schema": "arcpuzzles-parametric-episode-private-v1",
            "status": "proposed prototype; no production approval or training admission",
            "task_id": TASK_ID,
            "prototype_version": VERSION,
            "seed": seed,
            "parameters": expected_survivor,
            "n_train": n_train,
            "n_test": n_test,
            "rule_source": source,
            "rule_sha256": _sha256(source),
            "public_id": public_id,
            "demo_survivors": survivors,
            "query_outputs": outputs[n_train:],
            "input_sha256": [_grid_key(grid) for grid in inputs],
            "output_sha256": [_grid_key(output) for output in outputs],
        }
        return {"public": public, "private": private}

    if bridge is not None:
        return build(bridge)
    status = racket_runtime_status()
    if not status["available"]:
        raise RuntimeError(status["reason"])
    with RacketBridge() as owned:
        return build(owned)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_episode(episode: dict, out: str | Path, *, index: int) -> dict[str, Path]:
    """Write public visible bytes separately from private settings and answers."""
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative integer")
    out = Path(out)
    public = episode["public"]
    private = episode["private"]
    visible = public_challenge_bytes(public)
    public_id = _sha256(visible)
    if private.get("public_id") != public_id:
        raise ValueError("private public_id does not match visible challenge bytes")
    rule_bytes = private["rule_source"].encode("utf-8")
    if _sha256(rule_bytes) != private.get("rule_sha256"):
        raise ValueError("private rule_sha256 does not match rule_source bytes")
    rule_path = out / "private" / "rules" / f"{private['rule_sha256']}.rkt"
    if rule_path.exists() and rule_path.read_bytes() != rule_bytes:
        raise ValueError(f"existing rule artifact does not match {private['rule_sha256']}")
    public_path = out / "public" / f"challenge-{public_id}.json"
    if public_path.exists():
        raise ValueError(f"duplicate visible challenge: {public_id}")
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_bytes(visible)
    private_path = out / "private" / f"episode-{index:03d}.json"
    _write_json(private_path, private)
    if not rule_path.exists():
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_bytes(rule_bytes)
    return {"public": public_path, "private": private_path, "rule": rule_path}


def _canonical_parity(bridge: RacketBridge) -> dict:
    source = materialize_rule()
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    for pair in pairs:
        if execute_rule(source, pair["input"], bridge=bridge) != pair["output"]:
            raise RuntimeError("default rule failed canonical parity")
    return {
        "passed": len(pairs),
        "total": len(pairs),
        "unique_inputs": len({_grid_key(pair["input"]) for pair in pairs}),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7319)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--min-rung-width", type=int, choices=ALLOWED_MIN_RUNG_WIDTHS)
    parser.add_argument("--bar-alignment", choices=ALLOWED_BAR_ALIGNMENTS)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.all_settings and (
        args.min_rung_width is not None or args.bar_alignment is not None
    ):
        parser.error("--all-settings cannot be combined with setting overrides")

    requested = SETTINGS if args.all_settings else (
        (args.min_rung_width, args.bar_alignment),
    )
    episodes = []
    with RacketBridge() as bridge:
        parity = _canonical_parity(bridge)
        for index, (width, alignment) in enumerate(requested):
            episode = generate_episode(
                args.seed + index,
                min_rung_width=width,
                bar_alignment=alignment,
                n_train=args.n_train,
                n_test=args.n_test,
                bridge=bridge,
            )
            episodes.append(episode)
    episodes.sort(key=lambda episode: episode["private"]["public_id"])
    written = []
    for index, episode in enumerate(episodes):
        paths = write_episode(episode, args.out, index=index)
        written.append(
            {
                "public_id": episode["private"]["public_id"],
                "parameters": episode["private"]["parameters"],
                "paths": {name: str(path.relative_to(args.out)) for name, path in paths.items()},
            }
        )
    report = {
        "schema": "arcpuzzles-parametric-report-v1",
        "status": "proposed prototype; no production approval or training admission",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "command": " ".join(sys.argv),
        "seed": args.seed,
        "n_train": args.n_train,
        "n_test": args.n_test,
        "canonical_parity": parity,
        "episodes": written,
        "source_sha256": {
            "prototype.py": _sha256(Path(__file__).read_bytes()),
            "canonical_rule": _sha256(canonical_source()),
        },
        "limits": [
            "Bounded task-local prototype; no production parametric API or catalog change.",
            "Identifiability is checked only against the declared six-setting family.",
            "The sampler is a nearby authored subfamily with run lengths 2 through 5, not full-domain coverage.",
        ],
    }
    _write_json(args.out / "report.json", report)
    print(
        json.dumps(
            {
                "canonical_parity": parity,
                "episodes": len(episodes),
                "n_train": args.n_train,
                "n_test": args.n_test,
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
