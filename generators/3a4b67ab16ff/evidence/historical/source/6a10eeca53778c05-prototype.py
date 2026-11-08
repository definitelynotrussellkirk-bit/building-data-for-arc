#!/usr/bin/env python3
"""Racket-backed episode prototype for color-layer precedence.

The selected production generator remains fixed to its canonical ascending
numeric color order.  This isolated authoring prototype varies one hidden rule
parameter once per episode: whether colored bbox intersections are layered in
ascending or descending numeric order.  The canonical/default value is
``ascending`` and materializes the exact registered canonical source bytes.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "3a4b67ab16ff"
ORIGINAL_TASK_ID = "1c02dbbe"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "layer_order"
ALLOWED_LAYER_ORDERS = ("ascending", "descending")
DEFAULT_LAYER_ORDER = "ascending"
CANONICAL_PROGRAM_SHA256 = (
    "32c694357bd0cf193ee8522752d4e50538cd8c33aff87788d1f1300070ae64b6"
)
_MARKER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_UNSET = object()
_REPO_ROOT = Path(__file__).resolve().parents[4]
_CANONICAL_RECORD_PATH = (
    _REPO_ROOT
    / "shared"
    / "data"
    / "base"
    / "solutions"
    / "training"
    / "1c02dbbe__3a4b67ab16ff.json"
)
_GENERATOR_PATH = _REPO_ROOT / "generators" / TASK_ID / "generator.py"
_ORDER_SITE = "(range 1 10)"
_DESCENDING_ORDER_SITE = "(reverse (range 1 10))"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_count(name: str, value: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (not bool)")
    if not 1 <= value <= 20:
        raise ValueError(f"{name} must be between 1 and 20")
    return value


def _validate_layer_order(layer_order: str) -> str:
    if type(layer_order) is not str:
        raise TypeError("layer_order must be a string")
    if layer_order not in ALLOWED_LAYER_ORDERS:
        raise ValueError(f"layer_order must be one of {ALLOWED_LAYER_ORDERS}")
    return layer_order


def choose_layer_order(seed: int) -> str:
    """Choose one hidden parameter value deterministically for an episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|{PARAMETER_NAME}|{seed}".encode("utf-8")
    ).digest()
    return ALLOWED_LAYER_ORDERS[digest[0] % len(ALLOWED_LAYER_ORDERS)]


def canonical_rule() -> str:
    """Return the exact registered canonical Racket source, pinned by SHA-256."""
    record = json.loads(_CANONICAL_RECORD_PATH.read_text(encoding="utf-8"))
    source = record["racket_target"]["raw_code"]
    digest = _sha256_text(source)
    if digest != CANONICAL_PROGRAM_SHA256:
        raise RuntimeError(
            "canonical rule bytes changed: "
            f"expected {CANONICAL_PROGRAM_SHA256}, observed {digest}"
        )
    if source.count(_ORDER_SITE) != 1:
        raise RuntimeError("canonical rule no longer has exactly one color-order site")
    return source


def materialize_rule(layer_order: str) -> str:
    """Render the exact Racket authority candidate for one parameter value."""
    setting = _validate_layer_order(layer_order)
    source = canonical_rule()
    if setting == DEFAULT_LAYER_ORDER:
        return source
    return source.replace(_ORDER_SITE, _DESCENDING_ORDER_SITE, 1)


def _rule_body(program: str) -> str:
    text = program.strip()
    prefix = "(rule!"
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("program must be a complete (rule! BODY) form")
    return text[len(prefix) : -1].strip()


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be between 1 and 30")
    return grid


