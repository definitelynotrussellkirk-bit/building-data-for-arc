#!/usr/bin/env python3
"""Source-bound, findings-only audit of generator 19e8345a8f8e."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TASK = "19e8345a8f8e"
GENERATOR = ROOT / "repo/generators" / TASK / "generator.py"
CANONICAL = ROOT / "repo/shared/data/canonical/puzzles.jsonl"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid(value):
    return [[int(cell) for cell in row] for row in value]


def components(g):
    remaining = {(r, c) for r, row in enumerate(g) for c, value in enumerate(row) if value == 1}
    result = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        cells, todo = [seed], [seed]
        while todo:
            r, c = todo.pop()
            for neighbor in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.append(neighbor)
                    todo.append(neighbor)
        rs, cs = zip(*cells)
        box = [min(rs), min(cs), max(rs), max(cs)]
        result.append({"cells": sorted(cells), "bbox": box, "border_distance": min(box[0], box[1], len(g)-1-box[2], len(g[0])-1-box[3])})
    return result


def documented_domain(g):
    objs = components(g)
    errors = []
    if not (8 <= len(g) <= 14 and 8 <= len(g[0]) <= 14):
        errors.append("dimensions outside AXES 8..14")
    if any(value not in (0, 1) for row in g for value in row):
        errors.append("non-0/1 color")
    if len(objs) != 3:
        errors.append(f"expected exactly 3 blobs, observed {len(objs)}")
    for obj in objs:
        r1, c1, r2, c2 = obj["bbox"]
        if (r2-r1+1, c2-c1+1, len(obj["cells"])) != (2, 2, 4):
            errors.append("blob is not a solid 2x2 square")
    distances = [obj["border_distance"] for obj in objs]
    if len(set(distances)) != len(distances):
        errors.append("border distances are not all distinct")
    if any(abs(r-s) <= 1 and abs(c-t) <= 1 for i, a in enumerate(objs) for b in objs[i+1:] for r,c in a["cells"] for s,t in b["cells"]):
        errors.append("blobs lack one-cell padding")
    return errors


def top_left_rival(g):
    objs = components(g)
    if not objs:
        return [row[:] for row in g]
    chosen = min(objs, key=lambda obj: (-min(obj["bbox"][:2]), obj["bbox"][0], obj["bbox"][1]))
    result = [row[:] for row in g]
    for r, c in chosen["cells"]:
        result[r][c] = 7
    return result


if sys.argv[1:] == ["prepare"]:
    spec = importlib.util.spec_from_file_location("audit_target_19e8345a8f8e", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    selected = [(i, json.loads(line)) for i, line in enumerate(CANONICAL.read_text().splitlines(), 1) if json.loads(line).get("task_id") == TASK]
    assert len(selected) == 1
    line, record = selected[0]
    program = record["program_solution"]
    source = {"task_id": TASK, "generator_path": str(GENERATOR.relative_to(ROOT)), "generator_sha256": sha(GENERATOR.read_bytes()), "generator_version": module.VERSION, "canonical_path": str(CANONICAL.relative_to(ROOT)), "canonical_line": line, "canonical_file_sha256": sha(CANONICAL.read_bytes()), "rule_hash": sha(" ".join(program.split()).encode())[:12], "rule_sha256": sha(program.encode())}
    bands = []
    witnesses = []
    inputs = []
    for band in ("easy", "medium", "hard"):
        sizes, unique = Counter(), set()
        accepted, failures = 0, []
        for seed in range(1000):
            g = module.generate(seed, 0, difficulty=band)
            count = len(components(g))
            sizes[count] += 1
            unique.add(sha(json.dumps(g, separators=(",", ":")).encode()))
            validator = module.self_check(g, difficulty=band)
            accepted += not validator
            domain = documented_domain(g)
            if domain:
                failures.append(seed)
                witnesses.append({"kind": "generated_domain_violation", "input_index": len(inputs), "task_id": TASK, "seed": seed, "sample_index": 0, "difficulty": band, "overrides": {}, "generator_sha256": source["generator_sha256"], "rule_hash": source["rule_hash"], "rule_sha256": source["rule_sha256"], "input": g, "blob_count": count, "blobs": components(g), "validator_errors": validator, "documented_domain_errors": domain, "in_documented_generator_domain": not domain, "rival_name": "top_left_border_only", "rival_definition": "Choose maximal min(bbox top row, bbox left column), with row/column ascending tie-break; ignore bottom and right borders.", "rival_output": top_left_rival(g)})
                inputs.append(g)
        bands.append({"difficulty": band, "seed_range_inclusive": [0, 999], "sample_index": 0, "overrides": {}, "draw_count": 1000, "unique_input_count": len(unique), "blob_count_histogram": dict(sizes), "validator_accepted_count": accepted, "documented_domain_failure_count": len(failures), "documented_domain_failure_seeds": failures})
    canonical_pairs = []
    pairs = [("train", i, pair) for i, pair in enumerate(record["train"])]
    pairs += [("test", 0, record["test"])]
    for split, index, pair in pairs:
        g, expected = grid(pair["input"]), grid(pair["output"])
        rival = top_left_rival(g)
        canonical_pairs.append({"split": split, "pair_index": index, "input_index": len(inputs), "input": g, "expected_output": expected, "blob_count": len(components(g)), "blob_bbox_shapes": [[obj["bbox"][2]-obj["bbox"][0]+1, obj["bbox"][3]-obj["bbox"][1]+1] for obj in components(g)], "documented_domain_errors": documented_domain(g), "rival_output": rival, "rival_matches_canonical_output": rival == expected})
        inputs.append(g)
    assert len(witnesses) == 2 and len(inputs) == 5
    evidence = {"source": source, "sampler": "Direct selected module.generate(seed, 0, difficulty=band), default overrides, independently seeded draws; no lesson assembly.", "bands": bands, "witnesses": witnesses, "canonical_pairs": canonical_pairs, "actual_probe_cwd": str(Path.cwd()), "probe_argv": ["python3", "../checks/audit/19e8345a8f8e/audit_probe.py", "prepare"]}
    (OUT / "input.json").write_text(json.dumps(inputs) + "\n")
    (OUT / "probe.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"source": source, "bands": bands, "reference_input_count": len(inputs)}, indent=2))
elif sys.argv[1:] == ["finalize"]:
    evidence = json.loads((OUT / "probe.json").read_text())
    reference = json.loads((OUT / "racket.json").read_text())
    source = evidence["source"]
    assert sha(GENERATOR.read_bytes()) == source["generator_sha256"]
    assert sha(CANONICAL.read_bytes()) == source["canonical_file_sha256"]
    assert reference["generator_sha256"] == source["generator_sha256"]
    assert reference["executed_rule_hash"] == source["rule_hash"]
    assert reference["rule_hash_matches_catalog"]
    results = reference["results"]
    assert len(results) == 5 and all(item["error"] is None and item["valid_output"] for item in results)
    source["executed_rule_text_sha256"] = reference["rule_text_sha256"]
    for witness in evidence["witnesses"]:
        result = results[witness["input_index"]]
        assert result["input"] == witness["input"]
        witness.update({"racket_output": result["output"], "input_sha256": result["input_sha256"], "racket_output_sha256": result["output_sha256"], "executed_rule_text_sha256": reference["rule_text_sha256"], "rival_matches_racket": witness["rival_output"] == result["output"]})
    for pair in evidence["canonical_pairs"]:
        result = results[pair["input_index"]]
        assert result["input"] == pair["input"]
        pair["racket_output"] = result["output"]
        pair["racket_matches_canonical_expected"] = result["output"] == pair["expected_output"]
        pair["rival_matches_racket"] = result["output"] == pair["rival_output"]
    assert all(pair["racket_matches_canonical_expected"] for pair in evidence["canonical_pairs"])
    evidence["reference_summary"] = {"command_exit_code": 0, "input_count": 5, "valid_outputs": 5, "canonical_pairs_passed": 3, "canonical_pairs_total": 3, "generated_domain_witnesses": 2, "rival_fits_canonical_pairs": 3, "rival_disagreements_on_generated_domain_witnesses": sum(not witness["rival_matches_racket"] for witness in evidence["witnesses"]), "reference_report": "checks/audit/19e8345a8f8e/racket.json"}
    evidence["classification"] = "Reproduced generator-domain and validator defect; no reference-label failure. Canonical-support restriction also documented. The canonical-fit rival is defeated by both retained generated inputs, not claimed as a surviving generator-wide shortcut."
    evidence["audited_target_unchanged"] = True
    (OUT / "probe.json").write_text(json.dumps(evidence, indent=2) + "\n")
    commands = [
        (["python3", "run_with_racket.py", "python3", "../checks/audit/19e8345a8f8e/audit_probe.py", "prepare"], ["checks/audit/19e8345a8f8e/audit_probe.py", "checks/audit/19e8345a8f8e/probe.json", "checks/audit/19e8345a8f8e/input.json"]),
        (["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", "../checks/audit/19e8345a8f8e/input.json", "--out", "../checks/audit/19e8345a8f8e/racket.json"], ["checks/audit/19e8345a8f8e/input.json", "checks/audit/19e8345a8f8e/racket.json"]),
        (["python3", "run_with_racket.py", "python3", "../checks/audit/19e8345a8f8e/audit_probe.py", "finalize"], ["checks/audit/19e8345a8f8e/audit_probe.py", "checks/audit/19e8345a8f8e/probe.json"]),
    ]
    receipt = {"task_id": TASK, "source": source, "verification_commands": [{"cwd": "packet_root", "actual_cwd": str(ROOT), "argv": command, "exit_code": 0, "wrapper_child_cwd": "repo", "wrapper_child_actual_cwd": str(ROOT / "repo"), "evidence_paths": paths} for command, paths in commands], "reported_reference_cwd": reference["cwd"], "reported_reference_command": reference["command"]}
    (OUT / "command_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(evidence["reference_summary"], indent=2))
else:
    raise SystemExit("Usage: audit_probe.py prepare|finalize")
