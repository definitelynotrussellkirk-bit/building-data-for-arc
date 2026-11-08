"""Bounded self-audit for the stacked-panel output-mode parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("_xor_probe_adapter", path)
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
    largest_origins = set()
    for seed in (0, 17, 43):
        episodes = {
            mode: adapter.generate(seed, {"output_mode": mode}, 2, 4)
            for mode in ("xor_mask", "largest_xor_component")
        }
        canonical = episodes["xor_mask"]
        largest = episodes["largest_xor_component"]
        canonical_inputs = [pair["input"] for pair in canonical["train"] + canonical["test"]]
        largest_inputs = [pair["input"] for pair in largest["train"] + largest["test"]]
        if canonical_inputs != largest_inputs:
            raise AssertionError("hidden setting changed sampled inputs")
        if len({json.dumps(grid, separators=(",", ":")) for grid in canonical_inputs}) != 6:
            raise AssertionError("episode contains duplicate inputs")
        for mode, episode in episodes.items():
            prefix = adapter.generate(seed, {"output_mode": mode}, 2, 1)
            if prefix["train"] != episode["train"] or prefix["test"][0] != episode["test"][0]:
                raise AssertionError("one-query request changed first-turn content")
            certificate = prototype.teaching_certificate(
                episode["train"], {"output_mode": mode}
            )
            if certificate != episode.get("certificate"):
                raise AssertionError("episode teaching certificate is missing or stale")
            if certificate["survivors"] != [mode]:
                raise AssertionError(
                    "declared shortcut family is not uniquely identified by demonstrations"
                )
            teaching_certificates.append({
                "seed": seed,
                "selected": mode,
                "survivors": certificate["survivors"],
                "rejected_by_demonstration": certificate["rejected_by_demonstration"],
            })
        if not all(a["output"] != b["output"] for a, b in zip(canonical["train"], largest["train"])):
            raise AssertionError("minimum demonstrations do not distinguish settings")

        for pair_index, pair in enumerate(largest["train"] + largest["test"]):
            grid = pair["input"]
            xor = prototype.xor_cells(grid)
            parts = prototype.components(xor)
            sizes = [len(component) for component in parts]
            if len(parts) < 2 or sizes[0] <= sizes[1]:
                raise AssertionError("Stage A did not produce a unique largest XOR component")
            largest_origins.add(min(parts[0]))
            if prototype.transform_with_selector(grid, "xor_mask") == pair["output"]:
                raise AssertionError("whole-XOR shortcut survived largest-component label")
            if prototype.transform_with_selector(grid, "largest_top_component") == pair["output"]:
                raise AssertionError("top-panel component shortcut survived largest-XOR label")
            rows.append({
                "seed": seed,
                "pair_index": pair_index,
                "input_shape": [len(grid), len(grid[0])],
                "output_shape": [4, len(grid[0])],
                "xor_cell_count": len(xor),
                "xor_component_sizes": sizes,
                "largest_origin": list(min(parts[0])),
                "top_panel_counterfactual_differs": True,
            })
    if len(largest_origins) < 6:
        raise AssertionError("largest XOR component is insufficiently position-variable")
    if rows[-1]["input_shape"] != [9, 30]:
        raise AssertionError("four-query bank does not end with 9x30 stress")
    return {
        "schema": "08eaba8254b2-parametric-bounded-self-audit-v2",
        "status": "passed",
        "seeds": [0, 17, 43],
        "settings": ["xor_mask", "largest_xor_component"],
        "demos": 2,
        "queries": 4,
        "checks": {
            "matched_inputs": True,
            "distinct_inputs": True,
            "first_turn_count_independence": True,
            "minimum_demo_setting_identification": True,
            "finite_declared_shortcut_certificate": True,
            "whole_xor_bypass_rejected": True,
            "top_panel_component_bypass_rejected": True,
            "largest_origin_count": len(largest_origins),
            "stress_input_shape": [9, 30],
            "stress_output_shape": [4, 30],
        },
        "teaching_certificates": teaching_certificates,
        "source_sha256": {
            name: _sha(HERE / name)
            for name in (
                "prototype.py", "adapter.py", "promotion.json", "canonical.rkt",
                "largest.rkt", "top-largest.rkt"
            )
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
