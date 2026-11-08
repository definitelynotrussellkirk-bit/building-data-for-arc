"""Bounded peer probe; run from repository through the protected review launcher."""
from pathlib import Path
import hashlib
import json

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import load_selected_generator

TASK = "845bebcacc5c"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / TASK / "peer_result.json"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def numeric(rows):
    return [[int(v) for v in row] for row in rows]


def competitors(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x == 1}
    unseen = set(cells)
    groups = 0
    while unseen:
        groups += 1
        frontier = [unseen.pop()]
        while frontier:
            r, c = frontier.pop()
            neighbors = {(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)} & unseen
            unseen.difference_update(neighbors)
            frontier.extend(neighbors)
    counts = {"occupied_rows": len({r for r, c in cells}),
              "occupied_columns": len({c for r, c in cells}),
              "eight_connected_blue_components": groups}
    return {name: [[2] * n] if n else [[0]] for name, n in counts.items()}


def main():
    module, source, source_hash = load_selected_generator(TASK, root=ROOT)
    variants = Catalog()._variants().get(TASK)
    assert len(variants) == 1
    task = variants[0]
    program = task["program_solution"]
    apply, identity, bridge = _real_evaluator((ROOT / "shared/runtime").resolve())
    try:
        visible = []
        for name, pair in [(f"train_{i}", p) for i, p in enumerate(task["train"])] + [("original_test", task["test"])]:
            grid = numeric(pair["input"])
            gold = apply(program, grid)
            assert gold == numeric(pair["output"]), name
            rivals = competitors(grid)
            assert all(value == gold for value in rivals.values()), name
            visible.append({"name": name, "input": grid, "protected_gold": gold,
                            "competitor_outputs": rivals, "all_competitors_fit": True})

        # Finite, deterministic search; labels are never inferred in Python.
        witness = None
        for seed in range(64):
            controls = {"grid_h": 6, "grid_w": 8, "dot_count": 6}
            grid = module.generate(seed, 0, **controls)
            rivals = competitors(grid)
            count = sum(x == 1 for row in grid for x in row)
            if all(len(value[0]) < count for value in rivals.values()):
                gold = apply(program, grid)
                assert not module.self_check(grid)
                assert all(value != gold for value in rivals.values())
                witness = {"seed": seed, "sample_index": 0, "difficulty": None,
                           "overrides": controls, "input": grid, "input_sha256": digest(grid),
                           "protected_gold": gold, "competitor_outputs": rivals,
                           "self_check": [], "all_competitors_differ": True}
                break
        assert witness is not None, "No separating generated query found within 64 seeds"

        controls = {"grid_h": 7, "grid_w": 10, "dot_count": 4}
        baseline = module.generate(314159, 7, **controls, palette_kind="default", texture="default")
        aliases = module.generate(314159, 7, **controls, palette_kind="warm", texture="cool")
        unknown = module.generate(314159, 7, **controls, palette_kind="default", texture="default",
                                  __override_contract_unknown_axis__=123)
        assert aliases == baseline == unknown
        try:
            module.generate(314159, 7, difficulty="easy", grid_h=12, grid_w=14, dot_count=10)
        except ValueError as exc:
            easy_error = f"ValueError: {exc}"
        else:
            raise AssertionError("Recorded easy-domain override rejection no longer reproduces")

        zero = module.generate(314159, 7, texture="no_dots")
        zero_gold = apply(program, zero)
        assert zero_gold == [[0]]

        result = {"schema": "bounded-peer-learnability-v1", "task_id": TASK,
                  "status": "finding_reproduced", "source_path": str(source.relative_to(ROOT)),
                  "source_sha256": source_hash,
                  "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                  "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "racket": identity, "protected_gold_evaluations": len(visible) + 2,
                  "visible_cases": visible, "generated_query": witness,
                  "searched_seeds": list(range(witness["seed"] + 1)),
                  "prior_contract_finding": {"seed": 314159, "sample_index": 7, "overrides": controls,
                     "palette_and_texture_changes_ignored": True, "unknown_key_ignored": True,
                     "same_grid_sha256": digest(baseline), "easy_domain_error": easy_error},
                  "no_dots": {"input": zero, "protected_gold": zero_gold,
                              "self_check": module.self_check(zero),
                              "comment_mismatch": "Generator comment says empty output; canonical Racket returns [[0]]."},
                  "interpretation": "The three named competitors fit both canonical demos and the original test. They disagree with canonical Racket on this valid generated query. A demo with repeated rows/columns and diagonal contact would reject these three competitors.",
                  "limits": "Three finite Python competitors and one separating generated query; no claim that the original test is ambiguous under these competitors, no universal identifiability claim, no episode-frequency audit, no source repair or owner acceptance.",
                  "source_changed": False}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": result["status"], "result": str(OUT), "source_sha256": source_hash,
                          "witness_seed": witness["seed"], "gold_width": len(witness["protected_gold"][0]),
                          "competitor_widths": {k: len(v[0]) for k, v in witness["competitor_outputs"].items()},
                          "protected_gold_evaluations": result["protected_gold_evaluations"],
                          "probe_sha256": result["probe_sha256"],
                          "result_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest()}, sort_keys=True))
    finally:
        bridge.close()


if __name__ == "__main__":
    main()
