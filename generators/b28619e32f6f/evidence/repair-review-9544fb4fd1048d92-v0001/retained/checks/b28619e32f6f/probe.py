"""Bounded default-lesson threshold rival; final labels execute protected Racket.

Run through review.py run from the packet root. No production source is edited.
Search is one fixed rival, seeds 0..31, first default 3 demos and next query.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import signal
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "repo"
TASK = "b28619e32f6f"


def sha(value):
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode()).hexdigest()


def execute(bridge, source, grid):
    from puzzle_generators.rule_wrap import wrap_rule
    datum = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(source)} {datum})")


def main():
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("120s probe cap")))
    signal.alarm(120)
    started = time.monotonic()
    source_path = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("_b286_bounded_probe", source_path)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    assert gen.EXAMPLES_NEEDED == 3
    canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
    with canonical_path.open() as handle:
        canonical = next(json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK)
    intended = canonical["program_solution"]
    normalized = sha(" ".join(intended.split()))
    assert normalized[:12] == gen.RULE_HASH, (normalized, gen.RULE_HASH)
    marker = "(<= size 24)"
    assert intended.count(marker) == 1
    rival = intended.replace(marker, "(<= size 16)")
    result = {
        "schema": "b28619e32f6f-bounded-peer-v1",
        "task_id": TASK,
        "source_sha256": sha(source_path.read_text()),
        "probe_sha256": sha(Path(__file__).read_text()),
        "canonical_file_sha256": hashlib.sha256(canonical_path.read_bytes()).hexdigest(),
        "review_index_sha256": sha((source_path.parent / "evidence/review_index.json").read_text()),
        "declared_examples_needed": gen.EXAMPLES_NEEDED,
        "intended_program": intended,
        "rival_program": rival,
        "intended_program_sha256": sha(intended),
        "intended_normalized_rule_sha256": normalized,
        "declared_rule_hash": gen.RULE_HASH,
        "rival_program_sha256": sha(rival),
        "rival_description": "Preserve topology and lower threshold; medium regions use <=16 instead of <=24.",
        "search_bound": {"rivals": 1, "max_seeds": 32, "indices": [0, 1, 2, 3], "difficulty": None, "overrides": {}, "timeout_seconds": 120},
        "searched": [], "cases": [], "protected_racket_evaluations": 0,
        "limits": "Finite one-rival check of default initial 3-demo lessons and next query only. No mutations; no approval or training claim. Prior equality-boundary audit remains unresolved."
    }
    selected = None
    for seed in range(32):
        grids = [gen.generate(seed, index) for index in range(4)]
        errors = [gen.self_check(grid) for grid in grids]
        assert errors == [[], [], [], []], errors
        areas = [[r["size"] for r in gen._zero_regions(grid) if r["enclosed"]] for grid in grids]
        # Python finds candidates only. Final outputs below are both actual Racket.
        agrees = [all(not (16 < size <= 24) for size in sizes) for sizes in areas]
        result["searched"].append({"seed": seed, "areas": areas, "predicted_agreements": agrees})
        if agrees == [True, True, True, False]:
            selected = (seed, grids, areas)
            break
    if selected is None:
        result["status"] = "finite_no_finding"
    else:
        from arc_repl.racket_bridge import RacketBridge
        seed, grids, areas = selected
        result["selected_seed"] = seed
        with RacketBridge(timeout=10) as bridge:
            result["runtime_identity"] = bridge.runtime_identity
            assert bridge.runtime_identity.get("backend") == "racket"
            assert bridge.runtime_identity.get("protected") is True
            for index, grid in enumerate(grids):
                actual = execute(bridge, intended, grid)
                wrong = execute(bridge, rival, grid)
                result["protected_racket_evaluations"] += 2
                result["cases"].append({"split": "train" if index < 3 else "test", "sample_index": index,
                    "seed": seed, "input": grid, "input_sha256": sha(grid), "self_check": gen.self_check(grid),
                    "enclosed_areas": areas[index], "profile": gen.observe_overrides(grid),
                    "intended_output": actual, "intended_output_sha256": sha(actual),
                    "rival_output": wrong, "rival_output_sha256": sha(wrong), "agreement": actual == wrong,
                    "different_cells": sum(a != b for x, y in zip(actual, wrong) for a, b in zip(x, y))})
        assert [case["agreement"] for case in result["cases"]] == [True, True, True, False]
        demos = [{"input": c["input"], "output": c["intended_output"]} for c in result["cases"][:3]]
        query = {"input": result["cases"][3]["input"], "output": result["cases"][3]["intended_output"]}
        result["current_lesson_identifiable_reasons"] = gen.lesson_identifiable(demos, query)
        result["status"] = "finding_reproduced_repair_pending"
    result["elapsed_seconds"] = time.monotonic() - started
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    signal.alarm(0)
    print(json.dumps({key: result[key] for key in ("status", "source_sha256", "protected_racket_evaluations", "elapsed_seconds")}))
    if selected:
        print(json.dumps({"seed": result["selected_seed"], "cases": [{key: c[key] for key in ("split", "sample_index", "enclosed_areas", "agreement", "different_cells")} for c in result["cases"]], "current_lesson_identifiable_reasons": result["current_lesson_identifiable_reasons"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
