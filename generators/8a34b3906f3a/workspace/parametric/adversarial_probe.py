"""Bounded adversarial probe for the 8a34b3906f3a parametric family.

This is intentionally reusable by later agents: it attacks the minimum lesson,
matched-input contract, sampler boundaries, semantic selector rivals, public
projection, malformed private episodes, and (optionally) protected-Racket
execution. Results are finite evidence, never a uniqueness proof.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
_PATH = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location("_probe_target_8a34b3906f3a", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(PROTOTYPE)


def _expect_rejection(name: str, episode: dict[str, Any], mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    candidate = copy.deepcopy(episode)
    mutate(candidate)
    try:
        PROTOTYPE.certify(candidate)
    except (TypeError, ValueError) as exc:
        return {"attack": name, "rejected": True, "error": str(exc)}
    return {"attack": name, "rejected": False, "error": None}


def _first_background(grid: list[list[int]]) -> tuple[int, int]:
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                return r, c
    raise ValueError("probe expected a background cell")


def _negative_verifier_rows(episode: dict[str, Any]) -> list[dict[str, Any]]:
    def forge_program(candidate: dict[str, Any]) -> None:
        candidate["program_solution"] = PROTOTYPE.program({"completion_style": "same_color"})

    def forge_label(candidate: dict[str, Any]) -> None:
        candidate["train"][0]["output"][0][0] = 7

    def duplicate_input(candidate: dict[str, Any]) -> None:
        candidate["test"][0]["input"] = copy.deepcopy(candidate["train"][0]["input"])

    def bool_cell(candidate: dict[str, Any]) -> None:
        candidate["test"][0]["input"][0][0] = True

    def unknown_color(candidate: dict[str, Any]) -> None:
        r, c = _first_background(candidate["train"][0]["input"])
        candidate["train"][0]["input"][r][c] = 7

    def remove_payload_cell(candidate: dict[str, Any]) -> None:
        scene = PROTOTYPE.analyze_parametric_scene(candidate["train"][0]["input"])
        r, c = scene["payload_cells"][str(PROTOTYPE.KEY_COLORS[0])][0]
        candidate["train"][0]["input"][r][c] = 0

    def future_output_in_public_shape(candidate: dict[str, Any]) -> None:
        candidate["test"][0]["future_output"] = copy.deepcopy(candidate["test"][0]["output"])

    return [
        _expect_rejection("forged_program", episode, forge_program),
        _expect_rejection("forged_label", episode, forge_label),
        _expect_rejection("duplicate_input", episode, duplicate_input),
        _expect_rejection("boolean_cell", episode, bool_cell),
        _expect_rejection("unknown_color", episode, unknown_color),
        _expect_rejection("broken_payload", episode, remove_payload_cell),
        _expect_rejection("extra_private_pair_field", episode, future_output_in_public_shape),
    ]


def _public_projection_findings(episode: dict[str, Any], seed: int, style: str) -> list[str]:
    findings: list[str] = []
    view_hashes = []
    forbidden = (b"completion_style", b"selected_color", b"program", b"query_outputs", b"source_indices")
    for index in range(4):
        view = PROTOTYPE.public_turn(episode, index)
        raw = PROTOTYPE._raw(view)
        view_hashes.append(hashlib.sha256(raw).hexdigest())
        if set(view) != {"train", "test"} or len(view["test"]) != 1 or set(view["test"][0]) != {"input"}:
            findings.append(f"seed {seed} {style}: malformed public turn {index}")
        for token in forbidden:
            if token in raw:
                findings.append(f"seed {seed} {style}: public turn {index} leaked {token.decode()}")
    if len(set(view_hashes)) != 4:
        findings.append(f"seed {seed} {style}: four public query turns were not distinct")
    return findings


def run_probe(*, seed_count: int = 64, racket_seed_count: int = 4) -> dict[str, Any]:
    if type(seed_count) is not int or seed_count < 1:
        raise ValueError("seed_count must be a positive exact integer")
    if type(racket_seed_count) is not int or not 0 <= racket_seed_count <= seed_count:
        raise ValueError("racket_seed_count must be an exact integer in 0..seed_count")

    findings: list[str] = []
    query_sizes: set[int] = set()
    selected_colors: set[int] = set()
    missing_quadrants: set[int] = set()
    minimum_demo_episodes = 0
    maximum_demo_episodes = 0
    protected_racket_pairs = 0
    input_bank_hashes: set[str] = set()
    negative_rows: list[dict[str, Any]] = []

    runner = PROTOTYPE.RacketRunner() if racket_seed_count else None
    runtime = None
    if runner is not None:
        runner.__enter__()
        runtime = runner.identity
    try:
        for seed in range(seed_count):
            by_style: dict[str, dict[str, Any]] = {}
            for setting in PROTOTYPE.SETTINGS:
                style = setting["completion_style"]
                try:
                    minimum = PROTOTYPE.generate(seed, setting, 2, 4)
                    maximum = PROTOTYPE.generate(seed, setting, 6, 4)
                    minimum_demo_episodes += 1
                    maximum_demo_episodes += 1
                    min_cert = PROTOTYPE.certify(minimum)
                    PROTOTYPE.certify(maximum)
                    if min_cert["survivors"] != [setting]:
                        findings.append(f"seed {seed} {style}: selected setting not unique")
                    if style == "contact_payload":
                        if set(min_cert["selector_refutations"]) != set(PROTOTYPE.TEACHING_SELECTOR_RIVALS):
                            findings.append(f"seed {seed}: selector rival coverage incomplete")
                        if any(not rows for rows in min_cert["selector_refutations"].values()):
                            findings.append(f"seed {seed}: a selector rival survived both minimum demos")
                    by_style[style] = minimum
                    inputs = [pair["input"] for pair in minimum["train"] + minimum["test"]]
                    hashes = [PROTOTYPE.digest(grid) for grid in inputs]
                    if len(hashes) != len(set(hashes)):
                        findings.append(f"seed {seed} {style}: duplicate episode input")
                    input_bank_hashes.add(hashlib.sha256("".join(hashes).encode()).hexdigest())
                    query_sizes.update(len(pair["input"]) for pair in minimum["test"])
                    for pair in minimum["train"] + minimum["test"]:
                        scene = PROTOTYPE.analyze_parametric_scene(pair["input"])
                        selected_colors.add(scene["selected_color"])
                        missing_quadrants.add(scene["missing_quadrant"])
                        if len(set(scene["color_counts"].values())) != 1:
                            findings.append(f"seed {seed} {style}: payload color frequency shortcut")
                    findings.extend(_public_projection_findings(minimum, seed, style))
                    if runner is not None and seed < racket_seed_count:
                        cert = PROTOTYPE.certify(minimum, execute=runner)
                        if not cert["racket_checked"]:
                            findings.append(f"seed {seed} {style}: protected Racket flag absent")
                        protected_racket_pairs += len(minimum["train"]) + len(minimum["test"])
                except Exception as exc:  # probe records bounded sampler failures rather than hiding them
                    findings.append(f"seed {seed} {style}: {type(exc).__name__}: {exc}")

            if set(by_style) == {"same_color", "contact_payload"}:
                same_inputs = [pair["input"] for pair in by_style["same_color"]["train"] + by_style["same_color"]["test"]]
                contact_inputs = [pair["input"] for pair in by_style["contact_payload"]["train"] + by_style["contact_payload"]["test"]]
                if same_inputs != contact_inputs:
                    findings.append(f"seed {seed}: inputs depend on private setting")
                if seed == 0:
                    negative_rows = _negative_verifier_rows(by_style["contact_payload"])
    finally:
        if runner is not None:
            runner.__exit__(None, None, None)

    negative_all = bool(negative_rows) and all(row["rejected"] for row in negative_rows)
    if not negative_all:
        findings.append("one or more negative verifier attacks were accepted")
    if query_sizes != {21, 23, 25, 30}:
        findings.append(f"query size coverage changed: {sorted(query_sizes)}")
    if selected_colors != set(PROTOTYPE.KEY_COLORS):
        findings.append(f"selected color coverage changed: {sorted(selected_colors)}")
    if missing_quadrants != {0, 1, 2, 3}:
        findings.append(f"missing-quadrant coverage changed: {sorted(missing_quadrants)}")

    return {
        "schema": "8a34b3906f3a-adversarial-probe-v1",
        "task_id": PROTOTYPE.TASK_ID,
        "source_hashes": PROTOTYPE.source_hashes(),
        "policy": {
            "seeds": list(range(seed_count)),
            "settings": PROTOTYPE.SETTINGS,
            "demo_counts": [2, 6],
            "queries": 4,
            "racket_seed_count": racket_seed_count,
            "finite_limit": "No-finding results apply only to these seeds, declared settings and named rivals.",
        },
        "coverage": {
            "episodes": seed_count * len(PROTOTYPE.SETTINGS),
            "minimum_demo_episodes": minimum_demo_episodes,
            "maximum_demo_episodes": maximum_demo_episodes,
            "query_sizes": sorted(query_sizes),
            "selected_colors": sorted(selected_colors),
            "missing_quadrants": sorted(missing_quadrants),
            "selector_rivals": list(PROTOTYPE.TEACHING_SELECTOR_RIVALS),
            "finite_rivals": list(PROTOTYPE.EXTRA_RIVALS),
            "distinct_input_banks": len(input_bank_hashes),
            "protected_racket_pairs": protected_racket_pairs,
        },
        "negative_verifier": {
            "all_rejected": negative_all,
            "attacks": negative_rows,
        },
        "racket": runtime,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--racket-seeds", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run_probe(seed_count=args.seeds, racket_seed_count=args.racket_seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "findings": report["findings"], "coverage": report["coverage"]}, indent=2))
    return 0 if not report["findings"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
