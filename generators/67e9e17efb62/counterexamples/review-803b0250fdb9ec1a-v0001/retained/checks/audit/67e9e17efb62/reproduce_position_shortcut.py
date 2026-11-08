from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "67e9e17efb62"
ROOT = find_root(__file__)
GEN_PATH = ROOT / "generators" / TASK_ID / "generator.py"
OUT = ROOT.parent / "checks" / "audit" / TASK_ID


def load_generator():
    body = GEN_PATH.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}_{digest}", GEN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    exec(compile(body, str(GEN_PATH), "exec"), module.__dict__)
    return module, digest


def rival_output(gen, grid):
    facts = gen.semantic_profile(grid)
    if facts["position_bias"] == "left":
        return gen.rule_mirror(grid)
    return gen.SEMANTIC_RIVALS["ascending_only"](grid)


def summarize(gen, seed, sample_index, difficulty):
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    facts = gen.semantic_profile(grid)
    intended = gen.rule_mirror(grid)
    rival = rival_output(gen, grid)
    return {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "facts": facts,
        "input": grid,
        "intended_output": intended,
        "rival_output": rival,
        "rival_matches": rival == intended,
        "self_check": gen.self_check(grid),
    }


def main():
    gen, digest = load_generator()
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_facts = [gen.semantic_profile(pair["input"]) for pair in canonical]
    canonical_fit = all(
        rival_output(gen, pair["input"]) == pair["output"] for pair in canonical
    )

    found = None
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(20_000):
            records = [summarize(gen, seed, index, difficulty) for index in range(4)]
            if all(record["rival_matches"] for record in records[:3]) and not records[3]["rival_matches"]:
                if all(record["facts"]["position_bias"] == "left" for record in records[:3]) and records[3]["facts"]["position_bias"] == "right":
                    found = {
                        "difficulty": difficulty,
                        "seed": seed,
                        "train": records[:3],
                        "query": records[3],
                    }
                    break
        if found:
            break
    if found is None:
        raise SystemExit("no left-demo/right-query ambiguity window found")

    payload = {
        "schema": "67e9e17efb62-position-shortcut-ambiguity-v1",
        "task_id": TASK_ID,
        "generator_sha256": digest,
        "rival_rule": (
            "Use the full rise-and-fall serialization for left-anchored bars, "
            "but emit only the ascending runs for right-anchored bars."
        ),
        "canonical_pair_count": len(canonical),
        "canonical_positions": [facts["position_bias"] for facts in canonical_facts],
        "rival_fits_all_canonical_pairs": canonical_fit,
        "lesson_schedule_probe": (
            "same seed, consecutive sample_index 0..3; first three are demonstrations, fourth is query"
        ),
        **found,
        "conclusion": (
            "The nuisance-position rival fits every canonical pair and all three demonstrations, "
            "but predicts a different answer for the right-anchored query."
        ),
        "limitations": (
            "This is a concrete consecutive-index lesson window, not a measured global ambiguity rate."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "position_shortcut_ambiguity.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "input.json").write_text(
        json.dumps(found["query"]["input"], indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "rival_output.json").write_text(
        json.dumps(found["query"]["rival_output"], indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "difficulty": found["difficulty"],
        "seed": found["seed"],
        "demo_positions": [r["facts"]["position_bias"] for r in found["train"]],
        "query_position": found["query"]["facts"]["position_bias"],
        "query_bar_len": found["query"]["facts"]["bar_len"],
        "canonical_fit": canonical_fit,
    }, indent=2))


if __name__ == "__main__":
    main()
