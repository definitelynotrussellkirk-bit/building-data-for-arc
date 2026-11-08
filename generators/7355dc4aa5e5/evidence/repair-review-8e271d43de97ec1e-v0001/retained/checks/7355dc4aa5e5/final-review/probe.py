"""Bounded fresh review: queued-marker temporal eligibility and API bounds."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path


HOME = Path(__file__).resolve().parent
REPO = HOME.parents[2] / "repo"
SOURCE = REPO / "generators/7355dc4aa5e5/workspace/parametric"
SNAPSHOT = HOME / "source"
SNAPSHOT.mkdir(exist_ok=True)
source_hashes = {}
for filename in ("family.py", "prototype.py", "canonical.rkt", "adapter.py", "promotion.json"):
    data = (SOURCE / filename).read_bytes()
    (SNAPSHOT / filename).write_bytes(data)
    source_hashes[filename] = hashlib.sha256(data).hexdigest()
spec = importlib.util.spec_from_file_location("fresh7355", SNAPSHOT / "family.py")
family = importlib.util.module_from_spec(spec)
spec.loader.exec_module(family)
SETTINGS = [dict(diagonal_radius=r, propagation_passes=p) for r, p in itertools.product((1, 2), repeat=2)]


def stamp(grid, radius, live_eligibility=False):
    h, w = len(grid), len(grid[0])
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    out = [row[:] for row in grid]
    skipped = []
    for r, c in markers:
        if live_eligibility and out[r][c] != 1:
            skipped.append([r, c, out[r][c]])
            continue
        out[r] = [1] * w
        for rr in range(h):
            out[rr][c] = 1
        out[r][c] = 2
        for dr, dc in itertools.product((-radius, radius), repeat=2):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 3
    return out, skipped


def prediction(grid, settings, live=False):
    out, skipped = stamp(grid, settings["diagonal_radius"], live)
    traces = [skipped]
    if settings["propagation_passes"] == 2:
        bg = next(v for row in grid for v in row if v != 1)
        seeds = [[1 if v == 3 else bg for v in row] for row in out]
        out, skipped = stamp(seeds, settings["diagonal_radius"], live)
        traces.append(skipped)
    return out, traces


def diff(a, b):
    return [[r, c, va, vb] for r, (ra, rb) in enumerate(zip(a, b))
            for c, (va, vb) in enumerate(zip(ra, rb)) if va != vb]


def live_program(settings):
    # The single added guard implements exactly the temporal mistake under review.
    source = family.program(settings)
    needle = "(let ((g2 (reduce"
    assert source.count(needle) == 1
    source = source.replace(needle, "(if (not (= (cell-at acc r c) 1)) acc\n                       (let ((g2 (reduce")
    needle = "                   g\n                   dots))))"
    assert source.count(needle) == 1
    source = source.replace(needle, ")\n" + needle)
    return source


report = {"schema": "7355-fresh-temporal-review-v1", "source_sha256": source_hashes,
          "scope": {"seeds": [0, 63], "settings": SETTINGS, "demos": 2, "queries": 4},
          "setting_ambiguities": [], "live_eligibility_first_findings": [],
          "independent_mirror_mismatches": [], "api_failures": [], "runtime": []}
found = set()
for seed in range(64):
    episodes = [family.generate(seed, settings, demos=2, queries=4) for settings in SETTINGS]
    assert all([p["input"] for p in e["train"] + e["test"]] ==
               [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]] for e in episodes)
    demo_signatures = [repr([p["output"] for p in e["train"]]) for e in episodes]
    if len(set(demo_signatures)) != 4:
        report["setting_ambiguities"].append(seed)
    for settings, episode in zip(SETTINGS, episodes):
        pairs = episode["train"] + episode["test"]
        key = tuple(settings.values())
        predictions = [prediction(p["input"], settings, True) for p in pairs]
        for index, pair in enumerate(pairs):
            if prediction(pair["input"], settings)[0] != pair["output"]:
                report["independent_mirror_mismatches"].append([seed, settings, index])
        if key in found:
            continue
        mismatches = [i for i, (pair, pred) in enumerate(zip(pairs, predictions)) if pair["output"] != pred[0]]
        if any(i < 2 for i in mismatches) or not mismatches:
            continue
        query_index = mismatches[0] - 2
        pair, pred = pairs[mismatches[0]], predictions[mismatches[0]]
        finding = {"seed": seed, "settings": settings, "train_mismatches": [],
                   "query_mismatches": [i - 2 for i in mismatches], "witness_query_index": query_index,
                   "input": pair["input"], "correct_output": pair["output"], "rival_output": pred[0],
                   "skipped_marker_traces": pred[1], "cell_differences": diff(pair["output"], pred[0]),
                   "episode": episode}
        report["live_eligibility_first_findings"].append(finding)
        found.add(key)
        print(json.dumps({"finding": "live_marker_eligibility", "seed": seed, "settings": settings,
                          "query_index": query_index, "different_cells": len(finding["cell_differences"])}), flush=True)

valid = SETTINGS[0]
for label, kwargs in [("seed_bool", {"seed": True}), ("seed_negative", {"seed": -1}),
                      ("seed_upper", {"seed": 2**63}), ("demos_bool", {"demos": True}),
                      ("demos_low", {"demos": 1}), ("demos_high", {"demos": 7}),
                      ("queries_bool", {"queries": True}), ("queries_low", {"queries": 0}),
                      ("queries_high", {"queries": 5}),
                      ("radius_bool", {"settings": dict(diagonal_radius=True, propagation_passes=1)}),
                      ("passes_float", {"settings": dict(diagonal_radius=1, propagation_passes=2.0)})]:
    args = dict(seed=0, settings=valid, demos=2, queries=4)
    args.update(kwargs)
    try:
        family.generate(**args)
    except ValueError:
        pass
    else:
        report["api_failures"].append(label)
for seed in (0, 2**63 - 1):
    episode = family.generate(seed, valid, demos=6, queries=4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert max(max(len(p["input"]), len(p["input"][0])) for p in episode["train"] + episode["test"]) <= 30

from arc_repl.isolated_verifier import verify_candidate

for i, finding in enumerate(report["live_eligibility_first_findings"]):
    episode, settings = finding["episode"], finding["settings"]
    correct = family.program(settings)
    rival = live_program(settings)
    (HOME / f"finding-{i}-correct.rkt").write_text(correct)
    (HOME / f"finding-{i}-rival.rkt").write_text(rival)
    row = {"seed": finding["seed"], "settings": settings}
    for role, program in (("correct", correct), ("rival", rival)):
        receipt = verify_candidate(episode, program, racket_path=os.environ["RACKET_PATH"])
        (HOME / f"finding-{i}-{role}-execution.json").write_text(json.dumps(receipt, indent=2) + "\n")
        row[role] = {"status": receipt.get("status"), "hidden_exact": receipt.get("hidden_exact"),
                     "error": receipt.get("error")}
        if receipt.get("status") == "pass":
            expected = [p["output"] if role == "correct" else prediction(p["input"], settings, True)[0]
                        for p in episode["test"]]
            row[role]["independent_prediction_match"] = receipt["test_outputs"] == expected
    report["runtime"].append(row)

(HOME / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: report[key] for key in ("setting_ambiguities", "independent_mirror_mismatches", "api_failures", "runtime")}, indent=2))
assert not report["setting_ambiguities"] and not report["independent_mirror_mismatches"] and not report["api_failures"]
assert all(r["correct"]["status"] == r["rival"]["status"] == "pass" and r["correct"]["hidden_exact"] is True
           and r["rival"]["hidden_exact"] is False and r["correct"]["independent_prediction_match"]
           and r["rival"]["independent_prediction_match"] for r in report["runtime"])
