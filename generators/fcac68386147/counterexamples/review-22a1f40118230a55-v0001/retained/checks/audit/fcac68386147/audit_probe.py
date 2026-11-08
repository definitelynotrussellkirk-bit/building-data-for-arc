"""Findings-only audit. Run from packet root; all retained output stays here.

python3 run_with_racket.py python3 ../checks/audit/fcac68386147/audit_probe.py collect
python3 run_with_racket.py python3 -m arcpuzzles apply fcac68386147 --input ../checks/audit/fcac68386147/input.json --out ../checks/audit/fcac68386147/racket.json
python3 run_with_racket.py python3 ../checks/audit/fcac68386147/audit_probe.py verify

Uses only public Catalog generation / CLI apply for Racket labels.
The two rivals are auditor-defined, not claimed generator declarations.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

TID = "fcac68386147"
OUT = Path(__file__).resolve().parent
PACKET = next(path for path in OUT.parents if (path / "run_with_racket.py").is_file())
REPO = PACKET / "repo"
GEN = REPO / "generators" / TID / "generator.py"
EXPECTED_SHA = "e3cb70cda6c756fd3124cc0211641e83381f144ccc3245db06653f775236c005"
BANDS = ("easy", "medium", "hard")
BASE_SEED = 73000
LESSONS = 32


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def write(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2) + "\n")


def load_generator():
    assert sha(GEN.read_bytes()) == EXPECTED_SHA
    spec = importlib.util.spec_from_file_location("audit_target", GEN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repeat_tile(grid):
    n = len(grid)
    return [row * n for _ in range(n) for row in grid]


def collapse_foreground_to_mode(grid):
    counts = Counter(value for row in grid for value in row if value)
    color = min(counts, key=lambda value: (-counts[value], value))
    binary = [[color if value else 0 for value in row] for row in grid]
    return repeat_tile(binary)


def crop_background_border(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    top, bottom = min(r for r, _ in points), max(r for r, _ in points)
    left, right = min(c for _, c in points), max(c for _, c in points)
    crop = [row[left:right + 1] for row in grid[top:bottom + 1]]
    n = len(grid)
    return [[crop[r % len(crop)][c % len(crop[0])] for c in range(n*n)] for r in range(n*n)]


RIVALS = {
    "collapse_foreground_to_mode": collapse_foreground_to_mode,
    "crop_background_border": crop_background_border,
}


def lawful(grid):
    n = len(grid)
    palette = {value for row in grid for value in row if value}
    nonzero = sum(value != 0 for row in grid for value in row)
    return (2 <= n <= 5 and all(len(row) == n for row in grid)
            and all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
            and 1 <= len(palette) <= 3 and nonzero < n*n
            and (35*n*n + 99)//100 <= nonzero <= (75*n*n)//100)


def collect():
    from arcpuzzles import Catalog
    from reviewer_support import canonical_pairs, canonical_path, find_root
    generator = load_generator()
    root = find_root(GEN)
    pairs = canonical_pairs(TID, root=root, variant=0)
    selected = []
    for line_number, raw in enumerate(canonical_path(root).read_bytes().splitlines(keepends=True), 1):
        row = json.loads(raw)
        if row.get("task_id") == TID:
            selected.append((line_number, raw, row))
    assert len(selected) == 1
    line_number, raw, row = selected[0]
    rule_sha = sha(" ".join(row["program_solution"].split()).encode())
    assert generator.RULE_HASH == rule_sha[:12]
    source = {"task_id": TID, "generator_version": generator.VERSION,
              "generator_sha256": EXPECTED_SHA, "rule_hash": rule_sha[:12],
              "normalized_rule_sha256": rule_sha, "rule_text_sha256": sha(row["program_solution"].encode()),
              "canonical_row_line": line_number, "canonical_row_sha256_with_newline": sha(raw),
              "canonical_variant": 0, "canonical_pair_count": len(pairs),
              "canonical_ledger": "repo/shared/data/canonical/puzzles.jsonl"}
    canonical_fits = {}
    for name, rival in RIVALS.items():
        canonical_fits[name] = sum(rival(pair["input"]) == pair["output"] for pair in pairs)
    assert all(value == len(pairs) for value in canonical_fits.values())
    for pair in pairs:
        assert lawful(pair["input"]) and generator.self_check(pair["input"]) == []
        assert repeat_tile(pair["input"]) == pair["output"] == generator.rule_mirror(pair["input"])
    declared = {name: list(getattr(generator, name, ())) for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")}
    assert all(not value for value in declared.values()), "Update probe to iterate newly added declared rivals"
    catalog = Catalog()
    bands = {}
    witness = {}
    all_keys = set()
    episodes_path = OUT / "episodes.jsonl"
    with episodes_path.open("w") as handle:
        for band in BANDS:
            episodes = catalog.generate(TID, count=LESSONS, seed=BASE_SEED,
                difficulty=band, n_train=3, n_test=1, sample_index=0,
                overrides={}, allow_unapproved=True, timeout=300)
            unique = set()
            palette_counts, side_counts = Counter(), Counter()
            ambiguity = Counter()
            accepted, rejected = 0, 0
            index_sets = set()
            for episode in episodes:
                assert episode["provenance"]["generator_sha256"] == EXPECTED_SHA
                assert episode["executed_rule_hash"] == generator.RULE_HASH
                handle.write(json.dumps({"band": band, "episode": episode}, separators=(",", ":")) + "\n")
                episode_pairs = episode["train"] + episode["test"]
                index_sets.add(tuple(episode["sample_indices"]))
                rejected += len(episode["rejections"])
                for index, pair in zip(episode["sample_indices"], episode_pairs, strict=True):
                    grid = pair["input"]
                    before = deepcopy(grid)
                    assert lawful(grid) and generator.self_check(grid, difficulty=band) == []
                    assert generator.rule_mirror(grid) == repeat_tile(grid) == pair["output"]
                    assert grid == before
                    assert generator.generate(episode["seed"], index, difficulty=band) == grid
                    observed = generator.observe_overrides(grid)
                    palette_size = len({value for row in grid for value in row if value})
                    assert observed == {"side": len(grid), "palette_size": palette_size}
                    palette_counts[palette_size] += 1
                    side_counts[len(grid)] += 1
                    unique.add(grid_key(grid))
                    accepted += 1
                for name, rival in RIVALS.items():
                    fits = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
                    wrong = rival(episode["test"][0]["input"]) != episode["test"][0]["output"]
                    if fits and wrong:
                        ambiguity[name] += 1
                        witness.setdefault(name, {"band": band, "episode": episode})
            all_keys.update(unique)
            bands[band] = {"episodes": len(episodes), "accepted_inputs": accepted,
                           "rejected_draws": rejected, "unique_inputs": len(unique),
                           "seeds_inclusive": [BASE_SEED, BASE_SEED + LESSONS - 1],
                           "accepted_sample_index_sequences": sorted(index_sets),
                           "overrides": {}, "side_counts": dict(side_counts),
                           "palette_size_counts": dict(palette_counts),
                           "ambiguous_lessons": {name: ambiguity[name] for name in RIVALS}}
            print(json.dumps({"completed_band": band, **bands[band]}), flush=True)
    random.seed(12937)
    expected_rng = [random.random() for _ in range(10)]
    random.seed(12937)
    generator.generate(42, 17, difficulty="hard")
    assert [random.random() for _ in range(10)] == expected_rng
    grid = generator.generate(42, 17, difficulty="hard")
    saved = deepcopy(grid)
    grid[0][0] = (grid[0][0] + 1) % 10
    assert generator.generate(42, 17, difficulty="hard") == saved

    authority = []
    for pair in pairs:
        authority.append({"kind": "canonical", "split": pair["split"], "pair_index": pair["pair_index"],
                          "input": pair["input"], "expected": pair["output"],
                          "self_check": [], "documented_domain": True})
    for band in BANDS:
        for side in range(2, 6):
            for palette_size in range(1, 4):
                seed, index = 84000 + side*10 + palette_size, 900 + side*3 + palette_size
                overrides = {"side": side, "palette_size": palette_size}
                grid = generator.generate(seed, index, difficulty=band, **overrides)
                assert lawful(grid) and generator.self_check(grid) == []
                assert generator.observe_overrides(grid) == overrides
                authority.append({"kind": "override", "difficulty": band, "seed": seed,
                    "sample_index": index, "overrides": overrides, "input": grid,
                    "expected": repeat_tile(grid), "self_check": [], "documented_domain": True})
    for name, record in witness.items():
        episode = record["episode"]
        record["authority_input_indices"] = []
        for position, (sample_index, pair) in enumerate(zip(episode["sample_indices"], episode["train"] + episode["test"], strict=True)):
            record["authority_input_indices"].append(len(authority))
            authority.append({"kind": "rival_witness", "rival": name, "difficulty": record["band"],
                "seed": episode["seed"], "sample_index": sample_index, "overrides": {},
                "role": "train" if position < 3 else "query", "input": pair["input"],
                "expected": pair["output"], "rival_output": RIVALS[name](pair["input"]),
                "self_check": [], "documented_domain": True})
    assert len(authority) <= 64
    write("input.json", [record["input"] for record in authority])
    write("authority_cases.json", authority)
    write("witnesses.json", witness)
    summary = {"phase": "final_unchanged_audit_source", "source": source,
        "declared_rivals": declared, "auditor_rivals_canonical_fits": canonical_fits,
        "generation_api": {"method": "Catalog.generate", "task_id": TID,
            "count": LESSONS, "seed": BASE_SEED, "difficulty": list(BANDS), "n_train": 3,
            "n_test": 1, "sample_index": 0, "overrides": {}, "allow_unapproved": True, "timeout": 300},
        "bands": bands, "overall_unique_inputs": len(all_keys),
        "accepted_input_count": sum(band["accepted_inputs"] for band in bands.values()),
        "mirror_racket_mismatches": 0, "self_check_failures": 0,
        "documented_domain_failures": 0, "determinism_failures": 0,
        "global_rng_preserved": True, "fresh_returns": True,
        "authority_case_count": len(authority), "override_case_count": 36,
        "episodes_sha256": sha(episodes_path.read_bytes()),
        "lesson_policy": "Public production assembly: three first accepted pairs train, next accepted pair query; no windows overlap.",
        "rival_scope": "Both auditor-defined rivals fit all seven canonical pairs; declarations are absent. Counts cover only production 3-train/1-query lessons, not rotations or all possible rivals."}
    write("summary.json", summary)
    print(json.dumps({"summary": "summary.json", "witnesses": list(witness), "authority_cases": len(authority)}), flush=True)


def verify():
    load_generator()
    summary = json.loads((OUT / "summary.json").read_text())
    authority = json.loads((OUT / "authority_cases.json").read_text())
    actual = json.loads((OUT / "racket.json").read_text())
    assert actual["generator_sha256"] == EXPECTED_SHA
    assert actual["executed_rule_hash"] == summary["source"]["rule_hash"]
    assert len(actual["results"]) == len(authority)
    failures, counterexamples = [], []
    for index, (record, result) in enumerate(zip(authority, actual["results"], strict=True)):
        if result["input"] != record["input"] or result["output"] != record["expected"]:
            failures.append(index)
        if record["kind"] == "rival_witness":
            counterexamples.append({"authority_input_index": index, **summary["source"],
                **record, "actual_racket_output": result["output"],
                "matches_rival": result["output"] == record["rival_output"],
                "authority_command": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TID,
                    "--input", "../checks/audit/fcac68386147/input.json", "--out", "../checks/audit/fcac68386147/racket.json"],
                "command_cwd": "packet_root", "effective_cwd": "repo"})
    write("counterexamples.json", counterexamples)
    summary["public_apply_checked"] = len(authority)
    summary["public_apply_mismatch_indices"] = failures
    summary["public_apply_rule_hash"] = actual["executed_rule_hash"]
    write("summary.json", summary)
    print(json.dumps({"public_apply_checked": len(authority), "mismatches": failures,
                      "counterexample_pairs": len(counterexamples)}), flush=True)
    assert not failures


if __name__ == "__main__":
    {"collect": collect, "verify": verify}[sys.argv[1]]()
