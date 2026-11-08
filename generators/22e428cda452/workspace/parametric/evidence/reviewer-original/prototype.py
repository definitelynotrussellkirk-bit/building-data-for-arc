#!/usr/bin/env python3
"""Isolated episode-level projection-inset prototype for 22e428cda452.

This prototype preserves the original corner roles, colors, erasure, and
side-dependent glyphs while varying one small hidden rule parameter once per
episode: how far inward every projected glyph begins. The canonical/default
setting is one cell; the alternative is two cells. It does not modify the
selected production rule or generator labels.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge

TASK_ID = "22e428cda452"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_PROJECTION_INSETS = (1, 2)
DEFAULT_PROJECTION_INSET = 1

_CORNERS = (
    (1, lambda h, w: (0, 0)),
    (2, lambda h, w: (0, w - 1)),
    (4, lambda h, w: (h - 1, 0)),
    (8, lambda h, w: (h - 1, w - 1)),
)
_FIXTURE_MASKS = (5, 10, 15, 6)
_COLORS = (2, 3, 4, 5, 6, 8, 9, 0)


def _validate_inset(projection_inset: int) -> int:
    if type(projection_inset) is not int:
        raise TypeError("projection_inset must be an exact integer (not bool)")
    if projection_inset not in ALLOWED_PROJECTION_INSETS:
        raise ValueError(
            f"projection_inset must be one of {ALLOWED_PROJECTION_INSETS}"
        )
    return projection_inset


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def choose_projection_inset(seed: int) -> int:
    """Choose one hidden setting deterministically once for an episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}|projection_inset|{seed}".encode()).digest()
    return ALLOWED_PROJECTION_INSETS[digest[0] % len(ALLOWED_PROJECTION_INSETS)]


def make_input(variant: int = 0) -> list[list[int]]:
    """Build a lawful 10x10 scene that distinguishes both allowed insets."""
    if type(variant) is not int:
        raise TypeError("variant must be an exact integer")
    h = w = 10
    mask = _FIXTURE_MASKS[variant % len(_FIXTURE_MASKS)]
    grid = [[7 for _ in range(w)] for _ in range(h)]
    active = [item for item in _CORNERS if mask & item[0]]
    for index, (_, position) in enumerate(active):
        row, col = position(h, w)
        grid[row][col] = _COLORS[(variant + index) % len(_COLORS)]
    return grid


def _shape_offsets(top: bool, projection_inset: int):
    inset = _validate_inset(projection_inset)
    if top:
        return (
            (inset, inset),
            (inset, inset + 1),
            (inset + 1, inset),
            (inset + 1, inset + 1),
        )
    return (
        (inset + 2, inset + 1),
        (inset + 1, inset + 1),
        (inset, inset + 2),
    )


def apply_python(grid: list[list[int]], projection_inset: int) -> list[list[int]]:
    """Python assertion mirror; retained evidence is labeled by Racket."""
    inset = _validate_inset(projection_inset)
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    h, w = len(grid), len(grid[0])
    cells = []
    for _, position in _CORNERS:
        row, col = position(h, w)
        value = grid[row][col]
        if value != 7:
            cells.append((row, col, value))
    if not cells:
        raise ValueError("grid must contain at least one colored corner")

    output = deepcopy(grid)
    for row, col, _ in cells:
        output[row][col] = 7
    for row, col, color in cells:
        top = row == 0
        left = col == 0
        dr = 1 if top else -1
        dc = 1 if left else -1
        for row_offset, col_offset in _shape_offsets(top, inset):
            output[row + dr * row_offset][col + dc * col_offset] = color
    return output


def program_for(projection_inset: int) -> str:
    """Render the matching Racket authority candidate for one hidden setting."""
    inset = _validate_inset(projection_inset)
    top_a, top_b = inset, inset + 1
    bottom_a, bottom_b, bottom_c = inset + 2, inset + 1, inset
    bottom_col_a, bottom_col_c = inset + 1, inset + 2
    return f"""(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g)))
    (let* ((cells (filter (lambda (p) p)
                          (for*/list ((r (range 0 h)) (c (range 0 w)))
                            (and (!= (at g r c) 7)
                                 (list r c (at g r c))))))
           (base (recolor-cells g cells 7)))
      (reduce
        (lambda (acc cell)
          (let* ((cr (first cell))
                 (cc (second cell))
                 (cv (third cell))
                 (top (zero? cr))
                 (left (zero? cc))
                 (dr (if top 1 -1))
                 (dc (if left 1 -1))
                 (new-cells
                   (if top
                       (list (list (+ cr (* {top_a} dr)) (+ cc (* {top_a} dc)))
                             (list (+ cr (* {top_a} dr)) (+ cc (* {top_b} dc)))
                             (list (+ cr (* {top_b} dr)) (+ cc (* {top_a} dc)))
                             (list (+ cr (* {top_b} dr)) (+ cc (* {top_b} dc))))
                       (list (list (+ cr (* {bottom_a} dr)) (+ cc (* {bottom_col_a} dc)))
                             (list (+ cr (* {bottom_b} dr)) (+ cc (* {bottom_col_a} dc)))
                             (list (+ cr (* {bottom_c} dr)) (+ cc (* {bottom_col_c} dc)))))))
            (recolor-cells acc new-cells cv)))
        base
        cells)))))"""


def _rule_body(program: str) -> str:
    text = program.strip()
    prefix = "(rule!"
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("prototype program must be a (rule! BODY) form")
    return text[len(prefix) : -1].strip()


