"""Executable evidence builder for a proposed rectangle expansion-mode parameter.

The canonical/default mode repaints the full rectangle-marker bounding box.
The alternate mode preserves the source rectangle and draws only a frame-color
corridor to the marker.  The hidden mode is sampled once per four-pair episode,
never once per pair.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import random
import sys
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "a3c33cc348fb"
PROTOTYPE_VERSION = "expansion-mode-prototype-v1"
ALLOWED_EXPANSION_MODES = ("bbox", "corridor")
DEFAULT_EXPANSION_MODE = "bbox"
TRAIN_COUNT = 3
PAIR_COUNT = 4
INPUT_PROFILES = ("near_reach", "left_reach", "corner_reach", "far_reach")
INPUT_DIFFICULTIES = ("easy", "medium", "hard", "medium")

LIMITATIONS = [
    "Task-local proposal only; it does not change the production generator, canonical rule, catalog, or approval state.",
    "The default expansion_mode='bbox' program is byte-for-byte the canonical Racket program.",
    "Only expansion_mode in {'bbox','corridor'} is supported; marker color, frame/interior roles, and input grammar remain fixed.",
    "The mode is chosen once per episode from a rule-only deterministic stream; inputs come from a separate stream.",
    "Evidence retains two episodes (one per mode), four query rotations per episode, and the single declared rival mode.",
    "Finite examples refute the declared rival but do not prove identification against arbitrary programs or establish training suitability.",
    "The labeled execution canary validates runtime plumbing and is not part of either public episode.",
]

CORRIDOR_RULE = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((cyan (first (find-color g 8)))
                  (cr (first cyan))
                  (cc (second cyan))
                  (non-bg (flatmap (lambda (r)
                                     (flatmap (lambda (c)
                                                (let ((v (at g r c)))
                                                  (if (and (!= v 0) (!= v 8))
                                                      (list (list r c v))
                                                      (list))))
                                              (range 0 w)))
                                   (range 0 h)))
                  (rs (map first non-bg))
                  (cs (map second non-bg))
                  (r1 (min-list rs))
                  (r2 (max-list rs))
                  (c1 (min-list cs))
                  (c2 (max-list cs))
                  (frame-col (at g r1 c1)))
             (cellmap g
                      (r c v)
                      (cond
                        ((and (>= r r1) (<= r r2) (>= c c1) (<= c c2)) v)
                        ((and (= r cr)
                              (or (and (< cc c1) (>= c cc) (< c c1))
                                  (and (> cc c2) (> c c2) (<= c cc))))
                         frame-col)
                        ((and (= c cc)
                              (or (and (< cr r1) (>= r cr) (< r r1))
                                  (and (> cr r2) (> r r2) (<= r cr))))
                         frame-col)
                        (else 0)))))))"""


def _validate_mode(expansion_mode: Any) -> str:
    if type(expansion_mode) is not str or expansion_mode not in ALLOWED_EXPANSION_MODES:
        raise ValueError(
            f"expansion_mode must be one of {ALLOWED_EXPANSION_MODES}, "
            f"got {expansion_mode!r}"
        )
    return expansion_mode


@lru_cache(maxsize=1)
def _canonical_rule() -> str:
    root = find_root(__file__)
    rows = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    programs = {row["program_solution"] for row in rows}
    if len(programs) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}, got {len(programs)}")
    return programs.pop()


def rule_source(expansion_mode: Any) -> str:
    """Return exact executable Racket for one declared parameter setting."""
    mode = _validate_mode(expansion_mode)
    return _canonical_rule() if mode == "bbox" else CORRIDOR_RULE


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be literal ARC colors 0..9")
    return len(grid), width


