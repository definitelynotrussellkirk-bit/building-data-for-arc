"""Bounded self-audit for the marker target-policy parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("_marker_probe_adapter", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    adapter = _adapter()
    prototype = adapter._impl
    rows = []
    teaching_certificates = []
    farthest_origins = set()
    for seed in (0, 17, 43):
        episodes = {
            policy: adapter.generate(seed, {"target_policy": policy}, 2, 4)
            for policy in ("all_matches", "farthest_match")
        }
        all_episode = episodes["all_matches"]
        far_episode = episodes["farthest_match"]
        all_inputs = [pair["input"] for pair in all_episode["train"] + all_episode["test"]]
        far_inputs = [pair["input"] for pair in far_episode["train"] + far_episode["test"]]
        if all_inputs != far_inputs:
            raise AssertionError("hidden setting changed sampled inputs")
        if len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs}) != 6:
            raise AssertionError("episode contains duplicate inputs")
        for policy, episode in episodes.items():
            prefix = adapter.generate(seed, {"target_policy": policy}, 2, 1)
            if prefix["train"] != episode["train"] or prefix["test"][0] != episode["test"][0]:
                raise AssertionError("one-query request changed first-turn content")
            certificate = prototype.teaching_certificate(
                episode["train"], {"target_policy": policy}
            )
            if certificate != episode.get("certificate"):
                raise AssertionError("episode teaching certificate is missing or stale")
            if certificate["survivors"] != [policy]:
                raise AssertionError(
                    "declared shortcut family is not uniquely identified by demonstrations"
                )
            teaching_certificates.append({
                "seed": seed,
                "selected": policy,
                "survivors": certificate["survivors"],
                "rejected_by_demonstration": certificate["rejected_by_demonstration"],
            })
        if not all(a["output"] != b["output"] for a, b in zip(all_episode["train"], far_episode["train"])):
            raise AssertionError("minimum demonstrations do not distinguish settings")

        for pair_index, pair in enumerate(far_episode["train"] + far_episode["test"]):
            grid = pair["input"]
            candidates = list(prototype.candidate_footprints(grid))
            source = prototype._source_cells(grid)
            selectable = [candidate for candidate in candidates if candidate != source]
            scores = [prototype._candidate_score(grid, candidate) for candidate in selectable]
            if len(selectable) != 2 or len(set(scores)) != 2:
                raise AssertionError("Stage A did not produce two unequal-score targets")
            farthest = max(selectable, key=lambda candidate: prototype._candidate_score(grid, candidate))
            farthest_origins.add(min(farthest))
            nearest_output = prototype.transform_with_selector(grid, "nearest_non_source")
            if nearest_output == pair["output"]:
                raise AssertionError("nearest-target shortcut survived farthest label")
            rows.append({
                "seed": seed,
                "pair_index": pair_index,
                "shape": [len(grid), len(grid[0])],
                "candidate_count": len(candidates),
                "non_source_scores": sorted(scores),
                "farthest_origin": list(min(farthest)),
                "nearest_counterfactual_differs": True,
            })
    if len(farthest_origins) < 6:
        raise AssertionError("farthest target is insufficiently position-variable")
    if rows[-1]["shape"] != [30, 30]:
        raise AssertionError("four-query bank does not end with 30x30 stress")
    return {
        "schema": "e7c4af96e258-parametric-bounded-self-audit-v2",
        "status": "passed",
        "seeds": [0, 17, 43],
        "settings": ["all_matches", "farthest_match"],
        "demos": 2,
        "queries": 4,
        "checks": {
            "matched_inputs": True,
            "distinct_inputs": True,
            "first_turn_count_independence": True,
            "minimum_demo_setting_identification": True,
            "finite_declared_shortcut_certificate": True,
            "nearest_non_source_bypass_rejected": True,
            "farthest_position_count": len(farthest_origins),
            "stress_shape": [30, 30],
        },
        "teaching_certificates": teaching_certificates,
        "source_sha256": {
            name: _sha(HERE / name)
            for name in ("prototype.py", "adapter.py", "promotion.json", "canonical.rkt", "farthest.rkt", "nearest.rkt")
        },
        "cases": rows,
        "limits": "Finite Python mirror audit; protected-Racket worker and authoring preflight are separate evidence.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "case_count": len(report["cases"]), "out": str(args.out)}))


if __name__ == "__main__":
    main()
