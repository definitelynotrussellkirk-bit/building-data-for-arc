"""Source-bound geometry and demonstration-copy probe (authoring only).

Run through review.py run. This uses the selected Python mirror for bulk
measurements; Racket-backed battery/census evidence is recorded separately.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


def normalize_colors(grid):
    mapping = {0: 0}
    for row in grid:
        for color in row:
            if color not in mapping:
                mapping[color] = len(mapping)
    return tuple(tuple(mapping[color] for color in row) for row in grid)


def copy_recolor_query(demos, query):
    """A deliberately weak rival: copy a matching demo under color substitution."""
    for demo in demos:
        source = demo["input"]
        if len(source) != len(query) or len(source[0]) != len(query[0]):
            continue
        colors = {0: 0}
        consistent = True
        for row_a, row_b in zip(source, query):
            for a, b in zip(row_a, row_b):
                if colors.setdefault(a, b) != b or (a == 0) != (b == 0):
                    consistent = False
        if consistent and len(set(colors.values())) == len(colors):
            return [[colors[value] for value in row] for row in demo["output"]]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=50)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("use a new output path")
    root = find_root(__file__)
    gen, source, digest = load_selected_generator("7f03452e81df", root=root)
    report = {
        "task_id": gen.TASK_ID, "generator_sha256": digest,
        "generator_source": str(source.relative_to(root)), "rule_hash": gen.RULE_HASH,
        "label_basis": "selected Python mirror; not independent Racket evidence",
        "profile_panel": {"seeds": [0, args.seeds - 1], "sample_index": 0,
                          "difficulty": "medium", "overrides": "each declared scene_profile"},
        "profiles": {}, "copy_rival": {},
    }
    for profile in gen.SCENE_PROFILES:
        scenes, boxes, outputs, targets = set(), set(), set(), Counter()
        for seed in range(args.seeds):
            grid = gen.generate(seed, 0, difficulty="medium", scene_profile=profile)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            scenes.add(normalize_colors(grid))
            chosen = gen._chosen(gen._components(grid))
            boxes.add(tuple(chosen[key] for key in ("r1", "c1", "r2", "c2")))
            outputs.add(normalize_colors(gen.rule_mirror(grid)))
            targets[str(chosen["color"])] += 1
        report["profiles"][profile] = {
            "draws": args.seeds, "palette_normalized_inputs": len(scenes),
            "selected_bounding_boxes": len(boxes),
            "palette_normalized_outputs": len(outputs), "target_colors": dict(targets),
        }
    total, copied, matches, witness = 0, 0, 0, None
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 7, 19):
            for start in range(5):
                pairs = []
                for offset in range(gen.EXAMPLES_NEEDED + 1):
                    grid = gen.generate(seed, start + offset, difficulty=band)
                    pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
                prediction = copy_recolor_query(pairs[:-1], pairs[-1]["input"])
                copied += prediction is not None
                matches += prediction == pairs[-1]["output"]
                total += 1
                if witness is None:
                    witness = {"seed": seed, "start": start, "difficulty": band,
                               "instance": {"train": pairs[:-1], "test": pairs[-1:]},
                               "copy_prediction": prediction}
    report["copy_rival"] = {
        "seeds": [0, 1, 7, 19], "starts": [0, 1, 2, 3, 4],
        "bands": ["easy", "medium", "hard"], "demonstrations": gen.EXAMPLES_NEEDED,
        "episodes": total, "could_copy": copied, "correct_by_mirror": matches,
        "witness": witness,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(args.out), "generator_sha256": digest,
                      "profiles": report["profiles"],
                      "copy_rival": {k: v for k, v in report["copy_rival"].items() if k != "witness"}}, indent=2))


if __name__ == "__main__":
    main()