def _analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    if len(markers) != 1:
        raise ValueError(f"grid must contain exactly one cyan marker, got {len(markers)}")
    cells = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 8)
    ]
    if not cells:
        raise ValueError("grid must contain a non-background rectangle")
    rows = [row for row, _, _ in cells]
    cols = [col for _, col, _ in cells]
    row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
    marker_row, marker_col = markers[0]
    frame_color = grid[row0][col0]
    inner_color = next(
        (value for _, _, value in cells if value != frame_color), frame_color
    )
    if marker_col < col0 and row0 <= marker_row <= row1:
        side = "left"
    elif marker_col > col1 and row0 <= marker_row <= row1:
        side = "right"
    elif marker_row < row0 and col0 <= marker_col <= col1:
        side = "top"
    elif marker_row > row1 and col0 <= marker_col <= col1:
        side = "bottom"
    else:
        raise ValueError("marker must be outside and aligned with the rectangle")
    return {
        "height": height,
        "width": width,
        "bbox": (row0, col0, row1, col1),
        "marker": (marker_row, marker_col),
        "frame_color": frame_color,
        "inner_color": inner_color,
        "side": side,
    }


def python_mirror(grid: list[list[int]], expansion_mode: Any) -> list[list[int]]:
    """Independent mirror used only to cross-check executed Racket outputs."""
    mode = _validate_mode(expansion_mode)
    facts = _analyze(grid)
    height, width = facts["height"], facts["width"]
    row0, col0, row1, col1 = facts["bbox"]
    marker_row, marker_col = facts["marker"]
    frame_color = facts["frame_color"]
    output = [[0 for _ in range(width)] for _ in range(height)]

    if mode == "bbox":
        new_row0, new_row1 = min(row0, marker_row), max(row1, marker_row)
        new_col0, new_col1 = min(col0, marker_col), max(col1, marker_col)
        for row in range(new_row0, new_row1 + 1):
            for col in range(new_col0, new_col1 + 1):
                output[row][col] = (
                    frame_color
                    if row in (new_row0, new_row1) or col in (new_col0, new_col1)
                    else facts["inner_color"]
                )
        return output

    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            output[row][col] = grid[row][col]
    if facts["side"] == "left":
        for col in range(marker_col, col0):
            output[marker_row][col] = frame_color
    elif facts["side"] == "right":
        for col in range(col1 + 1, marker_col + 1):
            output[marker_row][col] = frame_color
    elif facts["side"] == "top":
        for row in range(marker_row, row0):
            output[row][marker_col] = frame_color
    else:
        for row in range(row1 + 1, marker_row + 1):
            output[row][marker_col] = frame_color
    return output


def _stream_rng(seed: int, stream: str) -> random.Random:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    digest = hashlib.sha256(
        f"{PROTOTYPE_VERSION}:{stream}:{seed}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def expansion_mode_for_seed(seed: int) -> str:
    """Choose the hidden mode once from an episode-only deterministic stream."""
    return _stream_rng(seed, "rule").choice(ALLOWED_EXPANSION_MODES)


@lru_cache(maxsize=1)
def _selected_generator():
    module, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))
    return module


def sample_inputs(seed: int) -> list[list[list[int]]]:
    """Draw four lawful inputs from a stream independent of the hidden mode."""
    rng = _stream_rng(seed, "inputs")
    module = _selected_generator()
    inputs = []
    for pair_index, (profile, difficulty) in enumerate(
        zip(INPUT_PROFILES, INPUT_DIFFICULTIES, strict=True)
    ):
        pair_seed = rng.getrandbits(63)
        sample_index = rng.randrange(1_000_000)
        grid = module.generate(
            pair_seed,
            sample_index,
            difficulty=difficulty,
            scene_profile=profile,
        )
        if module.self_check(grid):
            raise RuntimeError(f"production generator returned an invalid {profile} input")
        if python_mirror(grid, "bbox") == python_mirror(grid, "corridor"):
            raise RuntimeError(f"sampled {profile} input does not distinguish the modes")
        inputs.append(grid)
    fingerprints = {_json_sha256(grid) for grid in inputs}
    if len(fingerprints) != PAIR_COUNT:
        raise RuntimeError("episode input sampler produced duplicate grids")
    return inputs


def sample_episode(seed: int) -> dict[str, Any]:
    mode = expansion_mode_for_seed(seed)
    inputs = sample_inputs(seed)
    return {
        "episode_id": "episode-" + _json_sha256(inputs)[:16],
        "seed": seed,
        "parameters": {"expansion_mode": mode},
        "program": rule_source(mode),
        "inputs": inputs,
        "train_count": TRAIN_COUNT,
    }


