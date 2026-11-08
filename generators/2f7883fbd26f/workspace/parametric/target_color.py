#!/usr/bin/env python3
"""Task-local target-color parameter prototype for ARC family 2f7883fbd26f.

The selected production generator supplies lawful inputs.  Every retained
label, rival prediction, and canonical comparison is produced by executing an
exact emitted Racket rule through the packet's public RacketBridge.  This file
is prototype evidence only: it does not alter canonical authority or expose a
production parametric API.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import platform
import sys
from contextlib import nullcontext
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "2f7883fbd26f"
DEFAULT_TARGET_COLOR = 1
TARGET_COLORS = (1, 2)
PAIR_COUNTS = ((2, 4), (5, 1), (3, 2), (4, 3))
PARAMETER_SPEC = {
    "target_color": {
        "allowed": list(TARGET_COLORS),
        "default": DEFAULT_TARGET_COLOR,
        "scope": "one setting for the entire episode",
        "meaning": "color whose sliding 2x2 monochrome windows are counted",
        "input_constraints_depend_on_setting": False,
        "output_encoding": "a width-5 unary bar of leading color-1 cells",
    }
}
LIMITATIONS = [
    "Task-local prototype; no production parametric API or approval is added.",
    "Only target colors 1 and 2 are assessed; no second parameter is proposed.",
    "Inputs remain inside the selected generator's exact block/noise grammar.",
    "Finite setting enumeration distinguishes the declared settings, not every conceivable rule.",
    "Retained execution covers both settings at one seed plus all canonical pairs, not every seed.",
    "This evidence makes no model-trajectory or training-admission claim.",
]


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _validate_target_color(target_color) -> int:
    if type(target_color) is not int or target_color not in TARGET_COLORS:
        raise ValueError(
            f"target_color must be a literal integer in {list(TARGET_COLORS)}, got {target_color!r}"
        )
    return target_color


def _validate_episode_bounds(seed, n_train, n_test) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal integer")
    for name, value, upper in (("n_train", n_train, 4), ("n_test", n_test, 2)):
        if type(value) is not int or not 1 <= value <= upper:
            raise ValueError(f"{name} must be a literal integer in 1..{upper}")
    if n_train + n_test > len(PAIR_COUNTS):
        raise ValueError(
            f"n_train + n_test must be at most {len(PAIR_COUNTS)} for the fixed witness plan"
        )


def emit_racket(target_color=DEFAULT_TARGET_COLOR) -> str:
    """Emit the complete exact rule for one episode-wide target color."""
    target_color = _validate_target_color(target_color)
    return f"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((n (for*/sum ((r (range 0 (- h 1))) (c (range 0 (- w 1))))
                               (if (and
                                     (= {target_color} (at g r c))
                                     (= {target_color} (at g (+ r 1) c))
                                     (= {target_color} (at g r (+ c 1)))
                                     (= {target_color} (at g (+ r 1) (+ c 1))))
                                   1
                                   0))))
             (encode-bar n 5 1)))))"""


def execute_racket(program: str, inputs, *, bridge=None) -> list:
    """Execute exact rule text through the bundled public Racket bridge."""
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be nonempty Racket source text")
    body = strip_rule_wrapper(program) if program.lstrip().startswith("(rule!") else program
    with (nullcontext(bridge) if bridge is not None else RacketBridge()) as runtime:
        runtime.eval_text(f"(define parametric-target-color-rule {body})")
        outputs = []
        for grid in inputs:
            runtime.define_grid("parametric-target-color-input", normalize_grid(grid))
            output = runtime.eval_text(
                "(parametric-target-color-rule parametric-target-color-input)"
            )
            outputs.append(normalize_grid(output))
        return outputs


