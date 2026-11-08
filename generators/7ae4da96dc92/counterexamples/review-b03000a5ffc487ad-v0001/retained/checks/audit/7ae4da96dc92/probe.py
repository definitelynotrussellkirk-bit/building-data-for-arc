from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

TASK_ID = "7ae4da96dc92"
WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
HERE = Path(__file__).resolve().parent

sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            result.append((color, cells))
    return result


def object_bbox_rule(grid):
    out = [[0 for _ in row] for row in grid]
    for color, cells in components(grid):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        for r in range(min(rs), max(rs) + 1):
            for c in range(min(cs), max(cs) + 1):
                out[r][c] = color
    return out


def global_color_bbox_rival(grid):
    out = [[0 for _ in row] for row in grid]
    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                by_color[color].append((r, c))
    for color, cells in by_color.items():
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        for r in range(min(rs), max(rs) + 1):
            for c in range(min(cs), max(cs) + 1):
                out[r][c] = color
    return out


def canonical_pairs():
    pairs = []
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            train = row.get("train") or []
            test = row.get("test") or []
            if isinstance(train, dict):
                train = [train]
            if isinstance(test, dict):
                test = [test]
            pairs.extend(train)
            pairs.extend(test)
    return pairs


def sha256_json(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main():
    module = load_generator()
    racket = json.loads((HERE / "racket.json").read_text(encoding="utf-8"))
    counterexample = racket["results"][0]["input"]
    authoritative = racket["results"][0]["output"]
    rival = global_color_bbox_rival(counterexample)
    mirror = object_bbox_rule(counterexample)

    canonical = canonical_pairs()
    canonical_rows = []
    for index, pair in enumerate(canonical):
        intended = object_bbox_rule(pair["input"])
        shortcut = global_color_bbox_rival(pair["input"])
        canonical_rows.append({
            "index": index,
            "label_matches_object_bbox": intended == pair["output"],
            "shortcut_fits_label": shortcut == pair["output"],
            "self_check": module.self_check(copy.deepcopy(pair["input"])),
            "same_color_multiple_components": any(
                sum(1 for color2, _ in components(pair["input"]) if color2 == color) > 1
                for color in {color for color, _ in components(pair["input"])}
            ),
        })

    sample_rows = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(100):
            seed = 910000 + band_index * 1000 + index
            grid = module.generate(seed, index, difficulty=band)
            comps = components(grid)
            counts = defaultdict(int)
            for color, _ in comps:
                counts[color] += 1
            sample_rows.append({
                "band": band,
                "seed": seed,
                "sample_index": index,
                "self_check": module.self_check(copy.deepcopy(grid)),
                "shortcut_equals_object_bbox": global_color_bbox_rival(grid) == object_bbox_rule(grid),
                "same_color_multiple_components": any(value > 1 for value in counts.values()),
                "input_sha256": sha256_json(grid),
            })

    differences = []
    for r, (want_row, rival_row) in enumerate(zip(authoritative, rival)):
        for c, (want, got) in enumerate(zip(want_row, rival_row)):
            if want != got:
                differences.append({"row": r, "col": c, "intended": want, "rival": got})

    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "finding": "validator rejects a canonical repeated-color case and production draws never distinguish object bboxes from per-color bboxes",
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "executed_rule_hash": racket["executed_rule_hash"],
        "counterexample": {
            "input_path": "checks/audit/7ae4da96dc92/input.json",
            "racket_path": "checks/audit/7ae4da96dc92/racket.json",
            "input": counterexample,
            "intended_output": authoritative,
            "object_bbox_mirror_matches_racket": mirror == authoritative,
            "rival_output": rival,
            "difference_count": len(differences),
            "differences": differences,
            "self_check": module.self_check(copy.deepcopy(counterexample)),
            "belongs_to_documented_generator_domain": False,
            "domain_reason": "same nonzero color is used by two disconnected objects, which self_check rejects",
        },
        "canonical": {
            "pairs": len(canonical_rows),
            "self_check_accepted": sum(not row["self_check"] for row in canonical_rows),
            "shortcut_fits": sum(row["shortcut_fits_label"] for row in canonical_rows),
            "rows": canonical_rows,
        },
        "generated_census": {
            "draws": len(sample_rows),
            "bands": ["easy", "medium", "hard"],
            "per_band": 100,
            "seed_formula": "910000 + band_index*1000 + sample_index",
            "self_check_clean": sum(not row["self_check"] for row in sample_rows),
            "shortcut_equal": sum(row["shortcut_equals_object_bbox"] for row in sample_rows),
            "same_color_multiple_components": sum(row["same_color_multiple_components"] for row in sample_rows),
            "unique_inputs": len({row["input_sha256"] for row in sample_rows}),
        },
        "conclusion": (
            "The third canonical pair contains three disconnected objects of color 3 and is rejected by the "
            "selected validator. The selected source otherwise enforces one distinct color per object, so filling "
            "each color's single global bounding box is observationally identical to filling each connected "
            "object's bounding box on every sampled production draw. The authority disagrees with that shortcut "
            "on repeated-color objects, but the sampler excludes every such witness."
        ),
    }
    (HERE / "probe-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    rejected = next(
        (pair for pair, row in zip(canonical, canonical_rows) if row["self_check"]),
        None,
    )
    if rejected is not None:
        (HERE / "canonical-rejected.json").write_text(json.dumps({
            "schema": "arcpuzzles-audit-canonical-rejection-v1",
            "task_id": TASK_ID,
            "generator_sha256": report["generator_sha256"],
            "canonical_pair_index": next(i for i, row in enumerate(canonical_rows) if row["self_check"]),
            "input": rejected["input"],
            "expected_output": rejected["output"],
            "validator_findings": next(row["self_check"] for row in canonical_rows if row["self_check"]),
            "global_color_bbox_rival_output": global_color_bbox_rival(rejected["input"]),
        }, indent=2) + "\n", encoding="utf-8")

    (HERE / "rival.json").write_text(json.dumps({
        "schema": "arcpuzzles-audit-rival-v1",
        "task_id": TASK_ID,
        "generator_sha256": report["generator_sha256"],
        "executed_rule_hash": report["executed_rule_hash"],
        "input": counterexample,
        "actual_racket_output": authoritative,
        "rival_name": "fill one global bbox per color",
        "rival_output": rival,
        "differences": differences,
        "validator_findings": report["counterexample"]["self_check"],
        "belongs_to_documented_generator_domain": False,
        "command": "python3 review.py run python3 ../checks/audit/7ae4da96dc92/probe.py",
        "cwd": str(REPO),
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "canonical_validator_acceptance": f"{report['canonical']['self_check_accepted']}/{report['canonical']['pairs']}",
        "canonical_shortcut_fit": f"{report['canonical']['shortcut_fits']}/{report['canonical']['pairs']}",
        "generated_shortcut_equal": f"{report['generated_census']['shortcut_equal']}/{report['generated_census']['draws']}",
        "counterexample_differences": len(differences),
        "self_check": report["counterexample"]["self_check"],
    }, indent=2))


if __name__ == "__main__":
    main()
