#!/usr/bin/env python3
"""Separate authoring prototype for a fixed-per-episode triangle render mode.

``outline`` is the byte-exact canonical/default behavior. ``solid`` keeps the
same square-corner inference and triangle orientation but fills the selected
triangle. The setting is chosen once from the episode seed and shared by every
demonstration and query. This module does not alter production generation or
canonical authority.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "1238481b674b"
ALLOWED_RENDER_MODES = ("outline", "solid")
DEFAULT_RENDER_MODE = "outline"
PROTOTYPE_VERSION = "1.0.0"
DEMO_INDICES = (0, 1, 2, 3)
QUERY_INDEX = 4
DIFFICULTY = "medium"
PROTOTYPE_DIR = Path(__file__).resolve().parent
RULE_DIR = PROTOTYPE_DIR / "racket"

_RENDER_MARKER = "    ;; Draw the two square sides incident to the missing corner and the\n"
_SOLID_RENDER_BLOCK = """    ;; Fill the triangle selected by the same missing-corner inference.
    (define (local-r u)
      (if (or (= missing 0) (= missing 1))
          (+ r0 u)
          (- r1 u)))
    (define (local-c v)
      (if (or (= missing 0) (= missing 2))
          (+ c0 v)
          (- c1 v)))
    (define (paint-solid acc)
      (reduce
        (lambda (a u)
          (reduce
            (lambda (b v)
              (if (<= (+ u v) d)
                  (paint-if-bg b (local-r u) (local-c v))
                  b))
            a
            (range 0 (+ d 1))))
        acc
        (range 0 (+ d 1))))
    (paint-solid g))))"""


def _validate_render_mode(render_mode: str) -> str:
    if not isinstance(render_mode, str) or render_mode not in ALLOWED_RENDER_MODES:
        raise ValueError(
            f"render_mode must be one of {ALLOWED_RENDER_MODES}, got {render_mode!r}"
        )
    return render_mode


def choose_render_mode(seed: int) -> str:
    """Choose exactly one hidden setting for an entire episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return ALLOWED_RENDER_MODES[seed % len(ALLOWED_RENDER_MODES)]



def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def _triangle_facts(grid: list[list[int]]) -> dict[str, int]:
    _validate_grid(grid)
    marks = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(marks) != 4:
        raise ValueError(f"render-mode prototype requires exactly four gray cells, found {len(marks)}")
    if {value for row in grid for value in row} - {5, 7}:
        raise ValueError("render-mode prototype input palette must contain only orange 7 and gray 5")
    r0 = min(r for r, _ in marks)
    r1 = max(r for r, _ in marks)
    c0 = min(c for _, c in marks)
    c1 = max(c for _, c in marks)
    if r1 - r0 != c1 - c0 or r1 == r0:
        raise ValueError("gray extrema must define a nondegenerate square")
    corners = ((r0, c0), (r0, c1), (r1, c0), (r1, c1))
    present = [corner in marks for corner in corners]
    if sum(present) != 3:
        raise ValueError("exactly three gray cells must occupy square corners")
    missing = present.index(False)
    distractors = [mark for mark in marks if mark not in corners]
    if len(distractors) != 1:
        raise ValueError("exactly one gray cell must be the interior distractor")
    distractor_r, distractor_c = distractors[0]
    if not (r0 < distractor_r < r1 and c0 < distractor_c < c1):
        raise ValueError("the fourth gray cell must be strictly interior to the square")
    return {"r0": r0, "r1": r1, "c0": c0, "c1": c1, "d": r1 - r0, "missing": missing}


def _local_to_grid(facts: dict[str, int], u: int, v: int) -> tuple[int, int]:
    missing = facts["missing"]
    r = facts["r0"] + u if missing in (0, 1) else facts["r1"] - u
    c = facts["c0"] + v if missing in (0, 2) else facts["c1"] - v
    return r, c


def python_transform(grid: list[list[int]], render_mode: str) -> list[list[int]]:
    """Independent diagnostic mirror; retained labels are executed by Racket."""
    mode = _validate_render_mode(render_mode)
    facts = _triangle_facts(grid)
    output = copy.deepcopy(grid)
    d = facts["d"]
    for u in range(d + 1):
        for v in range(d + 1 - u):
            boundary = u == 0 or v == 0 or u + v == d
            if mode == "solid" or boundary:
                r, c = _local_to_grid(facts, u, v)
                if output[r][c] == 7:
                    output[r][c] = 8
    return output

def normalized_hash(source: str) -> str:
    """Return the repository's 12-hex whitespace-normalized Racket hash."""
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


