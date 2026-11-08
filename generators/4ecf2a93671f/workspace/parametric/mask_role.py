#!/usr/bin/env python3
"""Task-local mask-role prototype, never a production per-puzzle generator.

The selected generator supplies lawful inputs only. Every label and every
finite-setting rival prediction is obtained by executing emitted Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from contextlib import nullcontext
from pathlib import Path
import platform
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "4ecf2a93671f"
DEFAULT_MASK_ROLE = "background"
MASK_ROLES = ("background", "foreground")
PARAMETER_SPEC = {
    "mask_role": {
        "allowed": list(MASK_ROLES),
        "default": DEFAULT_MASK_ROLE,
        "scope": "one setting for the entire episode",
        "meaning": "select the same input-value predicate at block and subcell coordinates",
        "input_constraints_depend_on_setting": False,
    }
}
LIMITATIONS = [
    "Task-local prototype; no production parametric API or approval is added.",
    "Only background and foreground are supported; no second parameter is proposed.",
    "Input grammar remains the selected generator's square, two-color grammar with background 0.",
    "Finite setting checks identify the declared parameter, not every possible alternative rule.",
    "Retained execution covers one seed with both settings and the canonical pairs, not all seeds.",
    "This evidence makes no model-trajectory training-admission claim.",
]


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _validate_role(mask_role) -> str:
    if not isinstance(mask_role, str) or mask_role not in MASK_ROLES:
        raise ValueError(f"mask_role must be one of {list(MASK_ROLES)}, got {mask_role!r}")
    return mask_role


def _validate_episode_bounds(seed, n_train, n_test) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    for name, value, upper in (("n_train", n_train, 8), ("n_test", n_test, 4)):
        if type(value) is not int or not 1 <= value <= upper:
            raise ValueError(f"{name} must be a literal integer in 1..{upper}")


def emit_racket(mask_role=DEFAULT_MASK_ROLE) -> str:
    """Materialize a complete rule; its sole variation is one shared predicate."""
    mask_role = _validate_role(mask_role)
    predicate = "(zero? value)" if mask_role == "background" else "(!= value 0)"
    return f"""(lambda (g)
 ;; The input is square and has background 0 and one nonzero PAINT color.
 ;; The MASK is the {mask_role} support of that input.
 ;; At both scales, require membership in this same MASK, then paint.
 (let ()
   (define side (rows g))
   (define paint (mode g 0))
   (define (selected? value) {predicate})
   (build-grid (* side side) (* side side) (r c)
     (if (and (selected? (at g (quotient r side) (quotient c side)))
              (selected? (at g (modulo r side) (modulo c side))))
         paint
         0))))"""


def execute_racket(program: str, inputs, *, bridge=None) -> list:
    """Execute the exact emitted lambda, or the known canonical lambda wrapper.

    These sources bind their own dimensions and use no shorthand conversion.
    This narrow prototype intentionally does not implement a general normalizer.
    """
    body = strip_rule_wrapper(program) if program.lstrip().startswith("(rule!") else program
    with (nullcontext(bridge) if bridge is not None else RacketBridge()) as runtime:
        runtime.eval_text(f"(define parametric-rule {body})")
        outputs = []
        for grid in inputs:
            runtime.define_grid("parametric-input", normalize_grid(grid))
            outputs.append(normalize_grid(runtime.eval_text("(parametric-rule parametric-input)")))
        return outputs


def make_episode(seed, *, mask_role=DEFAULT_MASK_ROLE, n_train=3, n_test=1,
                 bridge=None, root=None) -> dict:
    """Choose the rule once, draw inputs, and execute that rule for every pair.

    The default is canonical background behavior. Passing ``mask_role=None``
    uses a deterministic two-setting schedule: ``MASK_ROLES[seed % 2]``. This
    choice is made before any pair draw and does not depend on pair count.
    """
    _validate_episode_bounds(seed, n_train, n_test)
    selected_role = MASK_ROLES[seed % len(MASK_ROLES)] if mask_role is None else _validate_role(mask_role)
    selected_root = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, generator_sha256 = load_selected_generator(TASK_ID, root=selected_root)
    program = emit_racket(selected_role)
    inputs = [generator.generate(seed, index, difficulty="medium")
              for index in range(n_train + n_test)]
    for index, grid in enumerate(inputs):
        errors = generator.self_check(grid)
        if errors:
            raise ValueError(f"selected generator produced unlawful input {index}: {errors}")
    outputs = execute_racket(program, inputs, bridge=bridge)
    pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, outputs)]
    return {
        "seed": seed,
        "parameters": {"mask_role": selected_role},
        "parameter_selection": "seed_modulo_two_once" if mask_role is None else "explicit_once",
        "program": program,
        "program_sha256": _sha256(program.encode("utf-8")),
        "executed_lambda": program,
        "executed_lambda_sha256": _sha256(program.encode("utf-8")),
        "generator_sha256": generator_sha256,
        "generator_version": generator.VERSION,
        "input_draws": {"difficulty": "medium", "sample_indices": list(range(n_train + n_test))},
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def analyze_settings(demos, query_inputs, *, bridge=None, root=None) -> dict:
    """Enumerate declared settings without consulting hidden query answers.

    Empty demos honestly leave both settings compatible. Contradictory demos
    honestly leave no setting compatible. Neither result is called identified.
    """
    selected_root = find_root(__file__) if root is None else Path(root).resolve()
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
            raise ValueError(f"input {index} is outside the prototype grammar: {errors}")

    settings = {}
    compatible = []
    with (nullcontext(bridge) if bridge is not None else RacketBridge()) as runtime:
        for role in MASK_ROLES:
            program = emit_racket(role)
            predictions = execute_racket(program, demo_inputs + query_inputs, bridge=runtime)
            demo_predictions = predictions[:len(demo_inputs)]
            matches = [predicted == expected for predicted, expected in zip(demo_predictions, demo_outputs)]
            settings[role] = {
                "program": program,
                "program_sha256": _sha256(program.encode("utf-8")),
                "demo_predictions": demo_predictions,
                "demo_matches": matches,
                "query_predictions": predictions[len(demo_inputs):],
            }
            if all(matches):
                compatible.append(role)
    ambiguities = []
    for first, second in itertools.combinations(compatible, 2):
        disagreements = [index for index, (left, right) in enumerate(zip(
            settings[first]["query_predictions"], settings[second]["query_predictions"])) if left != right]
        if disagreements:
            ambiguities.append({"settings": [first, second], "query_indices": disagreements})
    return {
        "declared_settings": list(MASK_ROLES),
        "compatible_settings": compatible,
        "identified": len(compatible) == 1,
        "outcome": "identified" if len(compatible) == 1 else "ambiguous" if compatible else "inconsistent",
        "query_relevant_ambiguities": ambiguities,
        "settings": settings,
    }


def public_challenge(episode) -> dict:
    """Expose demonstration pairs and query inputs, with no hidden metadata."""
    return {
        "train": [{"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
                  for pair in episode["train"]],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _canonical_authority(root) -> dict:
    with canonical_path(root).open(encoding="utf-8") as handle:
        rows = [row for line in handle if line.strip()
                if (row := json.loads(line)).get("task_id") == TASK_ID]
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    row = rows[0]
    program = row["program_solution"]
    return {
        "row_sha256": _sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        "program": program,
        "program_sha256": _sha256(program.encode("utf-8")),
    }


def _source_bindings(root) -> dict:
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    task = root / "generators" / TASK_ID
    prototype_files = [task / "workspace" / "parametric" / "mask_role.py",
                       task / "workspace" / "parametric" / "README.md",
                       task / "tests" / "test_parametric_mask_role.py"]
    return {
        "selected_generator": {"path": source.relative_to(root).as_posix(), "sha256": digest,
                               "version": generator.VERSION},
        "prototype_files": [{"path": path.relative_to(root).as_posix(), "sha256": _sha256(path.read_bytes())}
                            for path in prototype_files],
        "canonical_authority": _canonical_authority(root),
    }


def write_evidence(out_dir, *, seed=46371, root=None) -> dict:
    """Retain two complete private episodes and their direct execution checks."""
    _validate_episode_bounds(seed, 3, 1)
    selected_root = find_root(__file__) if root is None else Path(root).resolve()
    out_dir = Path(out_dir).resolve()
    if out_dir.exists():
        raise FileExistsError(f"choose a new evidence directory: {out_dir}")
    sources = _source_bindings(selected_root)
    canonical = sources["canonical_authority"]["program"]
    with RacketBridge() as bridge:
        episodes = [make_episode(seed, mask_role=role, bridge=bridge, root=selected_root)
                    for role in MASK_ROLES]
        analyses = [analyze_settings(episode["train"], [pair["input"] for pair in episode["test"]],
                                    bridge=bridge, root=selected_root) for episode in episodes]
        labels_reexecuted = all(
            report["settings"][episode["parameters"]["mask_role"]]["demo_predictions"]
            + report["settings"][episode["parameters"]["mask_role"]]["query_predictions"]
            == [pair["output"] for pair in episode["train"] + episode["test"]]
            for episode, report in zip(episodes, analyses))
        all_identified = all(report["compatible_settings"] == [episode["parameters"]["mask_role"]]
                             and not report["query_relevant_ambiguities"]
                             for episode, report in zip(episodes, analyses))

        canonical_records = canonical_pairs(TASK_ID, root=selected_root)
        canonical_inputs = [pair["input"] for pair in canonical_records]
        canonical_outputs = execute_racket(canonical, canonical_inputs, bridge=bridge)
        default_outputs = execute_racket(emit_racket(), canonical_inputs, bridge=bridge)
        parity_records = [{
            "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
            "input": pair["input"], "canonical_output": authoritative, "prototype_output": default,
            "canonical_label_match": authoritative == pair["output"], "prototype_match": default == authoritative,
        } for pair, authoritative, default in zip(canonical_records, canonical_outputs, default_outputs)]
        parity = all(pair["canonical_label_match"] and pair["prototype_match"] for pair in parity_records)

        generated_pairs = episodes[0]["train"] + episodes[0]["test"]
        generated_canonical = execute_racket(canonical, [pair["input"] for pair in generated_pairs], bridge=bridge)
        generated_parity = generated_canonical == [pair["output"] for pair in generated_pairs]
        witness_input = [[0, 0, 7], [7, 0, 7], [7, 7, 0]]
        generator, _, _ = load_selected_generator(TASK_ID, root=selected_root)
        witness_errors = generator.self_check(witness_input)
        witness_outputs = {role: execute_racket(emit_racket(role), [witness_input], bridge=bridge)[0]
                           for role in MASK_ROLES}
        witness_differs = witness_outputs["background"] != witness_outputs["foreground"]
        runtime_identity = {"engine": "arc_repl.racket_bridge.RacketBridge", "python_version": platform.python_version(),
                            "racket_binary": str(bridge.racket_binary),
                            "normalizer": "none for emitted self-contained lambdas; public strip_rule_wrapper for the known canonical lambda",
                            "evaluation": "(parametric-rule parametric-input)"}

    public = [public_challenge(episode) for episode in episodes]
    public_safe = all(set(challenge) == {"train", "test"}
                      and all(set(pair) == {"input", "output"} for pair in challenge["train"])
                      and all(set(pair) == {"input"} for pair in challenge["test"])
                      for challenge in public)
    passed = all((labels_reexecuted, all_identified, parity, generated_parity, witness_differs,
                  not witness_errors, public_safe))
    if not passed:
        raise RuntimeError("prototype evidence verification failed; no passed bundle will be written")
    # Bind the final source bytes and fail if the selected source changed mid-run.
    if _source_bindings(selected_root) != sources:
        raise RuntimeError("sources changed during evidence execution; rerun against stable bytes")
    private = {
        "schema": "arc-task-parametric-prototype-v1", "status": "prototype", "task_id": TASK_ID,
        "seed": seed, "parameters": PARAMETER_SPEC, "sources": sources, "runtime": runtime_identity,
        "episodes": episodes, "setting_identifiability": analyses, "limitations": LIMITATIONS,
    }
    private_bytes = _json_bytes(private)
    public_bytes = _json_bytes(public)
    verification = {
        "schema": "arc-task-parametric-verification-v1", "status": "passed", "scope": "prototype",
        "task_id": TASK_ID, "seed": seed,
        "invocation": {"python_executable": sys.executable, "argv": list(sys.argv), "cwd": str(Path.cwd()),
                       "replay_from_packet_root": f"python3 review.py run python3 generators/4ecf2a93671f/workspace/parametric/mask_role.py --seed {seed} --out ../checks/parametric"},
        "artifact_sha256": {"episodes.private.json": _sha256(private_bytes), "challenges.public.json": _sha256(public_bytes)},
        "all_episode_labels_reexecuted": labels_reexecuted,
        "episode_pair_count": sum(len(episode["train"]) + len(episode["test"]) for episode in episodes),
        "all_settings_identified": all_identified,
        "compatible_settings": [report["compatible_settings"] for report in analyses],
        "unsupported_settings": [], "public_schema_safe": public_safe,
        "canonical_default_parity": {"pair_count": len(parity_records), "all_match": parity, "pairs": parity_records,
                                     "generated_pair_count": len(generated_pairs), "generated_all_match": generated_parity,
                                     "generated_canonical_outputs": generated_canonical},
        "distinguishing_witness": {"input": witness_input, "lawful_input_errors": witness_errors,
                                   "outputs": witness_outputs, "outputs_differ": witness_differs},
        "limitations": LIMITATIONS,
    }
    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / "episodes.private.json").write_bytes(private_bytes)
    (out_dir / "challenges.public.json").write_bytes(public_bytes)
    (out_dir / "verification.json").write_bytes(_json_bytes(verification))
    return verification


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=46371)
    parser.add_argument("--out", type=Path, required=True, help="new directory for three evidence JSON files")
    args = parser.parse_args(argv)
    result = write_evidence(args.out, seed=args.seed)
    print(json.dumps({"status": result["status"], "scope": "prototype", "seed": args.seed,
                      "episode_pair_count": result["episode_pair_count"],
                      "compatible_settings": result["compatible_settings"],
                      "canonical_pairs": result["canonical_default_parity"]["pair_count"],
                      "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
