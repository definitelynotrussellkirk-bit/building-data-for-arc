#!/usr/bin/env python3
"""Bounded protected-Racket learnability audit for b7564fb4b95d."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK_ID = "b7564fb4b95d"
HOME = Path(__file__).resolve().parent
REPO = HOME.parents[3]
RUNTIME = REPO / "shared" / "runtime"
SEEDS = (0, 17, 97)
DEMO_COUNTS = (2, 3, 6)


def _load_exact(name: str, path: Path):
    body = path.read_bytes()
    unique = name + "_" + hashlib.sha256(str(path).encode() + body).hexdigest()
    spec = importlib.util.spec_from_file_location(unique, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def build_report() -> dict:
    prototype = _load_exact("audit_b756_prototype", HOME / "prototype.py")
    programs = {
        mode: prototype.program({prototype.PARAMETER: mode})
        for mode in prototype.MODES
    }
    cache: dict[tuple[str, str], list[list[int]]] = {}
    checks = []
    evaluations = 0
    causal_case = None

    with _local_imports(RUNTIME, HOME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
                nonlocal evaluations
                serial = json.dumps(grid, separators=(",", ":"))
                key = (hashlib.sha256(program.encode()).hexdigest(), serial)
                if key not in cache:
                    cache[key] = apply(program, grid)
                    evaluations += 1
                return cache[key]

            for seed in SEEDS:
                for demos in DEMO_COUNTS:
                    matched_by_mode = []
                    for mode in prototype.MODES:
                        settings = {prototype.PARAMETER: mode}
                        episode = prototype.generate(seed, settings, demos, 4)
                        inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
                        matched_by_mode.append(inputs)
                        if len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) != demos + 4:
                            raise RuntimeError("duplicate visible inputs in episode")
                        maximum = prototype.generate(seed, settings, 6, 4)
                        if episode["train"] != maximum["train"][:demos] or episode["test"] != maximum["test"]:
                            raise RuntimeError("episode prefixes are not stable")

                        authoritative = [execute(programs[mode], grid) for grid in inputs]
                        claims = [pair["output"] for split in ("train", "test") for pair in episode[split]]
                        if claims != authoritative:
                            raise RuntimeError(f"Python claims disagree with Racket: seed={seed}, mode={mode}")

                        demo_inputs = [pair["input"] for pair in episode["train"]]
                        expected_demo = authoritative[:demos]
                        setting_survivors = [
                            candidate
                            for candidate in prototype.MODES
                            if [execute(programs[candidate], grid) for grid in demo_inputs] == expected_demo
                        ]
                        shortcut_survivors = [
                            name
                            for name, rival in prototype.SHORTCUTS.items()
                            if [rival(grid) for grid in demo_inputs] == expected_demo
                        ]
                        if setting_survivors != [mode] or shortcut_survivors:
                            raise RuntimeError(
                                f"lesson ambiguity seed={seed} demos={demos} mode={mode}: "
                                f"settings={setting_survivors}, shortcuts={shortcut_survivors}"
                            )
                        checks.append({
                            "seed": seed,
                            "demos": demos,
                            "queries": 4,
                            "settings": settings,
                            "racket_labels": demos + 4,
                            "setting_survivors": setting_survivors,
                            "shortcut_survivors": shortcut_survivors,
                        })

                        if mode == "command_then_reflect" and causal_case is None:
                            pair = episode["train"][0]
                            correct = execute(programs[mode], pair["input"])
                            wrong_program = prototype.counterfactual_program()
                            wrong = execute(wrong_program, pair["input"])
                            if correct == wrong:
                                raise RuntimeError("wrong-order counterfactual did not change output")
                            causal_case = {
                                "seed": seed,
                                "demos": demos,
                                "input": pair["input"],
                                "settings": settings,
                                "intermediate_value": prototype.transform_intermediate(pair["input"]),
                                "output": correct,
                                "counterfactual_output": wrong,
                                "ablation": "wrong_order",
                            }
                    if matched_by_mode[0] != matched_by_mode[1]:
                        raise RuntimeError("settings did not receive matched inputs")

                stress = prototype.generate(
                    seed, {prototype.PARAMETER: "command_then_reflect"}, 6, 4
                )["test"][3]["input"]
                facts = prototype.analyze(stress)
                if not (
                    len(stress) == 30 and len(stress[0]) == 30
                    and facts["frame_count"] == 3
                    and facts["frame_cell_count"] >= 70
                    and facts["occupied_row_span"] >= 22
                    and facts["occupied_col_span"] >= 24
                ):
                    raise RuntimeError("30x30 stress contract failed")
        finally:
            bridge.close()

    if causal_case is None:
        raise RuntimeError("no causal case retained")
    sources = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(HOME.iterdir())
        if path.is_file() and path.suffix in {".py", ".rkt", ".json", ".md"}
    }
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "source_sha256": sources,
        "racket": identity,
        "racket_evaluations": evaluations,
        "scope": {
            "seeds": list(SEEDS),
            "demo_counts": list(DEMO_COUNTS),
            "queries": 4,
            "settings": [{"transform_order": value} for value in prototype.MODES],
            "named_shortcuts": list(prototype.SHORTCUTS),
            "claim_limit": "Finite declared-setting and named-shortcut audit; not universal uniqueness or training evidence.",
        },
        "checks": checks,
        "causal_case": causal_case,
        "conclusion": "All bounded labels matched protected Racket; each visible lesson isolated its setting and refuted every declared shortcut.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(args.out)
    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "checks": len(report["checks"]),
        "racket_evaluations": report["racket_evaluations"],
        "protected": report["racket"].get("protected"),
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
