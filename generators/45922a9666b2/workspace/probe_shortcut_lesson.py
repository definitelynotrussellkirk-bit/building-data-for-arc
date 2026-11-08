"""Retain a source-bound lesson and evaluate the generator's declared rivals.

The saved mirror outputs are hypotheses until compared with `arcpuzzles apply`.
Run this authoring tool through `review.py run`; never use it in a blind solve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=4)
    parser.add_argument("--start", type=int, default=46)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    args = parser.parse_args()
    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator("45922a9666b2", root=root)
    canonical = canonical_pairs(gen.TASK_ID, root=root, labeled_only=True)
    fits = {name: [rival(pair["input"]) == pair["output"] for pair in canonical]
            for name, rival in gen.CANONICAL_SHORTCUTS.items()}
    assert fits and all(all(matches) for matches in fits.values())
    pairs = []
    for index in range(args.start, args.start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(args.seed, index, difficulty=args.difficulty)
        assert not gen.self_check(grid)
        pairs.append({"sample_index": index, "input": grid,
                      "mirror_output": gen.rule_mirror(grid),
                      "axes": gen.observe_overrides(grid),
                      "rival_outputs": {name: rival(grid) for name, rival in gen.LESSON_COMPETITORS.items()}})
    rival_matches = {name: [p["rival_outputs"][name] == p["mirror_output"] for p in pairs]
                     for name in gen.LESSON_COMPETITORS}
    ambiguous_rotations = [{"rival": name, "query_index": query}
                           for name, matches in rival_matches.items()
                           for query in range(len(pairs))
                           if not matches[query] and all(matches[i] for i in range(len(pairs)) if i != query)]
    report = {"schema": "walker-shortcut-probe-v1", "task_id": gen.TASK_ID,
              "generator_sha256": source_sha, "generator_path": str(source),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "seed": args.seed, "start": args.start, "difficulty": args.difficulty,
              "n_train": gen.EXAMPLES_NEEDED, "n_test": 1,
              "canonical_pairs": len(canonical), "canonical_rival_fit": fits,
              "rival_matches": rival_matches, "ambiguous_rotations": ambiguous_rotations,
              "pairs": pairs, "label_status": "Python mirror; verify with canonical Racket apply"}
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "inputs.json").write_text(json.dumps([p["input"] for p in pairs]) + "\n")
    print(json.dumps({"generator_sha256": source_sha, "pairs": len(pairs),
                      "rival_matches": rival_matches, "ambiguous_rotations": ambiguous_rotations}))
    return int(bool(ambiguous_rotations))


if __name__ == "__main__":
    raise SystemExit(main())