def select_seeds(base_seed: int) -> dict[str, Any]:
    if type(base_seed) is not int:
        raise TypeError("base_seed must be a literal integer")
    found: dict[str, int] = {}
    examined = 0
    for seed in range(base_seed, base_seed + 1000):
        examined += 1
        found.setdefault(expansion_mode_for_seed(seed), seed)
        if set(found) == set(ALLOWED_EXPANSION_MODES):
            break
    if set(found) != set(ALLOWED_EXPANSION_MODES):
        raise RuntimeError("could not find one deterministic seed per setting")
    return {
        "base_seed": base_seed,
        "examined_seeds": examined,
        "by_expansion_mode": {
            mode: found[mode] for mode in ALLOWED_EXPANSION_MODES
        },
        "seeds": [found[mode] for mode in ALLOWED_EXPANSION_MODES],
    }


def public_challenge(
    pairs: list[dict[str, Any]], query_index: int = TRAIN_COUNT
) -> dict[str, Any]:
    if (
        type(query_index) is not int
        or len(pairs) != PAIR_COUNT
        or not 0 <= query_index < len(pairs)
    ):
        raise ValueError(f"query_index must select one of exactly {PAIR_COUNT} pairs")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for index, pair in enumerate(pairs)
            if index != query_index
        ],
        "test": [{"input": deepcopy(pairs[query_index]["input"])}],
    }


def score_rotation(
    predictions: dict[str, list[list[list[int]]]],
    chosen_mode: Any,
    query_index: int,
) -> dict[str, Any]:
    chosen = _validate_mode(chosen_mode)
    if set(predictions) != set(ALLOWED_EXPANSION_MODES):
        raise ValueError("predictions must cover every declared expansion_mode")
    length = len(predictions[chosen])
    if (
        length != PAIR_COUNT
        or type(query_index) is not int
        or not 0 <= query_index < length
    ):
        raise ValueError("inconsistent predictions or query index")
    if any(len(outputs) != length for outputs in predictions.values()):
        raise ValueError("inconsistent prediction lengths")
    demos = [index for index in range(length) if index != query_index]
    rivals = []
    for mode in ALLOWED_EXPANSION_MODES:
        if mode == chosen:
            continue
        mismatches = [
            index
            for index in demos
            if predictions[mode][index] != predictions[chosen][index]
        ]
        query_disagrees = predictions[mode][query_index] != predictions[chosen][query_index]
        status = (
            "refuted_by_demonstrations"
            if mismatches
            else "ambiguous_query"
            if query_disagrees
            else "survived_all"
        )
        rivals.append(
            {
                "expansion_mode": mode,
                "status": status,
                "demonstration_mismatches": mismatches,
                "query_disagrees": query_disagrees,
            }
        )
    return {
        "query_pair_index": query_index,
        "demonstration_pair_indices": demos,
        "is_production_query": query_index == TRAIN_COUNT,
        "rivals": rivals,
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha256(value: Any) -> str:
    return _sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _source_bindings() -> dict[str, str]:
    from arc_repl import isolated_verifier, racket_bridge

    here = Path(__file__).resolve()
    root = find_root(here)
    task_home = here.parents[2]
    paths = [
        here,
        here.with_name("README.md"),
        task_home / "generator.py",
        task_home / "tests/test_repair_contracts.py",
        task_home / "tests/test_parametric_expansion_mode.py",
        canonical_path(root),
        Path(isolated_verifier.__file__).resolve(),
        Path(racket_bridge.__file__).resolve(),
        Path(racket_bridge.__file__).with_name("executor.py").resolve(),
        Path(racket_bridge.__file__).parent / "racket_prelude/arc-prelude.rkt",
    ]
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in paths
    }


