from __future__ import annotations

from collections import deque
import copy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "4bc78768be8b"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def digest(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def components(grid: list[list[int]]) -> list[dict]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": sorted(cells), "size": len(cells)})
    return result


def authority_mirror(grid: list[list[int]]) -> list[list[int]]:
    objs = components(grid)
    if not objs:
        return copy.deepcopy(grid)
    minimum = min(obj["size"] for obj in objs)
    targets = [obj for obj in objs if obj["size"] == minimum]
    output = copy.deepcopy(grid)
    if len(targets) == 1:
        for r, c in targets[0]["cells"]:
            output[r][c] = 4
    return output


def color_two_rival(grid: list[list[int]]) -> list[list[int]]:
    return [[4 if value == 2 else value for value in row] for row in grid]


def cell_differences(left, right):
    return [
        {"row": r, "col": c, "left": left[r][c], "right": right[r][c]}
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def call_outcome(**kwargs):
    try:
        grid = GEN.generate(77123, 9, difficulty="medium", **kwargs)
    except Exception as exc:  # evidence, not production handling
        return {"status": "raised", "type": type(exc).__name__, "message": str(exc)}
    return {"status": "returned", "sha256": digest(grid)}


def main() -> None:
    generated = []
    rival_matches = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(20):
            seed = 410_000 + band_index * 10_000 + index
            grid = GEN.generate(seed, index, difficulty=band)
            truth = authority_mirror(grid)
            rival = color_two_rival(grid)
            objs = components(grid)
            match = truth == rival
            rival_matches += int(match)
            generated.append({
                "band": band,
                "index": index,
                "seed": seed,
                "input_sha256": digest(grid),
                "component_sizes": sorted((obj["size"], obj["color"]) for obj in objs),
                "smallest_color": min(objs, key=lambda obj: obj["size"])["color"],
                "rival_matches": match,
                "self_check": GEN.self_check(grid),
            })

    canonical = []
    canonical_rival_matches = 0
    canonical_rule_matches = 0
    first_disagreement = None
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        truth = authority_mirror(pair["input"])
        rival = color_two_rival(pair["input"])
        rule_match = truth == pair["output"]
        rival_match = rival == pair["output"]
        canonical_rule_matches += int(rule_match)
        canonical_rival_matches += int(rival_match)
        row = {
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "input_sha256": digest(pair["input"]),
            "authority_mirror_matches_label": rule_match,
            "color_two_rival_matches_label": rival_match,
            "difference_count": len(cell_differences(pair["output"], rival)),
        }
        canonical.append(row)
        if first_disagreement is None and not rival_match:
            first_disagreement = {
                **row,
                "input": pair["input"],
                "authority_output": pair["output"],
                "rival_output": rival,
                "differences": cell_differences(pair["output"], rival),
            }

    baseline = GEN.generate(77123, 9, difficulty="medium")
    controls = {
        "baseline": {"sha256": digest(baseline)},
        "palette_kind_warm": call_outcome(palette_kind="warm"),
        "palette_kind_cool": call_outcome(palette_kind="cool"),
        "anchor_corner_false": call_outcome(anchor_corner=False),
        "asymmetry_force_false": call_outcome(asymmetry_force=False),
        "texture_warm": call_outcome(texture="warm"),
        "unknown_axis": call_outcome(typo_axis="accepted?"),
    }
    baseline_sha = controls["baseline"]["sha256"]
    for value in controls.values():
        if value.get("status") == "returned" or "sha256" in value:
            value["same_as_baseline"] = value.get("sha256") == baseline_sha

    equal_sizes = GEN.generate(5, 0, texture="equal_sizes")
    equal_truth = authority_mirror(equal_sizes)
    equal_evidence = {
        "input": equal_sizes,
        "component_sizes": sorted((obj["size"], obj["color"]) for obj in components(equal_sizes)),
        "self_check": GEN.self_check(equal_sizes),
        "authority_changes_input": equal_truth != equal_sizes,
        "authority_output": equal_truth,
    }

    evidence = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(SOURCE.relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA256,
        "version": getattr(GEN, "VERSION", None),
        "rule_hash_declared": getattr(GEN, "RULE_HASH", None),
        "generated_probe": {
            "samples": len(generated),
            "rival_matches": rival_matches,
            "all_self_checks_empty": all(not row["self_check"] for row in generated),
            "rows": generated,
        },
        "canonical_probe": {
            "pairs": len(canonical),
            "authority_mirror_matches": canonical_rule_matches,
            "color_two_rival_matches": canonical_rival_matches,
            "rows": canonical,
            "first_disagreement": first_disagreement,
        },
        "override_probe": controls,
        "equal_sizes_probe": equal_evidence,
    }
    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    if first_disagreement:
        (HERE / "canonical-witness.json").write_text(
            json.dumps(first_disagreement, indent=2, sort_keys=True) + "\n"
        )
    print(json.dumps({
        "task_id": TASK_ID,
        "source_sha256": SOURCE_SHA256,
        "generated_rival_matches": f"{rival_matches}/{len(generated)}",
        "canonical_rival_matches": f"{canonical_rival_matches}/{len(canonical)}",
        "canonical_rule_matches": f"{canonical_rule_matches}/{len(canonical)}",
        "ignored_controls_same_as_baseline": {
            key: value.get("same_as_baseline")
            for key, value in controls.items() if key != "baseline"
        },
        "equal_sizes_self_check": equal_evidence["self_check"],
        "equal_sizes_component_sizes": equal_evidence["component_sizes"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
