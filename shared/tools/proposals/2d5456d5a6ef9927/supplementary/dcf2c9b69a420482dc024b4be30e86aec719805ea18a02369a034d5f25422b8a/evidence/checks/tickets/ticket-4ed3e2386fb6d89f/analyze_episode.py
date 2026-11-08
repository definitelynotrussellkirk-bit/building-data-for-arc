from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
SOURCE = REPO / "generators/22304ccc509c/generator.py"
EPISODE = HERE / "episode.jsonl"
OUT = HERE / "probe_result.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location("allocation_target", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    g = load_generator()
    episode = json.loads(EPISODE.read_text().splitlines()[0])
    pairs = [("train", i, p) for i, p in enumerate(episode["train"])] + [
        ("test", i, p) for i, p in enumerate(episode["test"])
    ]
    details = []
    for split, index, pair in pairs:
        grid = pair["input"]
        output = pair["output"]
        details.append(
            {
                "split": split,
                "pair_index": index,
                "shape": [len(grid), len(grid[0])],
                "self_check": g.self_check(grid),
                "mirror_matches_racket": g.rule_mirror(grid) == output,
                "observed_overrides": g.observe_overrides(grid),
                "witnesses": {
                    name: bool(fn(grid)) for name, fn in g.SEMANTIC_WITNESSES.items()
                },
                "rival_disagreements": {
                    name: fn(grid) != output for name, fn in g.SEMANTIC_RIVALS.items()
                },
            }
        )

    demo_pairs = episode["train"]
    query_reasons = [g.lesson_identifiable(demo_pairs, query) for query in episode["test"]]
    hashes = [row["input_sha256"] for row in episode["sampling"]["accepted_pairs"]]
    result = {
        "schema": "arcpuzzles-allocation-ticket-probe-v1",
        "task_id": "22304ccc509c",
        "source_path": "repo/generators/22304ccc509c/generator.py",
        "source_sha256": sha256(SOURCE),
        "expected_source_sha256": "f765aa107e6e5c50a9c3d9908f3f3d57a0cce91958b6306fc230192f9e78ea05",
        "source_matches_pin": sha256(SOURCE)
        == "f765aa107e6e5c50a9c3d9908f3f3d57a0cce91958b6306fc230192f9e78ea05",
        "rule_hash": episode["executed_rule_hash"],
        "seed": episode["seed"],
        "sample_indices": episode["sample_indices"],
        "train_count": len(episode["train"]),
        "query_count": len(episode["test"]),
        "accepted_count": len(pairs),
        "rejections": episode["sampling"]["rejections"],
        "unique_input_count": len(set(hashes)),
        "all_inputs_distinct": len(hashes) == len(set(hashes)),
        "all_self_checks_clean": all(not d["self_check"] for d in details),
        "all_racket_labels_match_independent_mirror": all(
            d["mirror_matches_racket"] for d in details
        ),
        "all_queries_identifiable_from_demos": all(not r for r in query_reasons),
        "query_identifiability_reasons": query_reasons,
        "declared_rivals": sorted(g.LESSON_COMPETITORS),
        "details": details,
        "episode_lesson_check": episode.get("lesson_check"),
        "limits": [
            "One source-bound medium-band episode only.",
            "Distinctness is within this seven-grid episode, not a corpus deduplication estimate.",
            "Finite declared rivals do not establish universal identifiability or training gain.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    assert result["source_matches_pin"]
    assert result["accepted_count"] == 7
    assert result["query_count"] == 4
    assert result["all_inputs_distinct"]
    assert result["all_self_checks_clean"]
    assert result["all_racket_labels_match_independent_mirror"]
    assert result["all_queries_identifiable_from_demos"]
    print(json.dumps({k: result[k] for k in [
        "source_sha256", "rule_hash", "accepted_count", "unique_input_count",
        "all_racket_labels_match_independent_mirror", "all_queries_identifiable_from_demos"
    ]}, sort_keys=True))


if __name__ == "__main__":
    main()
