#!/usr/bin/env python3
"""Proposed episode-level compass-slot rotation for task 5a85abd1e231.

The selected production generator and canonical authority remain fixed.  This
separate authoring prototype keeps the canonical reasoning chain—find each 3x3
glyph, decode its direction, and copy the whole tile—but rotates the decoded
*destination slot* by a hidden number of clockwise quarter turns chosen once
per episode.  Every retained label is executed by the exact materialized Racket
program through the bundled bridge; the Python transform is only a parity check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import types
from pathlib import Path
from typing import Any, Sequence

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.base import stable_rng
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "5a85abd1e231"
PROTOTYPE_VERSION = "compass-slot-rotation-v1"
ROTATIONS = (0, 1, 2, 3)
CANONICAL_DEFAULT = 0
N_TRAIN = 3
N_TEST = 1
# First deterministic seeds covering 270, 0, 90, and 180 degrees respectively.
DEFAULT_EVIDENCE_SEEDS = (0, 1, 3, 14)

PARAMETER_SPEC = {
    "slot_rotation_quarters": {
        "allowed": list(ROTATIONS),
        "canonical_default": CANONICAL_DEFAULT,
        "chosen_once_per_episode": True,
        "meaning": {
            0: "place each decoded glyph in its canonical compass slot",
            1: "place each decoded glyph one compass quarter-turn clockwise",
            2: "place each decoded glyph in the opposite compass slot",
            3: "place each decoded glyph one compass quarter-turn counterclockwise",
        },
        "input_constraints": [
            "the selected canonical nine-tile grammar must pass self_check",
            "all eight directional glyphs occur exactly once and the ninth tile is blank",
            "all four parameter settings must produce distinct outputs on every retained pair",
            "the same selected setting labels every demonstration and query in an episode",
        ],
    }
}

_CANONICAL_DESTINATION = """                     (let ((or (* 3 (target-row cells)))
                           (oc (* 3 (target-col cells))))"""
_ROTATED_DESTINATIONS = {
    1: """                     (let* ((target-r (target-row cells))
                            (target-c (target-col cells))
                            (rot-r target-c)
                            (rot-c (- 2 target-r))
                            (or (* 3 rot-r))
                            (oc (* 3 rot-c)))""",
    2: """                     (let* ((target-r (target-row cells))
                            (target-c (target-col cells))
                            (rot-r (- 2 target-r))
                            (rot-c (- 2 target-c))
                            (or (* 3 rot-r))
                            (oc (* 3 rot-c)))""",
    3: """                     (let* ((target-r (target-row cells))
                            (target-c (target-col cells))
                            (rot-r (- 2 target-c))
                            (rot-c target-r)
                            (or (* 3 rot-r))
                            (oc (* 3 rot-c)))""",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _encoded(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _canonical_row(root: Path) -> dict[str, Any]:
    rows = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    if not isinstance(rows[0].get("program_solution"), str):
        raise ValueError("canonical row has no Racket program_solution")
    return rows[0]


def _replace_once(source: str, old: str, new: str, *, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"canonical rule drift at {label}: expected one fragment, found {count}")
    return source.replace(old, new, 1)


def program_for(
    slot_rotation_quarters: int = CANONICAL_DEFAULT,
    *,
    root: Path | str | None = None,
) -> str:
    """Return exact Racket for one bounded compass-slot rotation setting."""
    if type(slot_rotation_quarters) is not int or slot_rotation_quarters not in ROTATIONS:
        raise ValueError(f"slot_rotation_quarters must be one of {ROTATIONS}")
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    canonical = _canonical_row(resolved)["program_solution"]
    if slot_rotation_quarters == CANONICAL_DEFAULT:
        return canonical
    return _replace_once(
        canonical,
        _CANONICAL_DESTINATION,
        _ROTATED_DESTINATIONS[slot_rotation_quarters],
        label="glyph destination mapping",
    )


def choose_parameters(seed: int) -> dict[str, int]:
    """Choose one hidden setting deterministically for the entire episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|slot_rotation_quarters", PROTOTYPE_VERSION)
    return {"slot_rotation_quarters": ROTATIONS[rng.randrange(len(ROTATIONS))]}


def _wrapped_callable(program: str, root: Path) -> str:
    """Wrap a rule while supplying the legacy tools namespace locally."""
    names = ("scripts", "scripts.comment_solutions")
    previous = {name: sys.modules.get(name) for name in names}
    package = types.ModuleType("scripts")
    package.__path__ = [str(root / "shared/tools")]
    sys.modules["scripts"] = package
    sys.modules.pop("scripts.comment_solutions", None)
    try:
        return wrap_rule(program)
    finally:
        for name in names:
            if previous[name] is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous[name]


def _execute_programs(
    programs: dict[int, str],
    grids: Sequence[list[list[int]]],
    *,
    root: Path,
) -> dict[int, list[list[list[int]]]]:
    """Execute each materialized Racket program over every supplied input."""
    bridge = RacketBridge()
    try:
        function_names: dict[int, str] = {}
        for setting, program in programs.items():
            name = f"__slot_rotation_{setting}"
            bridge.eval_text(f"(define {name} {_wrapped_callable(program, root)})")
            function_names[setting] = name
        outputs = {setting: [] for setting in programs}
        for pair_index, grid in enumerate(grids):
            grid_name = f"g_{pair_index}"
            bridge.define_grid(grid_name, grid)
            for setting, function_name in function_names.items():
                result = bridge.eval_text(f"({function_name} {grid_name})")
                if not isinstance(result, list) or not result or any(
                    not isinstance(row, list) for row in result
                ):
                    raise ValueError(f"Racket setting {setting} did not return a nonempty grid")
                outputs[setting].append(result)
        return outputs
    finally:
        bridge.shutdown()


def _rotate_slot(row: int, col: int, turns: int) -> tuple[int, int]:
    turns %= 4
    if turns == 0:
        return row, col
    if turns == 1:
        return col, 2 - row
    if turns == 2:
        return 2 - row, 2 - col
    return 2 - col, row


def _rotate_macro_blocks(canonical_output: list[list[int]], turns: int) -> list[list[int]]:
    """Independent parity mirror: rotate 3x3 destination blocks, not pixels."""
    if len(canonical_output) != 9 or any(len(row) != 9 for row in canonical_output):
        raise ValueError("canonical output must be 9x9")
    output = [[5 for _ in range(9)] for _ in range(9)]
    for block_row in range(3):
        for block_col in range(3):
            target_row, target_col = _rotate_slot(block_row, block_col, turns)
            for dr in range(3):
                for dc in range(3):
                    output[3 * target_row + dr][3 * target_col + dc] = canonical_output[
                        3 * block_row + dr
                    ][3 * block_col + dc]
    return output


def verify_canonical_default(*, root: Path | str | None = None) -> list[dict[str, Any]]:
    """Execute the default Racket program against every labeled canonical pair."""
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    row = _canonical_row(resolved)
    identities: list[tuple[str, int, dict[str, Any]]] = []
    for split in ("train", "test"):
        for index, pair in enumerate(row.get(split, [])):
            identities.append((split, index, pair))
    outputs = _execute_programs(
        {CANONICAL_DEFAULT: program_for(CANONICAL_DEFAULT, root=resolved)},
        [pair["input"] for _, _, pair in identities],
        root=resolved,
    )[CANONICAL_DEFAULT]
    return [
        {
            "split": split,
            "pair_index": index,
            "passed": actual == pair["output"],
            "actual_sha256": _sha256_text(_encoded(actual)),
            "expected_sha256": _sha256_text(_encoded(pair["output"])),
        }
        for (split, index, pair), actual in zip(identities, outputs, strict=True)
    ]


def _public_episode(
    grids: Sequence[list[list[int]]], selected_outputs: Sequence[list[list[int]]]
) -> dict[str, Any]:
    return {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(
                grids[:N_TRAIN], selected_outputs[:N_TRAIN], strict=True
            )
        ],
        # Hidden setting, Racket source, seed, and query answer are omitted.
        "test": [{"input": grid} for grid in grids[N_TRAIN:]],
    }


def materialize_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Generate and Racket-label one complete parameter-consistent episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=resolved)
    setting = choose_parameters(seed)["slot_rotation_quarters"]
    grids = [
        generator.generate(seed, pair_index, difficulty=difficulty)
        for pair_index in range(N_TRAIN + N_TEST)
    ]
    validation = [generator.self_check(grid) for grid in grids]
    if any(validation):
        raise AssertionError(f"selected generator returned unlawful prototype input: {validation}")

    programs = {turns: program_for(turns, root=resolved) for turns in ROTATIONS}
    outputs = _execute_programs(programs, grids, root=resolved)
    for turns in ROTATIONS:
        mirrors = [
            _rotate_macro_blocks(generator.rule_mirror(grid), turns) for grid in grids
        ]
        if outputs[turns] != mirrors:
            raise AssertionError(
                f"Racket output disagrees with independent block-rotation mirror for setting {turns}"
            )

    pair_distinctness = []
    for pair_index in range(len(grids)):
        signatures = {
            _encoded(outputs[turns][pair_index]) for turns in ROTATIONS
        }
        pair_distinctness.append(len(signatures) == len(ROTATIONS))
    if not all(pair_distinctness):
        raise AssertionError("retained episode does not distinguish all slot rotations")

    rivals = {
        rival: {
            "demo_mismatches": [
                pair_index
                for pair_index in range(N_TRAIN)
                if outputs[rival][pair_index] != outputs[setting][pair_index]
            ],
            "query_differs": outputs[rival][N_TRAIN] != outputs[setting][N_TRAIN],
        }
        for rival in ROTATIONS
        if rival != setting
    }
    expected_demo_mismatches = list(range(N_TRAIN))
    if not all(
        record["demo_mismatches"] == expected_demo_mismatches
        and record["query_differs"]
        for record in rivals.values()
    ):
        raise AssertionError("demonstrations failed to refute every alternative parameter setting")

    selected_outputs = outputs[setting]
    public = _public_episode(grids, selected_outputs)
    private_pairs = [
        {
            "sample_index": pair_index,
            "input": grid,
            "selected_output": selected_outputs[pair_index],
            "outputs": {turns: outputs[turns][pair_index] for turns in ROTATIONS},
            "all_settings_distinct": pair_distinctness[pair_index],
        }
        for pair_index, grid in enumerate(grids)
    ]
    prototype_path = Path(__file__).resolve()
    ledger_path = canonical_path(resolved)
    return {
        "schema": "arc-parametric-compass-slot-rotation-evidence-v1",
        "task_id": TASK_ID,
        "prototype_status": "proposed",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "parameter": {
            "slot_rotation_quarters": setting,
            "allowed": list(ROTATIONS),
            "canonical_default": CANONICAL_DEFAULT,
            "chosen_once_per_episode": True,
        },
        "parameter_spec": PARAMETER_SPEC,
        "racket_verified": True,
        "selected_generator_self_check_passed": True,
        "rivals": rivals,
        "programs": {
            turns: {"text": text, "sha256": _sha256_text(text)}
            for turns, text in programs.items()
        },
        "sources": {
            "prototype_path": str(prototype_path),
            "prototype_sha256": _sha256_file(prototype_path),
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha,
            "canonical_path": str(ledger_path),
            "canonical_sha256": _sha256_file(ledger_path),
        },
        "public": public,
        "public_sha256": _sha256_text(_encoded(public)),
        "private": {
            "train": private_pairs[:N_TRAIN],
            "test": private_pairs[N_TRAIN:],
        },
        "limitations": [
            "prototype only; production remains bound to the canonical zero-rotation rule",
            "bounded evidence for retained seeds and named parameter rivals, not all seeds or hypotheses",
            "the glyph tile is copied unchanged; only its decoded destination slot rotates",
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _public_filename(seed: int, public: dict[str, Any]) -> str:
    fingerprint = _sha256_text(_encoded({"seed": seed, "challenge": public}))[:20]
    return f"episode-{fingerprint}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_EVIDENCE_SEEDS))
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="easy")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    root = find_root(__file__)
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / "public").mkdir()
    (out_dir / "private").mkdir()
    (out_dir / "private" / "rules").mkdir()

    programs = {turns: program_for(turns, root=root) for turns in ROTATIONS}
    for turns, text in programs.items():
        (out_dir / "private" / "rules" / f"slot-rotation-{turns}.rkt").write_text(
            text + "\n", encoding="utf-8"
        )

    canonical_parity = verify_canonical_default(root=root)
    _write_json(out_dir / "private" / "canonical-parity.json", canonical_parity)
    if not canonical_parity or not all(record["passed"] for record in canonical_parity):
        raise AssertionError("canonical default Racket program failed labeled-pair parity")

    episodes = []
    observed = set()
    first_private_pair = None
    for seed in args.seeds:
        evidence = materialize_episode(seed, difficulty=args.difficulty, root=root)
        setting = evidence["parameter"]["slot_rotation_quarters"]
        observed.add(setting)
        public_name = _public_filename(seed, evidence["public"])
        public_path = out_dir / "public" / public_name
        private_path = out_dir / "private" / public_name
        _write_json(public_path, evidence["public"])
        private_document = dict(evidence)
        private_document.pop("public")
        _write_json(private_path, private_document)
        if first_private_pair is None:
            first_private_pair = evidence["private"]["train"][0]
        episodes.append(
            {
                "seed": seed,
                "slot_rotation_quarters": setting,
                "public_path": str(public_path.relative_to(out_dir)),
                "public_sha256": _sha256_file(public_path),
                "private_path": str(private_path.relative_to(out_dir)),
                "private_sha256": _sha256_file(private_path),
                "rivals": evidence["rivals"],
            }
        )

    if observed != set(ROTATIONS):
        raise RuntimeError(
            f"retained seeds must cover all settings; observed {sorted(observed)}"
        )
    if first_private_pair is None:
        raise RuntimeError("no episodes were materialized")
    differing_witness = {
        "input": first_private_pair["input"],
        "outputs": first_private_pair["outputs"],
        "all_settings_distinct": first_private_pair["all_settings_distinct"],
        "output_sha256": {
            setting: _sha256_text(_encoded(output))
            for setting, output in first_private_pair["outputs"].items()
        },
    }
    _write_json(out_dir / "private" / "differing-witness.json", differing_witness)

    source_paths = [
        Path(__file__).resolve(),
        Path(__file__).resolve().parents[2] / "generator.py",
        Path(__file__).resolve().parents[2] / "tests" / "test_parametric_slot_rotation.py",
        Path(__file__).resolve().parent / "README.md",
    ]
    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "prototype_status": "proposed",
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_spec": PARAMETER_SPEC,
        "command": shlex.join([sys.executable, *sys.argv]),
        "payload_cwd": str(Path.cwd()),
        "runtime": racket_runtime_status(),
        "canonical_pairs": {
            "checked": len(canonical_parity),
            "passed": sum(record["passed"] for record in canonical_parity),
        },
        "programs": {
            turns: {
                "path": f"private/rules/slot-rotation-{turns}.rkt",
                "sha256": _sha256_text(text),
            }
            for turns, text in programs.items()
        },
        "episodes": episodes,
        "differing_witness": "private/differing-witness.json",
        "source_sha256": {
            str(path.relative_to(root)): _sha256_file(path)
            for path in source_paths
            if path.exists()
        },
        "limitations": [
            "proposed task-local authoring prototype; it does not alter production authority",
            "finite Racket execution evidence covers four retained episodes and all labeled canonical pairs",
            "no claim is made that these are the only learnable nearby rule variants",
        ],
    }
    summary["artifact_sha256"] = {
        str(path.relative_to(out_dir)): _sha256_file(path)
        for path in sorted(out_dir.rglob("*"))
        if path.is_file()
    }
    _write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