def run_evidence(
    out: Path,
    *,
    base_seed: int = 20261022,
    racket_path: str | None = None,
) -> dict[str, Any]:
    """Execute both parameter settings with the isolated real-Racket verifier."""
    from arc_repl.isolated_verifier import verify_candidate

    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/rules").mkdir(parents=True)
    (out / "private/racket").mkdir(parents=True)
    (out / "private/episodes").mkdir(parents=True)

    selection = select_seeds(base_seed)
    report: dict[str, Any] = {
        "schema": "parametric-expansion-mode-evidence-v1",
        "status": "running",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_contract": {
            "name": "expansion_mode",
            "allowed_values": list(ALLOWED_EXPANSION_MODES),
            "original_default": DEFAULT_EXPANSION_MODE,
            "sampling_unit": "once per episode from a rule-only deterministic seed stream",
            "input_stream": "separate deterministic stream independent of expansion_mode",
        },
        "seed_selection": selection,
        "rules": [],
        "episodes": [],
        "limitations": LIMITATIONS,
        "invocation": {
            "argv": list(sys.argv),
            "cwd": str(Path.cwd()),
            "python_executable": sys.executable,
            "python_version": sys.version,
        },
    }
    _write_json(out / "report.json", report)

    try:
        report["source_sha256"] = _source_bindings()
        chosen_racket = racket_path if racket_path is not None else os.environ.get("RACKET_PATH", "")
        binary = Path(chosen_racket).resolve(strict=True)
        report["runtime"] = {
            "backend": "racket",
            "public_api": "arc_repl.isolated_verifier.verify_candidate",
            "racket_path": str(binary),
            "racket_sha256": _sha256(binary.read_bytes()),
        }

        episodes = [sample_episode(seed) for seed in selection["seeds"]]
        execution_inputs = [
            {
                "episode_id": episode["episode_id"],
                "pair_index": pair_index,
                "input": grid,
                "input_sha256": _json_sha256(grid),
            }
            for episode in episodes
            for pair_index, grid in enumerate(episode["inputs"])
        ]
        _write_json(out / "private/execution_inputs.json", execution_inputs)

        predictions: dict[str, list[list[list[int]]]] = {}
        parity_matches = 0
        for mode in ALLOWED_EXPANSION_MODES:
            program = rule_source(mode)
            program_sha = _sha256(program.encode("utf-8"))
            rule_rel = f"private/rules/expansion_mode_{mode}.rkt"
            receipt_rel = f"private/racket/expansion_mode_{mode}.json"
            (out / rule_rel).write_text(program + "\n", encoding="utf-8")
            report["rules"].append(
                {
                    "parameters": {"expansion_mode": mode},
                    "source": program,
                    "sha256": program_sha,
                    "path": rule_rel,
                    "execution_path": receipt_rel,
                    "canonical_default": mode == DEFAULT_EXPANSION_MODE,
                }
            )

            canary_input = execution_inputs[0]["input"]
            canary = {
                "input": canary_input,
                "output": python_mirror(canary_input, mode),
            }
            task = {
                "train": [canary],
                "test": [{"input": row["input"]} for row in execution_inputs],
            }
            receipt = verify_candidate(task, program, racket_path=str(binary))
            _write_json(
                out / receipt_rel,
                {
                    "program": program,
                    "program_sha256": program_sha,
                    "canary": canary,
                    "input_order": "../execution_inputs.json",
                    "input_sha256": [row["input_sha256"] for row in execution_inputs],
                    "receipt": receipt,
                },
            )
            if receipt.get("status") != "pass" or receipt.get("backend") != "racket":
                raise RuntimeError(
                    f"Racket execution failed for expansion_mode={mode}: "
                    f"{receipt.get('error')}"
                )
            predictions[mode] = receipt["test_outputs"]
            for row, observed in zip(execution_inputs, predictions[mode], strict=True):
                expected = python_mirror(row["input"], mode)
                if observed != expected:
                    _write_json(
                        out / "private/parity_failure.json",
                        {
                            "expansion_mode": mode,
                            "input": row["input"],
                            "racket_output": observed,
                            "python_mirror": expected,
                        },
                    )
                    raise RuntimeError(f"Racket/Python mismatch at expansion_mode={mode}")
                parity_matches += 1

        offset = 0
        rotation_rows = []
        for episode in episodes:
            chosen = episode["parameters"]["expansion_mode"]
            episode_predictions = {
                mode: predictions[mode][offset : offset + PAIR_COUNT]
                for mode in ALLOWED_EXPANSION_MODES
            }
            offset += PAIR_COUNT
            pairs = [
                {"input": grid, "output": output}
                for grid, output in zip(
                    episode["inputs"], episode_predictions[chosen], strict=True
                )
            ]
            rotations = [
                score_rotation(episode_predictions, chosen, query_index)
                for query_index in range(PAIR_COUNT)
            ]
            rotation_rows.extend(rotations)
            public = public_challenge(pairs)
            public_rel = f"public/{episode['episode_id']}.json"
            private_rel = f"private/episodes/{episode['episode_id']}.json"
            _write_json(out / public_rel, public)
            public_text = (out / public_rel).read_text(encoding="utf-8")
            if "expansion_mode" in public_text or "program" in public_text:
                raise RuntimeError("public challenge leaked a hidden parameter or program")
            _write_json(
                out / private_rel,
                {
                    "episode_id": episode["episode_id"],
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "program": episode["program"],
                    "program_sha256": _sha256(episode["program"].encode("utf-8")),
                    "pairs": pairs,
                    "cross_setting_outputs": {
                        mode: episode_predictions[mode]
                        for mode in ALLOWED_EXPANSION_MODES
                    },
                    "rotations": rotations,
                    "public_path": public_rel,
                    "public_sha256": _sha256((out / public_rel).read_bytes()),
                },
            )
            report["episodes"].append(
                {
                    "episode_id": episode["episode_id"],
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "public_path": public_rel,
                    "public_sha256": _sha256((out / public_rel).read_bytes()),
                    "private_path": private_rel,
                    "private_sha256": _sha256((out / private_rel).read_bytes()),
                }
            )

        witness = execution_inputs[0]["input"]
        witness_outputs = {
            mode: predictions[mode][0] for mode in ALLOWED_EXPANSION_MODES
        }
        _write_json(
            out / "private/cross_setting_witness.json",
            {
                "input": witness,
                "input_sha256": _json_sha256(witness),
                "outputs": witness_outputs,
                "output_sha256": {
                    mode: _json_sha256(output)
                    for mode, output in witness_outputs.items()
                },
                "pairwise_outputs_distinct": len(
                    {_json_sha256(output) for output in witness_outputs.values()}
                )
                == len(ALLOWED_EXPANSION_MODES),
            },
        )

        rival_rows = [
            rival for rotation in rotation_rows for rival in rotation["rivals"]
        ]
        report["summary"] = {
            "episodes": len(episodes),
            "episode_pairs": len(execution_inputs),
            "racket_rule_applications": len(execution_inputs)
            * len(ALLOWED_EXPANSION_MODES),
            "racket_canaries": len(ALLOWED_EXPANSION_MODES),
            "python_mirror_matches": parity_matches,
            "query_rotations": len(rotation_rows),
            "rotation_rival_checks": len(rival_rows),
            "refuted_rotation_rivals": sum(
                row["status"] == "refuted_by_demonstrations" for row in rival_rows
            ),
            "ambiguous_rotation_rivals": sum(
                row["status"] == "ambiguous_query" for row in rival_rows
            ),
            "survived_rotation_rivals": sum(
                row["status"] == "survived_all" for row in rival_rows
            ),
        }
        if _source_bindings() != report["source_sha256"]:
            raise RuntimeError("bound source files changed during evidence execution")
        report["status"] = (
            "pass"
            if all(row["status"] == "refuted_by_demonstrations" for row in rival_rows)
            else "ambiguity"
        )
    except Exception as exc:  # Evidence must retain failures rather than disappear.
        report["status"] = "error"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}

    _write_json(out / "report.json", report)
    manifest = {
        "schema": "parametric-evidence-manifest-v1",
        "status": report["status"],
        "task_id": TASK_ID,
        "report": "report.json",
        "report_sha256": _sha256((out / "report.json").read_bytes()),
        "public_challenges": [
            row["public_path"] for row in report.get("episodes", [])
        ],
        "private_evidence": [
            row["private_path"] for row in report.get("episodes", [])
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-seed", type=int, default=20261022)
    args = parser.parse_args(argv)
    report = run_evidence(args.out, base_seed=args.base_seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "summary": report.get("summary"),
                "error": report.get("error"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
