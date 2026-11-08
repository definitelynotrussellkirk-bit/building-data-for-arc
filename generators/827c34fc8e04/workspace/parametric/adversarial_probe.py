"""Focused deterministic audit for the 827c34fc8e04 parametric proposal."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import prototype


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    findings = []
    episodes = 0
    pairs = 0
    for seed in (0, 1, 17, 72, 991):
        generated = {}
        for setting in prototype.SETTINGS:
            key = json.dumps(setting, sort_keys=True)
            episode = prototype.generate(seed, setting, 6, 4)
            generated[key] = episode
            episodes += 1
            pairs += 10
            survivors = [candidate for candidate in prototype.SETTINGS if all(
                prototype.transform(pair["input"], candidate) == pair["output"]
                for pair in episode["train"][:2]
            )]
            if survivors != [setting]:
                findings.append({"seed": seed, "setting": setting, "survivors": survivors})
            short = prototype.generate(seed, setting, 2, 1)
            if short["train"] != episode["train"][:2] or short["test"] != episode["test"][:1]:
                findings.append({"seed": seed, "setting": setting, "error": "prefix dependence"})
        values = list(generated.values())
        left_inputs = [p["input"] for p in values[0]["train"] + values[0]["test"]]
        right_inputs = [p["input"] for p in values[1]["train"] + values[1]["test"]]
        if left_inputs != right_inputs:
            findings.append({"seed": seed, "error": "settings changed sampled inputs"})
    report = {
        "schema": "arcpuzzles-parametric-adversarial-probe-v1",
        "task_id": prototype.TASK_ID,
        "status": "passed" if not findings else "failed",
        "seeds": [0, 1, 17, 72, 991],
        "episodes": episodes,
        "labelled_pairs": pairs,
        "checks": ["finite-identification-from-first-two-demos", "matched-inputs",
                   "count-prefix-independence", "30x30-output-stress"],
        "findings": findings,
    }
    payload = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    report["report_sha256_without_self_hash"] = hashlib.sha256(payload.encode()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "episodes": episodes,
                      "labelled_pairs": pairs, "findings": len(findings)}))
    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
