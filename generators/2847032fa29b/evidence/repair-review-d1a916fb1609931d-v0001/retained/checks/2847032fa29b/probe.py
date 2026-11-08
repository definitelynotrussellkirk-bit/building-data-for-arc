"""Bounded peer audit of bbox-area ordering versus canonical cell count."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import load_selected_generator


TASK = "2847032fa29b"
EXPECTED = "73496bd89160cf7fb8c32470180b58bb66114e6abc89727e7347d473832eb362"
ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent


def bbox_gallery(module, grid):
    components = sorted(module._components(grid), key=lambda o:
                        ((o["r2"] - o["r1"] + 1) * (o["c2"] - o["c1"] + 1), o["color"]))
    crops = [module._crop(grid, obj) for obj in components]
    result = [[0] * (sum(len(crop[0]) for crop in crops) + len(crops) - 1)
              for _ in range(max(len(crop) for crop in crops))]
    left = 0
    for crop in crops:
        for row, values in enumerate(crop):
            result[row][left:left + len(values)] = values
        left += len(crop[0]) + 1
    return result


def main():
    module, source, digest = load_selected_generator(TASK, root=ROOT)
    if digest != EXPECTED:
        raise ValueError("Peer source differs from the pinned assignment")
    catalog = Catalog(ROOT)
    programs = {v["program_solution"] for v in catalog.get(TASK)["variants"]}
    if len(programs) != 1:
        raise ValueError("Expected one canonical program")
    canonical = next(iter(programs))
    rival = canonical
    for variable in ("a", "b"):
        area = f"(* (+ 1 (- (obj-r2 {variable}) (obj-r1 {variable}))) (+ 1 (- (obj-c2 {variable}) (obj-c1 {variable}))))"
        rival = rival.replace(f"(obj-size {variable})", area)
    if rival == canonical:
        raise ValueError("Rival did not change the ordering metric")
    searched, rejected, selected = [], [], None
    for seed in range(16):
        try:
            inputs = [module.generate(seed=seed, sample_index=index) for index in range(7)]
            for grid in inputs:
                errors = module.self_check(grid)
                if errors:
                    raise ValueError(str(errors))
            gold = [module.rule_mirror(grid) for grid in inputs]
            alternate = [bbox_gallery(module, grid) for grid in inputs]
            equal = [a == b for a, b in zip(gold, alternate)]
            row = {"seed": seed, "sample_indices": list(range(7)),
                   "profiles": [module.observe_overrides(grid)["scene_profile"] for grid in inputs],
                   "demo_agreement": equal[:3], "query_agreement": equal[3:]}
            searched.append(row)
            if all(equal[:3]) and not all(equal[3:]):
                selected = (row, inputs, gold, alternate)
                break
            if selected is None:
                fallback = (row, inputs, gold, alternate)
        except (ValueError, RuntimeError) as error:
            rejected.append({"seed": seed, "error": str(error)})
    if selected is None:
        selected = fallback
    row, inputs, gold, alternate = selected
    cases = []
    with _local_imports(ROOT / "shared/runtime", ROOT / "shared/runtime"):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            for index, grid in enumerate(inputs):
                output = _grid(apply(canonical, grid))
                rival_output = _grid(apply(rival, grid))
                if output != gold[index] or rival_output != alternate[index]:
                    raise ValueError("Python search interpretation disagrees with protected Racket")
                cases.append({"split": "train" if index < 3 else "test",
                              "pair_index": index if index < 3 else index - 3,
                              "sample_index": index, "input": grid,
                              "canonical_output": output, "rival_output": rival_output,
                              "agrees": output == rival_output})
        finally:
            bridge.close()
    finding = all(case["agrees"] for case in cases[:3]) and any(not case["agrees"] for case in cases[3:])
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError("Peer source changed during the probe")
    report = {
        "schema": "arcpuzzles-bounded-peer-shortcut-review-v1", "task_id": TASK,
        "status": "teaching_shortcut_found" if finding else "no_shortcut_found_in_bounded_search",
        "generator_path": str(source.relative_to(ROOT)), "generator_sha256": digest,
        "canonical_rule_hash": catalog.describe(TASK)["rule_hash"],
        "canonical_program": canonical, "rival_program": rival,
        "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
        "rival": "Sort by bounding-box area then numeric color; preserve canonical crops, alignment, and gaps.",
        "search": {"seed_bound": list(range(16)), "tested_episodes": len(searched),
                   "python_generated_inputs": 7 * len(searched), "rejected": rejected, "results": searched},
        "selected_lesson": row, "cases": cases, "racket": identity,
        "racket_evaluations": 2 * len(cases),
        "suggested_repair": "When a query distinguishes cell count from bbox-area order, select a distinguishing demonstration without increasing the demonstration count.",
        "source_modified": False, "training_admitted": False,
        "limits": "One declared rival, at most sixteen same-seed lessons assembled from seven consecutive generator draws (three demos/four queries); Python presearch followed by protected Racket on the one retained lesson only. No claim of universal ambiguity, native lesson-assembly enforcement, or acceptance.",
    }
    path = HERE / "bbox-order-shortcut.json"
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "seed": row["seed"],
                      "tested_episodes": len(searched), "racket_evaluations": 2 * len(cases),
                      "evidence": str(path), "demo_agreement": [c["agrees"] for c in cases[:3]],
                      "query_agreement": [c["agrees"] for c in cases[3:]]}, sort_keys=True))


if __name__ == "__main__":
    main()
