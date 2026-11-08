#!/usr/bin/env python3
"""Findings-only audit, authoring data allowed; never imports private runners."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys


TASK = "0f7d80015d9d"
HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
GENERATOR = REPO / "generators" / TASK / "generator.py"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return digest_bytes(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def relative_marker_order(grid):
    """Stamp right iff red is left of cyan; does not compute rectangle midpoint."""
    out = copy.deepcopy(grid)
    cells = {color: [(r, c) for r, row in enumerate(grid)
                     for c, value in enumerate(row) if value == color]
             for color in (2, 5, 8)}
    red, cyan = cells[2][0], cells[8][0]
    bottom = max(r for r, _ in cells[5])
    left = min(c for _, c in cells[5])
    right = max(c for _, c in cells[5])
    destination = right + 1 if red[1] < cyan[1] else left - 1
    out[red[0]][red[1]] = 7
    out[cyan[0]][cyan[1]] = 2
    out[bottom][destination] = 8
    return out


def main():
    source_hash = digest_bytes(GENERATOR.read_bytes())
    spec = importlib.util.spec_from_file_location("audit_generator", GENERATOR)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    catalog = Catalog(REPO)
    descriptor = catalog.describe(TASK)
    pairs = canonical_pairs(TASK, root=REPO)
    source = {
        "task_id": TASK,
        "generator_version": gen.VERSION,
        "generator_path": str(GENERATOR.relative_to(PACKET)),
        "generator_sha256": source_hash,
        "catalog_rule_hash": descriptor["rule_hash"],
        "declared_rule_hash": gen.RULE_HASH,
        "canonical_ledger_sha256": digest_bytes(
            (REPO / "shared/data/canonical/puzzles.jsonl").read_bytes()),
        "probe_sha256": digest_bytes(Path(__file__).read_bytes()),
    }
    canonical = []
    declared = {}
    declarations = {
        "CANONICAL_SHORTCUTS": gen.CANONICAL_SHORTCUTS,
        "LESSON_COMPETITORS": gen.LESSON_COMPETITORS,
    }
    for declaration, rivals in declarations.items():
        declared[declaration] = {}
        for name, rival in rivals.items():
            outcomes = []
            for pair in pairs:
                try:
                    outcomes.append({"matches": rival(copy.deepcopy(pair["input"])) == pair["output"]})
                except Exception as exc:
                    outcomes.append({"matches": False, "error": f"{type(exc).__name__}: {exc}"})
            declared[declaration][name] = outcomes
    for pair in pairs:
        canonical.append({
            "identity": {key: pair[key] for key in ("variant", "split", "pair_index")},
            "input_sha256": digest(pair["input"]),
            "validator_errors": gen.self_check(pair["input"]),
            "strict_canonical_errors": gen.strict_canonical_like(pair["input"]),
            "python_mirror_matches_canonical": gen.rule_mirror(pair["input"]) == pair["output"],
            "new_rival_matches_canonical": relative_marker_order(pair["input"]) == pair["output"],
        })

    generated = []
    selected = []
    seeds = [0, 1, 17, 2026]
    bands = [None, "easy", "medium", "hard"]
    for band, seed, index in itertools.product(bands, seeds, range(64)):
        grid = gen.generate(seed, index, difficulty=band)
        errors = gen.self_check(grid)
        facts = gen._analyze(grid)
        record = {"seed": seed, "sample_index": index, "difficulty": band,
                  "overrides": {}, "input_sha256": digest(grid),
                  "validator_errors": errors,
                  "new_rival_matches_python_mirror": relative_marker_order(grid) == gen.rule_mirror(grid),
                  "red_order_equals_red_midpoint_side": (facts["red"][1] < facts["cyan"][1]) == facts["red_left"],
                  "scene_profile": facts["scene_profile"]}
        generated.append(record)
        if seed == 17 and index < 12:
            selected.append({"kind": "generated", **record, "input": grid})

    overrides = []
    for case, (band, height, width, aspect, profile) in enumerate(itertools.product(
            bands, [7, 19], [7, 19], gen.RECT_ASPECTS, gen.SCHEDULE_PROFILES)):
        requested = {"grid_h": height, "grid_w": width, "rect_aspect": aspect,
                     "scene_profile": profile}
        grid = gen.generate(41000 + case, case, difficulty=band, **requested)
        overrides.append({"case": case, "seed": 41000 + case, "sample_index": case,
                          "difficulty": band, "overrides": requested,
                          "input_sha256": digest(grid),
                          "observed": gen.observe_overrides(grid),
                          "validator_errors": gen.self_check(grid, meta={"overrides": requested}),
                          "all_requested_axes_observed": gen.observe_overrides(grid) == requested,
                          "new_rival_matches_python_mirror": relative_marker_order(grid) == gen.rule_mirror(grid)})

    lessons = []
    for band, start in itertools.product(bands, range(16)):
        grids = [gen.generate(17, start + offset, difficulty=band) for offset in range(5)]
        demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids[:4]]
        query = {"input": grids[4], "output": gen.rule_mirror(grids[4])}
        survivors = []
        for name, rival in gen.LESSON_COMPETITORS.items():
            if all(rival(copy.deepcopy(pair["input"])) == pair["output"] for pair in demos):
                survivors.append(name)
        lessons.append({"seed": 17, "difficulty": band, "start": start,
                        "demo_indices": list(range(start, start + 4)), "query_index": start + 4,
                        "policy": "direct raw consecutive 4-demo/1-query window; no rejection or deduplication",
                        "input_sha256s": [digest(grid) for grid in grids],
                        "validator_errors": [gen.self_check(grid) for grid in grids],
                        "lesson_identifiable_errors": gen.lesson_identifiable(demos, query),
                        "declared_rival_survivors": survivors,
                        "new_rival_fits_every_demo_and_query": all(
                            relative_marker_order(grid) == gen.rule_mirror(grid) for grid in grids)})

    hand = [[7] * 9 for _ in range(9)]
    for row in range(5, 9):
        for col in range(1, 7):
            hand[row][col] = 5
    hand[4][4] = 2
    hand[4][5] = 8
    hand_record = {
        "kind": "hand_constructed", "seed": None, "sample_index": None, "overrides": None,
        "input": hand, "input_sha256": digest(hand),
        "validator_errors": gen.self_check(hand),
        "strict_canonical_errors": gen.strict_canonical_like(hand),
        "observed_axes": gen.observe_overrides(hand),
        "passes_documented_invariants_and_validator": True,
        "belongs_to_actual_sampler_support": False,
        "sampler_exclusion_reason": "right_same_side always sets cyan_col=midpoint; here red_col=4, cyan_col=5, midpoint=3",
        "documented_domain_status": "Accepted by self_check and strict_canonical_like; obeys all INVARIANTS. The implemented sampler has narrower marker-order support.",
    }
    authority_inputs = [{"kind": "canonical", "identity": canonical[i]["identity"],
                         "input": pair["input"]} for i, pair in enumerate(pairs)]
    authority_inputs.append(hand_record)
    authority_inputs.extend(selected)
    write("input.json", [row["input"] for row in authority_inputs])
    preliminary = {
        "source": source, "canonical": canonical,
        "declared_rival_canonical_checks": declared,
        "generated_selection": {"bands": bands, "seeds": seeds, "indices_inclusive": [0, 63],
                                "count": len(generated), "unique_input_count": len({r["input_sha256"] for r in generated})},
        "generated_samples": generated, "override_samples": overrides, "lessons": lessons,
        "hand_counterexample": hand_record,
        "authority_input_metadata": [{k: v for k, v in row.items() if k != "input"} for row in authority_inputs],
    }
    write("preliminary.json", preliminary)
    argv = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
            "--input", f"../checks/audit/{TASK}/input.json", "--out", f"../checks/audit/{TASK}/racket.json"]
    run = subprocess.run(argv, cwd=PACKET, capture_output=True, text=True)
    commands = [{"cwd": "packet_root", "actual_cwd": str(PACKET), "argv": argv,
                 "payload_cwd": "repo", "actual_payload_cwd": str(REPO),
                 "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
                 "generator_sha256": source_hash,
                 "evidence_paths": [f"checks/audit/{TASK}/{name}" for name in
                                    ("input.json", "racket.json", "preliminary.json")]}]
    write("commands.json", commands)
    if run.returncode != 0:
        raise RuntimeError(f"Racket apply failed: {run.stderr}")
    receipt = json.loads((HERE / "racket.json").read_text())
    assert receipt["generator_sha256"] == source_hash
    assert receipt["catalog_rule_hash"] == source["catalog_rule_hash"]
    assert receipt["rule_hash_matches_catalog"] is True
    assert len(receipt["results"]) == len(authority_inputs)
    comparisons = []
    for index, (row, result) in enumerate(zip(authority_inputs, receipt["results"], strict=True)):
        assert result["input"] == row["input"]
        assert result["index"] == index
        assert result["error"] is None and result["valid_output"] is True
        rival = relative_marker_order(row["input"])
        comparisons.append({"authority_index": index, "kind": row["kind"],
                            "input_sha256": result["input_sha256"],
                            "racket_output_sha256": result["output_sha256"],
                            "new_rival_matches_racket": rival == result["output"],
                            "python_mirror_matches_racket": gen.rule_mirror(row["input"]) == result["output"]})
        if row["kind"] == "hand_constructed":
            hand_record.update({"actual_racket_output": result["output"],
                                "rival_output": rival,
                                "racket_output_sha256": result["output_sha256"],
                                "rival_output_sha256": digest(rival)})
        elif row["kind"] == "canonical":
            assert result["output"] == pairs[index]["output"]
    assert digest_bytes(GENERATOR.read_bytes()) == source_hash
    evidence = {"classification": "reproduced sampler-support shortcut; hand-input separator, not a generated wrong label",
                "source": {**source, "executed_rule_hash": receipt["executed_rule_hash"],
                           "rule_text_sha256": receipt["rule_text_sha256"]},
                "rival": "relative_marker_order: move red to cyan; stamp on bottom outside right iff original red_col < cyan_col, otherwise outside left",
                "canonical_fit": {"matches": sum(r["new_rival_matches_canonical"] for r in canonical), "denominator": len(canonical)},
                "generated_probe": {"matches_python_mirror": sum(r["new_rival_matches_python_mirror"] for r in generated),
                                    "denominator": len(generated), **preliminary["generated_selection"]},
                "override_probe": {"denominator": len(overrides), "all_axes_observed": sum(r["all_requested_axes_observed"] for r in overrides),
                                   "unique_input_count": len({r["input_sha256"] for r in overrides}),
                                   "all_rival_matches_python_mirror": all(r["new_rival_matches_python_mirror"] for r in overrides)},
                "window_probe": {"count": len(lessons), "seed": 17, "bands": bands, "cyclic_starts_inclusive": [0, 15],
                                 "raw_unique_input_count": len({h for lesson in lessons for h in lesson["input_sha256s"]}),
                                 "overlapping_input_occurrences": len(lessons) * 5,
                                 "all_named_competitors_refuted": all(not row["declared_rival_survivors"] for row in lessons),
                                 "new_rival_survives_all_demos_and_queries": all(row["new_rival_fits_every_demo_and_query"] for row in lessons)},
                "authority_verification": {"count": len(comparisons), "canonical_count": len(pairs), "generated_count": len(selected), "hand_count": 1,
                                           "comparison_rows": comparisons},
                "counterexample": hand_record,
                "proof_of_universal_generated_equivalence": [
                    "left_opposite: red_col < midpoint < cyan_col, so red_col < cyan_col is true",
                    "right_opposite: cyan_col < midpoint < red_col, so red_col < cyan_col is false",
                    "center_opposite: cyan_col < red_col = midpoint, so red_col < cyan_col is false",
                    "right_same_side: cyan_col = midpoint < red_col, so red_col < cyan_col is false",
                    "These exhaust generated scene_profile values; public overrides alter no marker-order constraint."],
                "limitations": ["Only 48 generated inputs were independently Racket-labelled here; the 1024 default and 192 override probes compare to the task Python mirror.",
                                "The hand separator cannot be emitted by the current sampler. No generated wrong label or canonical rejection is claimed.",
                                "64 windows are direct raw consecutive windows with overlapping inputs, not 64 independent production lessons."]}
    write("evidence.json", evidence)
    print(json.dumps({"source": evidence["source"], "canonical_fit": evidence["canonical_fit"],
                      "generated_probe": evidence["generated_probe"], "override_probe": evidence["override_probe"],
                      "window_probe": evidence["window_probe"], "authority_count": len(comparisons),
                      "hand_rival_matches_racket": comparisons[len(pairs)]["new_rival_matches_racket"]}, indent=2))


if __name__ == "__main__":
    main()