def _solid_source(canonical: str) -> str:
    count = canonical.count(_RENDER_MARKER)
    if count != 1:
        raise ValueError(
            f"expected exactly one canonical render marker, found {count}"
        )
    prefix, _ = canonical.split(_RENDER_MARKER, 1)
    return prefix + _SOLID_RENDER_BLOCK


def racket_source(render_mode: str, *, root: Path | str) -> str:
    """Return a complete exact Racket rule for one bounded setting."""
    mode = _validate_render_mode(render_mode)
    canonical = _canonical_source(root=Path(root))
    return canonical if mode == "outline" else _solid_source(canonical)


def racket_sha256(render_mode: str, *, root: Path | str) -> str:
    return hashlib.sha256(
        racket_source(render_mode, root=root).encode("utf-8")
    ).hexdigest()


def rule_path(render_mode: str) -> Path:
    return RULE_DIR / f"{_validate_render_mode(render_mode)}.rkt"


def materialize_rules(*, root: Path | str) -> dict[str, str]:
    """Write both complete sources and return their raw SHA-256 hashes."""
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for mode in ALLOWED_RENDER_MODES:
        source = racket_source(mode, root=root)
        rule_path(mode).write_text(source, encoding="utf-8")
        hashes[mode] = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return hashes


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
    callable_source = stripped[len(prefix):-1].strip()
    if not callable_source.startswith("(lambda "):
        raise ValueError("prototype rule body must be a lambda")
    return callable_source


