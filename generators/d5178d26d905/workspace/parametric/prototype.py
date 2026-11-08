#!/usr/bin/env python3
"""Proposed episode-level special-row mapping-order variant for d5178d26d905.

The selected production rule remains ``top_to_bottom``.  The alternative keeps
all object roles, parsing, line colors, fills, and retention masks unchanged,
but maps template special rows to reference special rows bottom-to-top.  A
single setting is chosen from the episode seed and shared by every pair.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "d5178d26d905"
PARAMETER_NAME = "special_mapping_order"
ALLOWED_MAPPING_ORDERS = ("top_to_bottom", "bottom_to_top")
DEFAULT_MAPPING_ORDER = "top_to_bottom"
PROTOTYPE_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]

# Portable task-test runtimes expose dependencies at their root.  The library
# workspace keeps the same packages under shared/runtime.
DEPENDENCY_ROOT = REPO if (REPO / "RUNTIME_MANIFEST.json").is_file() else REPO / "shared/runtime"
for import_root in (REPO, DEPENDENCY_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper  # noqa: E402
from reviewer_support import find_root, load_selected_generator  # noqa: E402


_CANONICAL_PROGRAM = r'''(rule!
 ;; A full gray(5) column splits the board: one side is a REFERENCE
 ;; panel drawn only in 0/4 (yellow marks the line columns, and its
 ;; rarer rows mark SPECIAL rows), the other a TEMPLATE panel of
 ;; colored vertical lines whose special rows show a highlight fill.
 ;; Repaint the reference: line columns take the template line colors;
 ;; each special reference row takes its matching template row's fill,
 ;; keeping a line cell colored only where the template kept it.
 (lambda (g)
   (let ()
     (define div-col
       (find-first (lambda (c) (all? (lambda (r) (= (at g r c) 5))
                                     (range 0 h)))
                   (range 0 w)))
     (define (panel cstart cend)  ;; non-gray rows of the region, cropped
       (map (lambda (r) (for/list ((cx (range cstart cend))) (at g r cx)))
            (filter (lambda (r) (any? (lambda (cx) (not (= (at g r cx) 5)))
                                      (range cstart cend)))
                    (range 0 h))))
     (define left (panel 0 div-col))
     (define right (panel (+ div-col 1) w))
     (define (ref? mat)
       (all? (lambda (row) (all? (lambda (v) (or (zero? v) (= v 4))) row))
             mat))
     (define ref (if (ref? left) left right))
     (define tmp (if (ref? left) right left))
     (define tmp-w (length (first tmp)))
     (define tmp-normal  ;; the template's most common row
       (pick-max (remove-duplicates tmp)
                 (lambda (row) (count-if (lambda (r2) (equal? r2 row))
                                         tmp))))
     (define line-cols
       (filter (lambda (cx) (not (zero? (nth tmp-normal cx))))
               (range 0 tmp-w)))
     (define line-colors (map (lambda (cx) (nth tmp-normal cx)) line-cols))
     (define tmp-specials
       (filter (lambda (i) (not (equal? (nth tmp i) tmp-normal)))
               (range 0 (length tmp))))
     (define (yellows row) (count-if (lambda (v) (= v 4)) row))
     (define ref-normal  ;; the ref row with the fewest (but >0) yellows
       (pick-min (filter (lambda (row) (> (yellows row) 0)) ref) yellows))
     (define ref-line-cols
       (filter (lambda (cx) (= (nth ref-normal cx) 4))
               (range 0 (length (first ref)))))
     (define ref-specials
       (filter (lambda (i) (and (> (yellows (nth ref i)) 0)
                                (not (equal? (nth ref i) ref-normal))))
               (range 0 (length ref))))
     (define (index-in lst v)
       (let loop ((xs lst) (i 0))
         (cond ((null? xs) -1)
               ((= (car xs) v) i)
               (else (loop (cdr xs) (+ i 1))))))
     (define (fill-of tmp-row)  ;; the row's color off the line columns
       (let loop ((cx 0))
         (cond ((>= cx tmp-w) 0)
               ((member? cx line-cols) (loop (+ cx 1)))
               (else (nth tmp-row cx)))))
     (build-grid (length ref) (length (first ref)) (rr cc)
                 (let ((si (index-in ref-specials rr)))
                   (if (>= si 0)
                       (let* ((tmp-row (nth tmp (nth tmp-specials si)))
                              (fill (fill-of tmp-row)))
                         (if (member? cc ref-line-cols)
                             (let* ((k (index-in ref-line-cols cc))
                                    (tv (nth tmp-row (nth line-cols k)))
                                    (lc (nth line-colors k)))
                               (if (= tv lc) lc fill))
                             fill))
                       (if (member? cc ref-line-cols)
                           (nth line-colors (index-in ref-line-cols cc))
                           0)))))))
'''

_REF_SPECIALS = '''     (define ref-specials
       (filter (lambda (i) (and (> (yellows (nth ref i)) 0)
                                (not (equal? (nth ref i) ref-normal))))
               (range 0 (length ref))))'''
_REVERSED_REF_SPECIALS = '''     (define ref-specials
       (reverse
        (filter (lambda (i) (and (> (yellows (nth ref i)) 0)
                                 (not (equal? (nth ref i) ref-normal))))
                (range 0 (length ref)))))'''


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _validate_mapping_order(value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_MAPPING_ORDERS:
        raise ValueError(
            "special_mapping_order must be one of "
            f"{ALLOWED_MAPPING_ORDERS}, got {value!r}"
        )
    return value


def choose_parameters(episode_seed: int) -> dict[str, str]:
    if type(episode_seed) is not int:
        raise TypeError("episode_seed must be an integer")
    return {
        PARAMETER_NAME: ALLOWED_MAPPING_ORDERS[
            episode_seed % len(ALLOWED_MAPPING_ORDERS)
        ]
    }


def render_program(special_mapping_order: str = DEFAULT_MAPPING_ORDER) -> str:
    order = _validate_mapping_order(special_mapping_order)
    if order == DEFAULT_MAPPING_ORDER:
        return _CANONICAL_PROGRAM
    if _REF_SPECIALS not in _CANONICAL_PROGRAM:
        raise RuntimeError("canonical rule template no longer contains ref-specials")
    return _CANONICAL_PROGRAM.replace(_REF_SPECIALS, _REVERSED_REF_SPECIALS, 1)


def rule_sha256(special_mapping_order: str) -> str:
    return sha256_text(render_program(special_mapping_order))


def _selected_generator():
    return load_selected_generator(TASK_ID, root=find_root(__file__))


def build_input(episode_seed: int, pair_index: int) -> list[list[int]]:
    """Build a lawful three-special input that distinguishes both settings."""
    if type(episode_seed) is not int:
        raise TypeError("episode_seed must be an integer")
    if type(pair_index) is not int:
        raise TypeError("pair_index must be an integer")
    if pair_index < 0:
        raise ValueError("pair_index must be nonnegative")
    generator, _source, _digest = _selected_generator()
    sample_index = 1 + 3 * pair_index  # always the three-special profile
    band = ("easy", "medium", "hard")[pair_index % 3]
    return generator.generate(episode_seed, sample_index, difficulty=band)


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def execute(grid: list[list[int]], program: str, bridge: RacketBridge) -> list[list[int]]:
    """Execute one exact materialized rule program on one input grid."""
    # This canonical lambda uses the rule! host bindings h and w.  The task
    # runtime omits the optional source parser used by wrap_rule, and this rule
    # contains no dictionary literals or for/X shorthand, so reproduce only
    # the documented lambda preamble after the shared comment/wrapper steps.
    body = strip_rule_wrapper(strip_line_comments(program))
    callable_rule = (
        "(lambda (g) (let* ((h (rows g)) (w (cols g))) "
        f"({body} g)))"
    )
    return bridge.eval_text(f"({callable_rule} {_grid_literal(grid)})")


def _validate_counts(n_train: Any, n_test: Any) -> tuple[int, int]:
    for name, value in (("n_train", n_train), ("n_test", n_test)):
        if type(value) is not int or not 1 <= value <= 10:
            raise ValueError(f"{name} must be an integer in 1..10")
    return n_train, n_test


def _build_episode(
    episode_seed: int,
    order: str,
    n_train: int,
    n_test: int,
    bridge: RacketBridge,
) -> dict[str, Any]:
    programs = {value: render_program(value) for value in ALLOWED_MAPPING_ORDERS}
    selected_program = programs[order]
    selected_hash = sha256_text(selected_program)
    other = next(value for value in ALLOWED_MAPPING_ORDERS if value != order)
    generator, source, source_sha = _selected_generator()

    pairs: list[dict[str, Any]] = []
    execution: list[dict[str, Any]] = []
    rival_outputs: list[list[list[int]]] = []
    for pair_index in range(n_train + n_test):
        grid = build_input(episode_seed, pair_index)
        selected_output = execute(grid, selected_program, bridge)
        rival_output = execute(grid, programs[other], bridge)
        if selected_output == rival_output:
            raise RuntimeError(
                f"pair {pair_index} does not distinguish mapping-order settings"
            )
        if order == DEFAULT_MAPPING_ORDER and selected_output != generator.rule_mirror(grid):
            raise RuntimeError("canonical prototype setting diverges from selected rule")
        pairs.append({"input": deepcopy(grid), "output": selected_output})
        rival_outputs.append(rival_output)
        execution.append(
            {
                "pair_index": pair_index,
                "input_sha256": sha256_text(json.dumps(grid, separators=(",", ":"))),
                "output_sha256": sha256_text(
                    json.dumps(selected_output, separators=(",", ":"))
                ),
                "program_sha256": selected_hash,
                "rival_program_sha256": sha256_text(programs[other]),
                "matches_selected_rule": execute(grid, selected_program, bridge)
                == selected_output,
                "differs_from_parameter_rival": rival_output != selected_output,
            }
        )

    return {
        "schema": "d5178d26d905-parametric-mapping-order-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": episode_seed,
        "parameters": {PARAMETER_NAME: order},
        "default_setting": DEFAULT_MAPPING_ORDER,
        "program": selected_program,
        "program_sha256": selected_hash,
        "selected_generator_path": str(source),
        "selected_generator_sha256": source_sha,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "execution": execution,
        "parameter_rival": other,
        "rival_outputs": {
            "train": rival_outputs[:n_train],
            "test": rival_outputs[n_train:],
        },
    }


def generate_episode(
    episode_seed: int,
    *,
    special_mapping_order: str | None = None,
    n_train: int = 3,
    n_test: int = 1,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Choose one rule setting and execute it unchanged for a whole episode."""
    if type(episode_seed) is not int:
        raise TypeError("episode_seed must be an integer")
    n_train, n_test = _validate_counts(n_train, n_test)
    order = (
        choose_parameters(episode_seed)[PARAMETER_NAME]
        if special_mapping_order is None
        else _validate_mapping_order(special_mapping_order)
    )
    if bridge is not None:
        return _build_episode(episode_seed, order, n_train, n_test, bridge)
    with RacketBridge() as own_bridge:
        return _build_episode(episode_seed, order, n_train, n_test, own_bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a challenge with hidden parameter, rule text, and query labels."""
    return {
        "schema": "arc-parametric-challenge-v1",
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _source_hashes() -> dict[str, str]:
    files = [
        Path(__file__),
        Path(__file__).resolve().parents[2] / "tests/test_parametric_mapping_order.py",
    ]
    hashes: dict[str, str] = {}
    for path in files:
        if path.is_file():
            try:
                name = str(path.relative_to(find_root(__file__)))
            except ValueError:
                name = str(path)
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)

    with RacketBridge() as bridge:
        episodes = [
            generate_episode(
                args.seed,
                special_mapping_order=order,
                n_train=3,
                n_test=1,
                bridge=bridge,
            )
            for order in ALLOWED_MAPPING_ORDERS
        ]
        witness_grid = build_input(args.seed, 0)
        witness = {
            "input": witness_grid,
            "outputs": {
                order: execute(witness_grid, render_program(order), bridge)
                for order in ALLOWED_MAPPING_ORDERS
            },
        }
        runtime_identity = bridge.runtime_identity

    for index, episode in enumerate(episodes):
        (args.out / f"public-{index}.json").write_text(
            json.dumps(public_challenge(episode), indent=2) + "\n"
        )
        (args.out / f"private-{index}.json").write_text(
            json.dumps(episode, indent=2) + "\n"
        )
        (args.out / f"rule-{index}.rkt").write_text(episode["program"])

    all_demos_refute = all(
        all(item["differs_from_parameter_rival"] for item in episode["execution"][:3])
        for episode in episodes
    )
    receipt = {
        "schema": "d5178d26d905-parametric-receipt-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": args.seed,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_MAPPING_ORDERS),
            "default": DEFAULT_MAPPING_ORDER,
        },
        "argv": sys.argv,
        "runtime_identity": runtime_identity,
        "source_sha256": _source_hashes(),
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": 3, "test": 1},
        "all_labels_executed_in_racket": True,
        "all_demonstrations_refute_other_setting": all_demos_refute,
        "canonical_default_matches_selected_rule": all(
            item["output"]
            == _selected_generator()[0].rule_mirror(item["input"])
            for item in episodes[0]["train"] + episodes[0]["test"]
        ),
        "limitations": [
            "Two mapping-order settings only; the canonical production path is unchanged.",
            "Inputs use the repaired generator's three-special profile at four finite seeds/indices.",
            "Every demonstration distinguishes the declared alternative, but this is not a universal identifiability proof.",
            "Prototype evidence does not grant source, variant, approval, or training admission.",
        ],
    }
    (args.out / "witness.json").write_text(json.dumps(witness, indent=2) + "\n")
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "complete_episodes": receipt["complete_episodes"],
                "executed_pairs": 4 * len(episodes),
                "out": str(args.out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
