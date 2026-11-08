"""Bounded learnability, public-projection and causal checks for d9d4f0ebb48b.

This is reviewer tooling, not an admission path.  It checks a finite named rival
set against visible demonstrations and can retain one protected-Racket shortcut
witness.  A passing report does not prove universal rule uniqueness.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location("_d9d4f0ebb48b_audit_prototype", _PROTOTYPE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load prototype: {_PROTOTYPE_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

SHORTCUTS = (
    "always_first",
    "always_last",
    "marker_color",
    "reverse_selector",
    "off_by_one",
)


def _paint_all(grid: list[list[int]], color: int) -> list[list[int]]:
    out = copy.deepcopy(grid)
    for center in prototype.find_plus_centers(grid):
        prototype._paint_footprint(out, center, color)
    return out


def rival_output(grid: list[list[int]], rival: str) -> list[list[int]]:
    """Evaluate one explicit finite rival with an independent intermediate."""
    if rival in prototype.MODES:
        return prototype.apply_mode(grid, rival)
    centers = prototype.find_plus_centers(grid)
    if not centers:
        raise ValueError("rivals require at least one true plus")
    selector_count = sum(cell != 0 for cell in grid[0])
    if not 1 <= selector_count <= len(centers):
        raise ValueError("selector must index a true plus")
    if rival == "always_first":
        selected = centers[0]
        color = grid[selected[0]][selected[1]]
    elif rival == "always_last":
        selected = centers[-1]
        color = grid[selected[0]][selected[1]]
    elif rival == "marker_color":
        color = grid[0][0]
    elif rival == "reverse_selector":
        selected = centers[-selector_count]
        color = grid[selected[0]][selected[1]]
    elif rival == "off_by_one":
        selected = centers[selector_count % len(centers)]
        color = grid[selected[0]][selected[1]]
    else:
        raise ValueError(f"unknown rival: {rival}")
    return _paint_all(grid, color)


def wrong_program(rival: str = "always_first") -> str:
    """Return a Racket counterfactual with an explicitly wrong intermediate."""
    if rival != "always_first":
        raise ValueError("only the retained always_first Racket ablation is supported")
    source = prototype.program({"fill_color_mode": "selector_source"})
    old = "(selected (list-ref centers (- selector-count 1)))"
    new = "(selected (first centers))"
    if source.count(old) != 1:
        raise ValueError("selector-source program guard failed")
    return source.replace(old, new, 1)


def visible_audit(seed: int, mode: str, demos: int = 2, queries: int = 4) -> dict[str, Any]:
    """Fit declared settings and named shortcuts to demonstrations only."""
    episode = prototype.generate(seed, {"fill_color_mode": mode}, demos, queries)
    declared = {}
    survivors = []
    for candidate in prototype.MODES:
        predictions = [rival_output(pair["input"], candidate) for pair in episode["train"]]
        fits = all(prediction == pair["output"] for prediction, pair in zip(predictions, episode["train"]))
        declared[candidate] = {
            "fits_all_demos": fits,
            "query_disagreements": sum(
                rival_output(pair["input"], candidate) != pair["output"]
                for pair in episode["test"]
            ),
        }
        if fits:
            survivors.append(candidate)
    shortcuts = {}
    for rival in SHORTCUTS:
        predictions = [rival_output(pair["input"], rival) for pair in episode["train"]]
        shortcuts[rival] = {
            "fits_all_demos": all(
                prediction == pair["output"]
                for prediction, pair in zip(predictions, episode["train"])
            ),
            "first_eliminating_demo": next(
                (
                    index
                    for index, (prediction, pair) in enumerate(zip(predictions, episode["train"]))
                    if prediction != pair["output"]
                ),
                None,
            ),
            "query_disagreements": sum(
                rival_output(pair["input"], rival) != pair["output"]
                for pair in episode["test"]
            ),
        }
    inputs = [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]
    return {
        "seed": seed,
        "setting": {"fill_color_mode": mode},
        "demos": demos,
        "query_count": queries,
        "survivors": survivors,
        "declared_settings": declared,
        "shortcuts": shortcuts,
        "all_inputs_distinct": len(inputs) == len(set(inputs)),
        "scope": "Two declared settings plus five named shortcuts; demonstrations only; not universal uniqueness.",
    }


def public_projection(seed: int, mode: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    """Check visible bytes, private invariance and first-turn slicing."""
    episode = prototype.generate(seed, {"fill_color_mode": mode}, demos, queries)
    private = {
        **copy.deepcopy(episode),
        "settings": {"fill_color_mode": mode},
        "private_note": "must not affect public identity",
    }
    visible = public_challenge_bytes(private)
    altered = copy.deepcopy(private)
    altered["settings"] = {"fill_color_mode": "local" if mode != "local" else "selector_source"}
    altered["program_solution"] = "(rule! g)"
    altered["private_note"] = "changed"
    for pair in altered["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    invariant = public_challenge_bytes(altered) == visible

    first_turn_source = {"train": private["train"], "test": private["test"][:1]}
    first_turn = public_challenge_bytes(first_turn_source)
    single_query_view = {"train": copy.deepcopy(private["train"]), "test": [copy.deepcopy(private["test"][0])]}
    single_turn = public_challenge_bytes(single_query_view)
    parsed_first = json.loads(first_turn)
    return {
        "seed": seed,
        "setting": {"fill_color_mode": mode},
        "public_id": public_challenge_id(private),
        "public_sha256": hashlib.sha256(visible).hexdigest(),
        "public_bytes": visible.decode("utf-8"),
        "private_metadata_invariant": invariant,
        "first_turn_sha256": hashlib.sha256(first_turn).hexdigest(),
        "first_turn_matches_single_query": first_turn == single_turn,
        "future_queries_absent_from_first_turn": (
            len(parsed_first["test"]) == 1
            and parsed_first["test"][0]["input"] == private["test"][0]["input"]
        ),
        "scope": "Projection and first-turn structure only; controller timing is not executed here.",
    }


def _execute_racket(program: str, grid: list[list[int]], bridge: Any) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped = wrap_rule(program)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrapped} {literal})")


def build_report() -> dict[str, Any]:
    """Build a compact report including one protected-Racket wrong-intermediate case."""
    audits = [
        visible_audit(seed, mode, demos=2, queries=4)
        for seed in (0, 17, 2718)
        for mode in prototype.MODES
    ]
    projections = [public_projection(31, mode, demos=3, queries=4) for mode in prototype.MODES]

    from arc_repl.racket_bridge import RacketBridge

    episode = prototype.generate(0, {"fill_color_mode": "selector_source"}, demos=2, queries=4)
    # Pair one uses selector length two, so always-first is a concrete wrong intermediate.
    pair = episode["train"][1]
    correct_program = prototype.program({"fill_color_mode": "selector_source"})
    counterfactual_program = wrong_program("always_first")
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        correct = _execute_racket(correct_program, pair["input"], bridge)
        counterfactual = _execute_racket(counterfactual_program, pair["input"], bridge)
    finally:
        bridge.close()
    intermediate = prototype.selector_intermediate(pair["input"])
    centers = prototype.find_plus_centers(pair["input"])
    first_row, first_col = centers[0]
    retained_case = {
        "input": pair["input"],
        "settings": {"fill_color_mode": "selector_source"},
        "correct_intermediate": intermediate,
        "wrong_intermediate": {
            "selected_index": 0,
            "selected_center": [first_row, first_col],
            "selected_color": pair["input"][first_row][first_col],
        },
        "program": correct_program,
        "output": correct,
        "counterfactual_program": counterfactual_program,
        "counterfactual_output": counterfactual,
        "ablation": "wrong_intermediate",
        "changes_final_output": correct != counterfactual,
    }
    return {
        "schema": "d9d4f0ebb48b-parametric-self-audit-v1",
        "status": "passed"
        if all(a["survivors"] == [a["setting"]["fill_color_mode"]] for a in audits)
        and all(not row["fits_all_demos"] for a in audits for row in a["shortcuts"].values())
        and all(p["private_metadata_invariant"] for p in projections)
        and retained_case["changes_final_output"]
        else "failed",
        "audits": audits,
        "public_projections": projections,
        "racket": {"backend": identity.get("backend"), "protected": identity.get("protected")},
        "retained_racket_case": retained_case,
        "limits": "Finite declared settings and five named shortcuts over three seeds; no universal uniqueness or model-learning claim.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    options = parser.parse_args(argv)
    report = build_report()
    destination = Path(options.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "out": str(destination),
        "audits": len(report["audits"]),
        "racket": report["racket"],
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