def _racket_outputs(source: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute a complete retained rule through the bundled Racket bridge."""
    from arc_repl.racket_bridge import RacketBridge

    callable_source = _callable_racket_source(source)
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define prototype-rule {callable_source})")
        result = bridge.eval_text(f"(map prototype-rule '{_racket_literal(grids)})")
    if not isinstance(result, list) or len(result) != len(grids):
        raise RuntimeError("unexpected Racket result shape")
    return result


def build_episode(*, root: Path | str, seed: int) -> dict[str, Any]:
    """Build four demonstrations and one query, all labelled by exact Racket."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    root = Path(root).resolve()
    mode = choose_render_mode(seed)
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    indexed_inputs = [
        (index, module.generate(seed, index, difficulty=DIFFICULTY))
        for index in (*DEMO_INDICES, QUERY_INDEX)
    ]
    inputs = [grid for _, grid in indexed_inputs]
    source = racket_source(mode, root=root)
    outputs = _racket_outputs(source, inputs)
    diagnostic = [python_transform(grid, mode) for grid in inputs]
    if outputs != diagnostic:
        raise AssertionError(f"{mode}: Racket labels disagree with Python diagnostic")
    pairs = [
        {
            "sample_index": index,
            "render_mode": mode,
            "input": copy.deepcopy(grid),
            "output": copy.deepcopy(output),
        }
        for (index, grid), output in zip(indexed_inputs, outputs)
    ]
    return {
        "schema": "arcpuzzles-parametric-triangle-render-episode-v1",
        "status": "prototype",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": DIFFICULTY,
        "parameter": {"render_mode": mode},
        "label_authority": "executed_racket",
        "racket_rule_hash": normalized_hash(source),
        "selected_generator_path": str(source_path.relative_to(root)),
        "selected_generator_sha256": source_sha,
        "train": pairs[:-1],
        "test": pairs[-1:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Expose labelled demonstrations and an unlabelled query only."""
    return {
        "schema": "arcpuzzles-parametric-triangle-render-public-v1",
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _racket_runtime_metadata() -> dict[str, str]:
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
) -> dict[str, Any]:
    """Execute both settings and retain bounded, source-bound evidence."""
    root = Path(root).resolve()
    seeds = dict(seeds or {"outline": 18, "solid": 19})
    if set(seeds) != set(ALLOWED_RENDER_MODES):
        raise ValueError(f"seeds must have exactly keys {ALLOWED_RENDER_MODES}")
    for mode, seed in seeds.items():
        if choose_render_mode(seed) != mode:
            raise ValueError(
                f"seed {seed} selects {choose_render_mode(seed)!r}, not {mode!r}"
            )

    rule_hashes = materialize_rules(root=root)
    module, selected_path, selected_sha = load_selected_generator(TASK_ID, root=root)
    sources = {mode: racket_source(mode, root=root) for mode in ALLOWED_RENDER_MODES}
    if sources[DEFAULT_RENDER_MODE] != _canonical_source(root=root):
        raise AssertionError("outline setting is not byte-exact canonical source")
    if normalized_hash(sources[DEFAULT_RENDER_MODE]) != module.RULE_HASH:
        raise AssertionError("default prototype no longer matches selected RULE_HASH")

    settings: dict[str, Any] = {}
    public: dict[str, Any] = {}
    all_pairs_disagree = True
    for mode in ALLOWED_RENDER_MODES:
        alternative = "solid" if mode == "outline" else "outline"
        episode = build_episode(root=root, seed=seeds[mode])
        pairs = [*episode["train"], *episode["test"]]
        inputs = [pair["input"] for pair in pairs]
        actual_outputs = [pair["output"] for pair in pairs]
        alternative_outputs = _racket_outputs(sources[alternative], inputs)
        python_outputs = [python_transform(grid, mode) for grid in inputs]
        if actual_outputs != python_outputs:
            raise AssertionError(f"{mode}: retained Racket labels disagree with Python")

        executed_pairs = []
        for offset, (pair, actual, rival) in enumerate(
            zip(pairs, actual_outputs, alternative_outputs)
        ):
            disagreement = actual != rival
            all_pairs_disagree &= disagreement
            split = "train" if offset < len(episode["train"]) else "test"
            pair_index = offset if split == "train" else offset - len(episode["train"])
            executed_pairs.append(
                {
                    "split": split,
                    "pair_index": pair_index,
                    "sample_index": pair["sample_index"],
                    "input": pair["input"],
                    "racket_output": actual,
                    "alternative_render_mode": alternative,
                    "alternative_racket_output": rival,
                    "settings_disagree": disagreement,
                    "input_sha256": _digest(pair["input"]),
                    "output_sha256": _digest(actual),
                }
            )
        demo_flags = [
            row["settings_disagree"]
            for row in executed_pairs
            if row["split"] == "train"
        ]
        query_flags = [
            row["settings_disagree"]
            for row in executed_pairs
            if row["split"] == "test"
        ]
        if not demo_flags or not all(demo_flags):
            raise AssertionError(f"{mode}: not every demo refutes {alternative}")
        if not query_flags or not all(query_flags):
            raise AssertionError(f"{mode}: query does not require the setting")

        settings[mode] = {
            "render_mode": mode,
            "is_canonical_default": mode == DEFAULT_RENDER_MODE,
            "seed": seeds[mode],
            "difficulty": DIFFICULTY,
            "demonstration_indices": list(DEMO_INDICES),
            "query_index": QUERY_INDEX,
            "racket_path": str(rule_path(mode).relative_to(root)),
            "racket_text": sources[mode],
            "racket_sha256": rule_hashes[mode],
            "racket_rule_hash": normalized_hash(sources[mode]),
            "episode": episode,
            "executed_pairs": executed_pairs,
            "all_pairs_match_python_and_racket": True,
            "every_demo_refutes_alternative_setting": all(demo_flags),
            "query_requires_setting": all(query_flags),
        }
        public[mode] = public_challenge(episode)

    if not all_pairs_disagree:
        raise AssertionError("at least one retained pair does not distinguish settings")

    return {
        "schema": "arcpuzzles-parametric-triangle-render-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "render_mode",
            "allowed_values": list(ALLOWED_RENDER_MODES),
            "canonical_default": DEFAULT_RENDER_MODE,
            "selection": "ALLOWED_RENDER_MODES[seed % 2], once per episode",
            "input_constraints": (
                "Same selected-generator grammar: orange background, three square-corner "
                "gray clues, and one strictly interior gray distractor. Side length must "
                "leave at least one non-gray strict interior cell so demos distinguish "
                "outline from solid."
            ),
        },
        "invariants_across_settings": [
            "infer the axis-aligned square from the same four gray cells",
            "use the absent square corner as the triangle apex",
            "preserve every gray clue and all cells outside the selected triangle",
            "paint only orange background cells with color 8",
            "change only boundary-only versus full-triangle rendering",
        ],
        "prototype_source_path": str(Path(__file__).resolve().relative_to(root)),
        "prototype_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "selected_generator_path": str(selected_path.relative_to(root)),
        "selected_generator_sha256": selected_sha,
        "racket_runtime": _racket_runtime_metadata(),
        "settings": settings,
        "public_challenges": public,
        "all_retained_pairs_distinguish_settings": all_pairs_disagree,
        "limits": [
            "Bounded evidence for outline seed 18 and solid seed 19, not production approval.",
            "The selected generator and canonical authority remain fixed to outline.",
            "The demonstrations distinguish only the declared outline/solid rival.",
            "Malformed grids and other hidden rule families remain outside this prototype.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    parser.add_argument("--outline-seed", type=int, default=18)
    parser.add_argument("--solid-seed", type=int, default=19)
    args = parser.parse_args()

    root = find_root(__file__)
    report = build_report(
        root=root,
        seeds={"outline": args.outline_seed, "solid": args.solid_seed},
    )
    report["execution"] = {"argv": list(sys.argv), "cwd": os.getcwd()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for mode, challenge in report["public_challenges"].items():
            (args.write_public / f"{mode}_public.json").write_text(
                json.dumps(challenge, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
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
