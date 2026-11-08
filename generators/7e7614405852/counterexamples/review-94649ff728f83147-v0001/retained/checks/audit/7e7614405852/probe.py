"""Source-bound audit: orientation is confounded with side-border position.

Run through packet review.py; this script never supplies authoritative labels.
prepare writes inputs; compare consumes labels from the supported apply command.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "7e7614405852"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rival(grid):
    """Mark exact triples in either orientation if center is not on a side edge."""
    result = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for dr, dc in ((0, 1), (1, 0)):
        for row in range(height):
            for col in range(width):
                color = grid[row][col]
                if not color:
                    continue
                prev_row, prev_col = row - dr, col - dc
                if (0 <= prev_row < height and 0 <= prev_col < width
                        and grid[prev_row][prev_col] == color):
                    continue
                length = 0
                rr, cc = row, col
                while 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == color:
                    length += 1
                    rr, cc = rr + dr, cc + dc
                center_row, center_col = row + dr, col + dc
                if length == 3 and 0 < center_col < width - 1:
                    result[center_row][center_col] = 8
    return result


def main(mode):
    module, source, source_hash = load_selected_generator(TASK, root=ROOT)
    if mode == "prepare":
        record = Catalog(ROOT).get(TASK)
        canonical = canonical_pairs(TASK, root=ROOT)
        dump("canonical_record.json", {
            "task_id": TASK,
            "generator_sha256": record["generator_sha256"],
            "rule_hash": record["rule_hash"],
            "variants": record["variants"],
            "normalized_pairs": canonical,
        })
        rule_text = record["variants"][0]["program_solution"]
        fixtures = []
        for pair in canonical:
            fixtures.append({
                "role": "canonical",
                "variant": pair["variant"], "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input": pair["input"], "canonical_output": pair["output"],
            })
        for sample_index in range(3):
            grid = module.generate(seed=17, sample_index=sample_index)
            fixtures.append({
                "role": "ordinary_demo", "seed": 17,
                "sample_index": sample_index, "difficulty": None,
                "overrides": {}, "input": grid,
            })
        query = [
            [1, 1, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 2, 0],
            [0, 0, 0, 0, 0, 0, 2, 0],
            [0, 0, 0, 0, 0, 0, 2, 0],
            [3, 3, 3, 3, 3, 0, 0, 0],
        ]
        fixtures.append({
            "role": "interior_vertical_query", "seed": None,
            "sample_index": None, "difficulty": None, "overrides": None,
            "construction": "Hand-made 5x8 grid: one horizontal triple, one length-five run, and an interior vertical triple centered at zero-based (2,6).",
            "input": query,
        })
        for fixture in fixtures:
            fixture["self_check_errors"] = module.self_check(fixture["input"])
            fixture["strict_canonical_like_errors"] = module.strict_canonical_like(fixture["input"])
            fixture["observed_axes"] = module.observe_overrides(fixture["input"])
        inputs = {"inputs": [fixture["input"] for fixture in fixtures]}
        dump("input.json", inputs)
        dump("fixtures.json", fixtures)
        binding_paths = [
            source,
            ROOT / "generators" / TASK / "notes.md",
            ROOT / "generators" / TASK / "evidence/review_index.json",
            ROOT / "shared/runtime/reviewer_support.py",
            ROOT / "shared/runtime/puzzle_generators/base.py",
        ]
        bindings = {
            "task_id": TASK,
            "generator_source_sha256": source_hash,
            "declared_rule_hash": module.RULE_HASH,
            "catalog_rule_hash": record["rule_hash"],
            "exact_program_solution_sha256": hashlib.sha256(rule_text.encode()).hexdigest(),
            "normalized_program_solution_sha256": hashlib.sha256(" ".join(rule_text.split()).encode()).hexdigest(),
            "canonical_record_sha256": digest(HERE / "canonical_record.json"),
            "input_sha256": digest(HERE / "input.json"),
            "probe_sha256": digest(Path(__file__)),
            "source_files": {
                str(path.relative_to(ROOT)): digest(path) for path in binding_paths
            },
        }
        dump("bindings.json", bindings)
        print(json.dumps({"fixtures": len(fixtures), "canonical_pairs": len(canonical), "source_sha256": source_hash, "rule_hash": record["rule_hash"], "canonical_variants": record["variants"]}, indent=2))
    elif mode == "compare":
        bindings = json.loads((HERE / "bindings.json").read_text())
        assert source_hash == bindings["generator_source_sha256"]
        assert digest(Path(__file__)) == bindings["probe_sha256"]
        fixtures = json.loads((HERE / "fixtures.json").read_text())
        actual = json.loads((HERE / "racket.json").read_text())
        results = actual["results"]
        assert len(fixtures) == len(results)
        rows, demos = [], []
        for index, (fixture, result) in enumerate(zip(fixtures, results)):
            assert result["error"] is None, result
            inp, output = fixture["input"], result["output"]
            assert result["input"] == inp
            rival_output = rival(inp)
            difference = [
                {"row": r, "col": c, "input": inp[r][c],
                 "racket": output[r][c], "rival": rival_output[r][c]}
                for r in range(len(inp)) for c in range(len(inp[0]))
                if output[r][c] != rival_output[r][c]
            ]
            rows.append({
                **fixture, "apply_result_index": index,
                "racket_output": output, "rival_output": rival_output,
                "rival_matches_racket": not difference, "differences": difference,
                "racket_matches_retained_canonical": (
                    output == fixture["canonical_output"] if "canonical_output" in fixture else None),
            })
            if fixture["role"] == "ordinary_demo":
                demos.append({"input": inp, "output": output})
            if fixture["role"] == "interior_vertical_query":
                query = {"input": inp, "output": output}
                query_result = rows[-1]
        hook = module.lesson_identifiable(demos, query)
        report = {
            "schema": "task-local-adversarial-teaching-probe-v1",
            "task_id": TASK,
            "source_bindings": bindings,
            "racket_receipt_sha256": digest(HERE / "racket.json"),
            "rival": "Mark the center of every maximal nonzero monochromatic run of exactly three cells, in either orientation, if its center is not in the first or last column.",
            "scope": "Three ordinary generated demonstrations, all retained canonical pairs, one hand-made validator-accepted interior query. No full battery or universal semantic claim.",
            "ordinary_demo_count": len(demos),
            "all_ordinary_demos_match_rival": all(row["rival_matches_racket"] for row in rows if row["role"] == "ordinary_demo"),
            "all_canonical_pairs_match_rival": all(row["rival_matches_racket"] for row in rows if row["role"] == "canonical"),
            "all_canonical_outputs_reproduced": all(row["racket_matches_retained_canonical"] for row in rows if row["role"] == "canonical"),
            "query_self_check_errors": query_result["self_check_errors"],
            "query_strict_canonical_like_errors": query_result["strict_canonical_like_errors"],
            "query_difference": query_result["differences"],
            "lesson_identifiable_errors": hook,
            "declared_rival_refuted_by_demos": {
                name: any(competitor(deepcopy(pair["input"])) != pair["output"] for pair in demos)
                for name, competitor in module.LESSON_COMPETITORS.items()
            },
            "rows": rows,
        }
        assert report["all_ordinary_demos_match_rival"]
        assert report["all_canonical_pairs_match_rival"]
        assert report["all_canonical_outputs_reproduced"]
        assert not report["query_self_check_errors"]
        assert not report["query_strict_canonical_like_errors"]
        assert not hook
        assert report["query_difference"] == [{"row": 2, "col": 6, "input": 2, "racket": 2, "rival": 8}]
        assert all(report["declared_rival_refuted_by_demos"].values())
        dump("probe_report.json", report)
        print(json.dumps({key: value for key, value in report.items() if key not in {"rows", "source_bindings"}}, indent=2))
    else:
        raise SystemExit("Usage: probe.py prepare|compare")


if __name__ == "__main__":
    main(sys.argv[1])