def apply_racket(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute one materialized program; this is the labeling authority."""
    source_grid = _validate_grid(grid)
    bridge.define_grid("g", source_grid)
    output = bridge.eval_text(f"({_rule_body(program)} g)")
    normalized = _validate_grid(output)
    if len(normalized) != len(source_grid) or len(normalized[0]) != len(source_grid[0]):
        raise ValueError("Racket program changed grid dimensions")
    return normalized


def _rect_corners(bounds: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    row0, col0, row1, col1 = bounds
    return {(row0, col0), (row0, col1), (row1, col0), (row1, col1)}


def _input_rng(seed: int, variant: int) -> random.Random:
    payload = f"{TASK_ID}|{PROTOTYPE_VERSION}|input|{seed}|{variant}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def make_input(seed: int, variant: int) -> list[list[int]]:
    """Build one lawful overlapping two-color joint-bbox scene.

    Input sampling is independent of ``layer_order``.  Both color bboxes lie
    inside the gray bbox and overlap by several cells, so ascending and
    descending programs necessarily disagree on the overlap.
    """
    _validate_seed(seed)
    if type(variant) is not int:
        raise TypeError("variant must be an exact integer (not bool)")
    if variant < 0:
        raise ValueError("variant must be nonnegative")
    rng = _input_rng(seed, variant)
    height = rng.randint(15, 22)
    width = rng.randint(15, 22)
    margin_top = rng.randint(2, 3)
    margin_left = rng.randint(2, 3)
    margin_bottom = rng.randint(2, 3)
    margin_right = rng.randint(2, 3)
    gr0, gc0 = margin_top, margin_left
    gr1, gc1 = height - margin_bottom - 1, width - margin_right - 1
    middle_row = (gr0 + gr1) // 2
    middle_col = (gc0 + gc1) // 2

    upper_left = (
        gr0 + 1,
        gc0 + 1,
        min(gr1 - 2, middle_row + rng.randint(1, 2)),
        min(gc1 - 2, middle_col + rng.randint(1, 2)),
    )
    lower_right = (
        max(gr0 + 2, middle_row - rng.randint(1, 2)),
        max(gc0 + 2, middle_col - rng.randint(1, 2)),
        gr1 - 1,
        gc1 - 1,
    )
    if _rect_corners(upper_left) & _rect_corners(lower_right):
        raise AssertionError("constructed marker sets unexpectedly collide")
    overlap = (
        max(upper_left[0], lower_right[0]),
        max(upper_left[1], lower_right[1]),
        min(upper_left[2], lower_right[2]),
        min(upper_left[3], lower_right[3]),
    )
    if overlap[0] > overlap[2] or overlap[1] > overlap[3]:
        raise AssertionError("constructed color rectangles must overlap")

    low_color, high_color = sorted(rng.sample(_MARKER_COLORS, 2))
    if rng.randrange(2):
        colored_bounds = ((low_color, lower_right), (high_color, upper_left))
    else:
        colored_bounds = ((low_color, upper_left), (high_color, lower_right))

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(gr0, gr1 + 1):
        for col in range(gc0, gc1 + 1):
            grid[row][col] = 5
    for color, bounds in colored_bounds:
        for row, col in _rect_corners(bounds):
            grid[row][col] = color
    return grid


def _distinct_inputs(seed: int, count: int) -> list[list[list[int]]]:
    inputs: list[list[list[int]]] = []
    seen: set[str] = set()
    variant = 0
    while len(inputs) < count:
        if variant >= count * 100:
            raise RuntimeError("could not construct enough distinct input grids")
        grid = make_input(seed, variant)
        key = json.dumps(grid, separators=(",", ":"))
        variant += 1
        if key in seen:
            continue
        seen.add(key)
        inputs.append(grid)
    return inputs


def _rival(setting: str) -> str:
    return next(value for value in ALLOWED_LAYER_ORDERS if value != setting)


def build_episode(
    seed: int,
    layer_order: Any = _UNSET,
    *,
    train_count: int = 3,
    test_count: int = 4,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete private episode, with every label executed in Racket."""
    seed = _validate_seed(seed)
    train_count = _validate_count("train_count", train_count)
    test_count = _validate_count("test_count", test_count)
    setting = (
        choose_layer_order(seed)
        if layer_order is _UNSET
        else _validate_layer_order(layer_order)
    )
    rival = _rival(setting)
    selected_program = materialize_rule(setting)
    rival_program = materialize_rule(rival)
    inputs = _distinct_inputs(seed, train_count + test_count)

    runtime = bridge if bridge is not None else RacketBridge(max_calls_before_restart=64)
    owns_runtime = bridge is None
    pairs: list[dict[str, Any]] = []
    try:
        for grid in inputs:
            output = apply_racket(runtime, selected_program, grid)
            rival_output = apply_racket(runtime, rival_program, grid)
            pairs.append(
                {
                    "input": grid,
                    "output": output,
                    "rival_output": rival_output,
                    "distinguishes_rival": output != rival_output,
                }
            )
    finally:
        if owns_runtime:
            runtime.shutdown()

    train = pairs[:train_count]
    test = pairs[train_count:]
    demo_refutation = all(pair["distinguishes_rival"] for pair in train)
    query_differences = all(pair["distinguishes_rival"] for pair in test)
    if not demo_refutation or not query_differences:
        raise AssertionError("sampled episode does not identify and exercise layer_order")

    return {
        "schema": f"{TASK_ID}-layer-order-private-v1",
        "task_id": TASK_ID,
        "original_task_id": ORIGINAL_TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {PARAMETER_NAME: setting},
        "defaults": {PARAMETER_NAME: DEFAULT_LAYER_ORDER},
        "input_constraints": {
            "gray_bbox": "complete rectangular color-5 field with a zero margin",
            "markers": "two non-gray colors, four corner markers per joint bbox",
            "interaction": "the two clipped color rectangles overlap",
            "parameter_dependency": "none; identical inputs are valid for both settings",
        },
        "program": {
            "source": selected_program,
            "sha256": _sha256_text(selected_program),
            "canonical_exact": setting == DEFAULT_LAYER_ORDER,
        },
        "rival": {
            "parameters": {PARAMETER_NAME: rival},
            "program_source": rival_program,
            "program_sha256": _sha256_text(rival_program),
        },
        "train": train,
        "test": test,
        "checks": {
            "setting_selected_once": True,
            "all_labels_from_racket": True,
            "demonstrations_refute_rival": demo_refutation,
            "all_queries_differ_from_rival": query_differences,
            "demonstration_count": train_count,
            "query_count": test_count,
            "unique_input_count": len(inputs),
        },
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    """Return exact visible challenge bytes, excluding all private fields."""
    return public_challenge_bytes(episode)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(public_bytes(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(episode)


def public_filename(episode: dict[str, Any]) -> str:
    return f"challenge-{public_id(episode)}.json"


def _find_seed_for(setting: str, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_layer_order(seed) != setting:
        seed += 1
    return seed


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize(
    out_dir: Path,
    *,
    seed_start: int = 1200,
    train_count: int = 3,
    test_count: int = 4,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Retain one complete Racket-backed episode per allowed setting."""
    seed_start = _validate_seed(seed_start)
    train_count = _validate_count("train_count", train_count)
    test_count = _validate_count("test_count", test_count)
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence: {out_dir}")
    private_dir = out_dir / "private"
    public_dir = out_dir / "public"
    program_dir = private_dir / "programs"
    episode_dir = private_dir / "episodes"
    for directory in (program_dir, episode_dir, public_dir):
        directory.mkdir(parents=True, exist_ok=False)

    for setting in ALLOWED_LAYER_ORDERS:
        (program_dir / f"{setting}.rkt").write_text(
            materialize_rule(setting) + "\n", encoding="utf-8"
        )

    used: set[int] = set()
    records: list[dict[str, Any]] = []
    ids: set[str] = set()
    runtime = bridge if bridge is not None else RacketBridge(max_calls_before_restart=128)
    owns_runtime = bridge is None
    try:
        for offset, setting in enumerate(ALLOWED_LAYER_ORDERS):
            seed = _find_seed_for(setting, seed_start + offset, used)
            used.add(seed)
            episode = build_episode(
                seed,
                train_count=train_count,
                test_count=test_count,
                bridge=runtime,
            )
            if episode["parameters"][PARAMETER_NAME] != setting:
                raise AssertionError("seed selector did not retain requested setting")
            identifier = public_id(episode)
            if identifier in ids:
                raise ValueError("duplicate visible public challenge payload")
            ids.add(identifier)
            private_rel = Path("private") / "episodes" / f"episode-{setting}-seed-{seed}.json"
            public_rel = Path("public") / public_filename(episode)
            _write_json(out_dir / private_rel, episode)
            (out_dir / public_rel).write_bytes(public_bytes(episode))
            records.append(
                {
                    "layer_order": setting,
                    "seed": seed,
                    "train_count": train_count,
                    "query_count": test_count,
                    "unique_input_count": episode["checks"]["unique_input_count"],
                    "demonstrations_refute_rival": episode["checks"][
                        "demonstrations_refute_rival"
                    ],
                    "all_queries_differ_from_rival": episode["checks"][
                        "all_queries_differ_from_rival"
                    ],
                    "program_sha256": episode["program"]["sha256"],
                    "public_id": identifier,
                    "public_sha256": _sha256_bytes(public_bytes(episode)),
                    "private_path": private_rel.as_posix(),
                    "public_path": public_rel.as_posix(),
                }
            )
    finally:
        if owns_runtime:
            runtime.shutdown()

    records.sort(key=lambda row: row["public_id"])
    source_snapshot = {
        "task_id": TASK_ID,
        "original_task_id": ORIGINAL_TASK_ID,
        "canonical_record_path": str(_CANONICAL_RECORD_PATH.relative_to(_REPO_ROOT)),
        "canonical_record_sha256": _sha256_bytes(_CANONICAL_RECORD_PATH.read_bytes()),
        "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
        "canonical_default_exact_source": materialize_rule(DEFAULT_LAYER_ORDER)
        == canonical_rule(),
        "generator_path": str(_GENERATOR_PATH.relative_to(_REPO_ROOT)),
        "generator_sha256": _sha256_bytes(_GENERATOR_PATH.read_bytes()),
        "prototype_path": str(Path(__file__).resolve().relative_to(_REPO_ROOT)),
        "prototype_sha256": _sha256_bytes(Path(__file__).read_bytes()),
    }
    _write_json(private_dir / "source_snapshot.json", source_snapshot)

    report = {
        "schema": f"{TASK_ID}-layer-order-evidence-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_LAYER_ORDERS),
            "default": DEFAULT_LAYER_ORDER,
        },
        "episode_count": len(records),
        "episodes": records,
        "all_racket_labels": True,
        "all_demonstrations_refute_rival": all(
            row["demonstrations_refute_rival"] for row in records
        ),
        "all_queries_differ_from_rival": all(
            row["all_queries_differ_from_rival"] for row in records
        ),
        "public_identifier_status": "exact_visible_bytes_only",
        "source_snapshot": "private/source_snapshot.json",
        "limits": [
            "authoring prototype only; it does not replace the production canonical rule",
            "evidence covers two-color overlapping bbox scenes and the two declared order values",
            "parameter identifiability is established against the paired order rival, not every conceivable rule",
        ],
    }
    _write_json(out_dir / "manifest.json", report)
    return report


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=1200)
    parser.add_argument("--train", type=int, default=3)
    parser.add_argument("--test", type=int, default=4)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    report = materialize(
        args.out,
        seed_start=args.seed_start,
        train_count=args.train,
        test_count=args.test,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