def apply_racket(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    bridge.define_grid("g", grid)
    body = _rule_body(program)
    output = bridge.eval_text(f"({body} g)")
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(
            not isinstance(row, list) or len(row) != len(output[0])
            for row in output
        )
    ):
        raise ValueError("Racket program did not return a nonempty rectangular grid")
    return output


def build_episode(
    seed: int,
    projection_inset: int | None = None,
) -> dict[str, Any]:
    """Build one complete hidden-setting episode with provisional Python labels."""
    _validate_seed(seed)
    setting = (
        choose_projection_inset(seed)
        if projection_inset is None
        else _validate_inset(projection_inset)
    )
    train = []
    for offset in range(3):
        grid = make_input(seed + offset)
        train.append({"input": grid, "output": apply_python(grid, setting)})
    query = make_input(seed + 103)
    return {
        "train": train,
        "test": {"input": query, "output": apply_python(query, setting)},
        "program": program_for(setting),
        "meta": {
            "seed": seed,
            "projection_inset": setting,
            "default_projection_inset": DEFAULT_PROJECTION_INSET,
            "setting_selected_once": True,
            "prototype_version": PROTOTYPE_VERSION,
        },
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    setting = _validate_inset(episode["meta"]["projection_inset"])
    rival = next(value for value in ALLOWED_PROJECTION_INSETS if value != setting)
    findings: list[str] = []
    if not any(
        apply_python(pair["input"], rival) != pair["output"]
        for pair in episode["train"]
    ):
        findings.append(f"rival projection_inset={rival} fits every demonstration")
    if apply_python(episode["test"]["input"], rival) == episode["test"]["output"]:
        findings.append(f"query does not distinguish projection_inset={rival}")
    return findings


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "22e428cda452-projection-inset-public-v1",
        "train": deepcopy(episode["train"]),
        "test": {"input": deepcopy(episode["test"]["input"])},
    }


def _json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _find_seed_for(setting: int, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_projection_inset(seed) != setting:
        seed += 1
    return seed


def materialize(out_dir: Path, seed_start: int = 431) -> dict[str, Any]:
    """Execute both settings in Racket and retain private/public evidence."""
    out_dir = Path(out_dir)
    private_dir = out_dir / "private"
    public_dir = out_dir / "public"
    program_dir = private_dir / "programs"
    for directory in (out_dir, private_dir, public_dir, program_dir):
        directory.mkdir(parents=True, exist_ok=True)

    used: set[int] = set()
    records = []
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for index, setting in enumerate(ALLOWED_PROJECTION_INSETS):
            seed = _find_seed_for(setting, seed_start + index, used)
            used.add(seed)
            episode = build_episode(seed)
            assert episode["meta"]["projection_inset"] == setting
            program = episode["program"]
            (program_dir / f"projection-inset-{setting}.rkt").write_text(
                program + "\n"
            )

            for pair in episode["train"]:
                racket_output = apply_racket(bridge, program, pair["input"])
                assert racket_output == apply_python(pair["input"], setting)
                pair["output"] = racket_output
            racket_query = apply_racket(bridge, program, episode["test"]["input"])
            assert racket_query == apply_python(episode["test"]["input"], setting)
            episode["test"]["output"] = racket_query
            findings = parameter_rival_findings(episode)
            if findings:
                raise AssertionError(findings)

            private_path = private_dir / f"episode-{setting}.json"
            private_path.write_text(json.dumps(episode, indent=2) + "\n")
            public = public_challenge(episode)
            public_path = public_dir / f"episode-{setting}.json"
            public_path.write_text(json.dumps(public, indent=2) + "\n")
            rival = next(
                value for value in ALLOWED_PROJECTION_INSETS if value != setting
            )
            records.append(
                {
                    "seed": seed,
                    "projection_inset": setting,
                    "rival_projection_inset": rival,
                    "demonstration_differences": [
                        index
                        for index, pair in enumerate(episode["train"])
                        if apply_python(pair["input"], rival) != pair["output"]
                    ],
                    "query_differs": (
                        apply_python(episode["test"]["input"], rival)
                        != episode["test"]["output"]
                    ),
                    "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                    "public_sha256": _json_sha256(public),
                    "private_path": str(private_path.relative_to(out_dir)),
                    "public_path": str(public_path.relative_to(out_dir)),
                }
            )
    finally:
        bridge.shutdown()

    report = {
        "schema": "22e428cda452-projection-inset-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "projection_inset",
            "allowed_values": list(ALLOWED_PROJECTION_INSETS),
            "canonical_default": DEFAULT_PROJECTION_INSET,
            "selection_scope": "once per episode",
        },
        "complete_episodes": len(records),
        "all_labels_executed_in_racket": True,
        "all_demonstrations_refute_other_setting": all(
            bool(record["demonstration_differences"]) for record in records
        ),
        "all_queries_distinguish_other_setting": all(
            record["query_differs"] for record in records
        ),
        "records": records,
        "limits": [
            "Only insets 1 and 2 are assessed.",
            "Fixtures are controlled 10x10 corner scenes, not a production sampler.",
            "Finite two-setting evidence does not prove universal identifiability.",
        ],
    }
    (out_dir / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "evidence" / "retained",
    )
    parser.add_argument("--seed-start", type=int, default=431)
    args = parser.parse_args()
    report = materialize(args.out, seed_start=args.seed_start)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