def _selected_root(root=None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def _draw_inputs(generator, seed: int, count: int) -> list:
    inputs = []
    for sample_index, (color_one_windows, color_two_windows) in enumerate(PAIR_COUNTS[:count]):
        grid = generator.generate(
            seed,
            sample_index,
            difficulty="medium",
            grid_h=9,
            grid_w=9,
            n_target_blocks=color_one_windows,
            n_decoy_blocks=color_two_windows,
            n_singleton_ones=2,
            n_singleton_twos=1,
        )
        errors = generator.self_check(grid)
        if errors:
            raise ValueError(f"selected generator produced unlawful input {sample_index}: {errors}")
        inputs.append(grid)
    return inputs


def make_episode(
    seed,
    *,
    target_color=DEFAULT_TARGET_COLOR,
    n_train=3,
    n_test=1,
    bridge=None,
    root=None,
) -> dict:
    """Choose one rule setting, draw lawful shared inputs, and execute all labels."""
    _validate_episode_bounds(seed, n_train, n_test)
    selected_color = (
        TARGET_COLORS[seed % len(TARGET_COLORS)]
        if target_color is None
        else _validate_target_color(target_color)
    )
    selected_root = _selected_root(root)
    generator, _, generator_sha256 = load_selected_generator(TASK_ID, root=selected_root)
    inputs = _draw_inputs(generator, seed, n_train + n_test)
    program = emit_racket(selected_color)
    outputs = execute_racket(program, inputs, bridge=bridge)
    pairs = [
        {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
        for grid, output in zip(inputs, outputs)
    ]
    return {
        "schema": "arc-target-color-parametric-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"target_color": selected_color},
        "parameter_selection": "seed_modulo_two_once" if target_color is None else "explicit_once",
        "program": program,
        "program_sha256": _sha256(program.encode("utf-8")),
        "generator_sha256": generator_sha256,
        "generator_version": generator.VERSION,
        "input_draws": {
            "difficulty": "medium",
            "sample_indices": list(range(n_train + n_test)),
            "window_count_plan": [
                {"color_1": one, "color_2": two}
                for one, two in PAIR_COUNTS[: n_train + n_test]
            ],
        },
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def analyze_settings(demos, query_inputs, *, bridge=None, root=None) -> dict:
    """Enumerate both declared settings using demonstrations, never query labels."""
    selected_root = _selected_root(root)
    generator, _, _ = load_selected_generator(TASK_ID, root=selected_root)
    demo_inputs = []
    demo_outputs = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            raise ValueError(f"demo {index} must contain input and output")
        demo_inputs.append(normalize_grid(pair["input"]))
        demo_outputs.append(normalize_grid(pair["output"]))
    query_inputs = [normalize_grid(grid) for grid in query_inputs]
    for index, grid in enumerate(demo_inputs + query_inputs):
        errors = generator.self_check(grid)
        if errors:
            raise ValueError(f"input {index} is outside the selected grammar: {errors}")

    settings = {}
    compatible = []
    with (nullcontext(bridge) if bridge is not None else RacketBridge()) as runtime:
        for color in TARGET_COLORS:
            program = emit_racket(color)
            predictions = execute_racket(program, demo_inputs + query_inputs, bridge=runtime)
            demo_predictions = predictions[: len(demo_inputs)]
            matches = [
                predicted == expected
                for predicted, expected in zip(demo_predictions, demo_outputs)
            ]
            settings[str(color)] = {
                "program": program,
                "program_sha256": _sha256(program.encode("utf-8")),
                "demo_predictions": demo_predictions,
                "demo_matches": matches,
                "query_predictions": predictions[len(demo_inputs) :],
            }
            if all(matches):
                compatible.append(color)

    ambiguities = []
    for first, second in itertools.combinations(compatible, 2):
        disagreements = [
            index
            for index, (left, right) in enumerate(
                zip(
                    settings[str(first)]["query_predictions"],
                    settings[str(second)]["query_predictions"],
                )
            )
            if left != right
        ]
        if disagreements:
            ambiguities.append(
                {"settings": [first, second], "query_indices": disagreements}
            )
    return {
        "declared_settings": list(TARGET_COLORS),
        "compatible_settings": compatible,
        "identified": len(compatible) == 1,
        "outcome": (
            "identified"
            if len(compatible) == 1
            else "ambiguous"
            if compatible
            else "inconsistent"
        ),
        "query_relevant_ambiguities": ambiguities,
        "settings": settings,
    }


def public_challenge(episode) -> dict:
    """Return only demonstrations and query inputs, deeply detached from private data."""
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _canonical_authority(root: Path) -> dict:
    with canonical_path(root).open(encoding="utf-8") as handle:
        rows = [
            row
            for line in handle
            if line.strip()
            if (row := json.loads(line)).get("task_id") == TASK_ID
        ]
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    row = rows[0]
    program = row["program_solution"]
    return {
        "row_sha256": _sha256(
            json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ),
        "program": program,
        "program_sha256": _sha256(program.encode("utf-8")),
    }


def _source_bindings(root: Path) -> dict:
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    task = root / "generators" / TASK_ID
    files = [
        task / "workspace" / "parametric" / "target_color.py",
        task / "workspace" / "parametric" / "README.md",
        task / "tests" / "test_parametric_target_color.py",
    ]
    missing = [path for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing prototype source binding(s): {missing}")
    return {
        "selected_generator": {
            "path": source.relative_to(root).as_posix(),
            "sha256": digest,
            "version": generator.VERSION,
        },
        "prototype_files": [
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256(path.read_bytes()),
            }
            for path in files
        ],
        "canonical_authority": _canonical_authority(root),
    }


def write_evidence(out_dir, *, seed=9173, root=None) -> dict:
    """Execute both complete episodes and retain private/public verification files."""
    _validate_episode_bounds(seed, 3, 1)
    selected_root = _selected_root(root)
    out_dir = Path(out_dir).resolve()
    if out_dir.exists():
        raise FileExistsError(f"choose a new evidence directory: {out_dir}")
    sources = _source_bindings(selected_root)

    with RacketBridge() as bridge:
        episodes = [
            make_episode(
                seed,
                target_color=color,
                bridge=bridge,
                root=selected_root,
            )
            for color in TARGET_COLORS
        ]
        analyses = [
            analyze_settings(
                episode["train"],
                [pair["input"] for pair in episode["test"]],
                bridge=bridge,
                root=selected_root,
            )
            for episode in episodes
        ]
        labels_reexecuted = all(
            report["settings"][str(episode["parameters"]["target_color"])][
                "demo_predictions"
            ]
            + report["settings"][str(episode["parameters"]["target_color"])][
                "query_predictions"
            ]
            == [pair["output"] for pair in episode["train"] + episode["test"]]
            for episode, report in zip(episodes, analyses)
        )
        all_identified = all(
            report["compatible_settings"]
            == [episode["parameters"]["target_color"]]
            and not report["query_relevant_ambiguities"]
            for episode, report in zip(episodes, analyses)
        )

        canonical_records = canonical_pairs(TASK_ID, root=selected_root)
        canonical_inputs = [pair["input"] for pair in canonical_records]
        canonical_program = sources["canonical_authority"]["program"]
        authoritative_outputs = execute_racket(
            canonical_program, canonical_inputs, bridge=bridge
        )
        default_outputs = execute_racket(emit_racket(), canonical_inputs, bridge=bridge)
        parity_records = [
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "canonical_label_match": authoritative == pair["output"],
                "prototype_match": default == authoritative,
            }
            for pair, authoritative, default in zip(
                canonical_records, authoritative_outputs, default_outputs
            )
        ]
        parity = all(
            row["canonical_label_match"] and row["prototype_match"]
            for row in parity_records
        )

        witness_input = episodes[0]["train"][0]["input"]
        witness_outputs = {
            str(color): execute_racket(
                emit_racket(color), [witness_input], bridge=bridge
            )[0]
            for color in TARGET_COLORS
        }
        witness_differs = witness_outputs["1"] != witness_outputs["2"]
        generator, _, _ = load_selected_generator(TASK_ID, root=selected_root)
        witness_errors = generator.self_check(witness_input)
        runtime_identity = {
            "engine": "arc_repl.racket_bridge.RacketBridge",
            "python_version": platform.python_version(),
            "racket_binary": str(bridge.racket_binary),
            "normalizer": "public normalize_grid and strip_rule_wrapper",
            "evaluation": "(parametric-target-color-rule parametric-target-color-input)",
        }

    public = [public_challenge(episode) for episode in episodes]
    public_safe = all(
        set(challenge) == {"train", "test"}
        and all(set(pair) == {"input", "output"} for pair in challenge["train"])
        and all(set(pair) == {"input"} for pair in challenge["test"])
        for challenge in public
    )
    passed = all(
        (
            labels_reexecuted,
            all_identified,
            parity,
            witness_differs,
            not witness_errors,
            public_safe,
        )
    )
    if not passed:
        raise RuntimeError("prototype evidence verification failed; refusing a passed bundle")
    if _source_bindings(selected_root) != sources:
        raise RuntimeError("sources changed during evidence execution; rerun on stable bytes")

    private = {
        "schema": "arc-target-color-parametric-prototype-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": PARAMETER_SPEC,
        "sources": sources,
        "runtime": runtime_identity,
        "episodes": episodes,
        "setting_identifiability": analyses,
        "limitations": LIMITATIONS,
    }
    private_bytes = _json_bytes(private)
    public_bytes = _json_bytes(public)
    verification = {
        "schema": "arc-target-color-parametric-verification-v1",
        "status": "passed",
        "scope": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "invocation": {
            "python_executable": sys.executable,
            "argv": list(sys.argv),
            "cwd": str(Path.cwd()),
            "replay_from_packet_root": (
                "python3 review.py run python3 "
                f"generators/{TASK_ID}/workspace/parametric/target_color.py "
                f"--seed {seed} --out ../checks/parametric/target-color"
            ),
        },
        "artifact_sha256": {
            "episodes.private.json": _sha256(private_bytes),
            "challenges.public.json": _sha256(public_bytes),
        },
        "all_episode_labels_reexecuted": labels_reexecuted,
        "episode_pair_count": sum(
            len(episode["train"]) + len(episode["test"]) for episode in episodes
        ),
        "all_settings_identified": all_identified,
        "compatible_settings": [
            report["compatible_settings"] for report in analyses
        ],
        "public_schema_safe": public_safe,
        "canonical_default_parity": {
            "all_match": parity,
            "pair_count": len(parity_records),
        },
        "canonical_parity_records": parity_records,
        "distinguishing_witness": {
            "input": witness_input,
            "lawful_input_errors": witness_errors,
            "outputs": witness_outputs,
            "outputs_differ": witness_differs,
        },
        "limitations": LIMITATIONS,
    }

    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / "episodes.private.json").write_bytes(private_bytes)
    (out_dir / "challenges.public.json").write_bytes(public_bytes)
    (out_dir / "verification.json").write_bytes(_json_bytes(verification))
    return verification


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=9173)
    parser.add_argument(
        "--out", type=Path, required=True, help="new directory for three evidence JSON files"
    )
    args = parser.parse_args(argv)
    result = write_evidence(args.out, seed=args.seed)
    print(
        json.dumps(
            {
                "status": result["status"],
                "scope": result["scope"],
                "seed": args.seed,
                "episode_pair_count": result["episode_pair_count"],
                "compatible_settings": result["compatible_settings"],
                "canonical_pairs": result["canonical_default_parity"]["pair_count"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
