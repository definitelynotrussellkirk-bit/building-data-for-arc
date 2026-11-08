"""Source-bound Racket probe for rank shortcuts and actual lesson rotations.

From the extracted packet root:
  python3 review.py run python3 generators/af840d59f24c/workspace/probe_rank_shortcuts.py \
      --out ../checks/rank-shortcuts.json --seeds 0,17,99173 --bands none,easy,medium,hard

This probes the currently selected source; historical templates are competitors,
not assumptions about current construction. Existing output paths are refused.
The rival set is declared task rivals plus the three probes below; shared generic
object/position rivals are outside this targeted probe and need their own gate.
Exit codes: 0 targeted probe passed, 1 findings, 2 Racket unavailable/failed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "af840d59f24c"


def first_seen_template(grid):
    """Historical row-order lookup; does not sort columns horizontally."""
    seen = list(dict.fromkeys(c for row in grid for c, value in enumerate(row) if value == 0))
    size = len(seen)
    if any(all(row[c] == 0 for row in grid) for c in seen):
        middle = size // 2
        order = [middle] + [i for i in reversed(range(size)) if i != middle]
    else:
        order, lo, hi = [size - 1], 0, size - 2
        while lo <= hi:
            order.append(lo)
            lo += 1
            if lo <= hi:
                order.append(hi)
                hi -= 1
    ranks = {column: rank + 1 for column, rank in zip(seen, order, strict=True)}
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)] for row in grid]


def frequency_template(grid):
    """Historical count lookup; horizontal ordering resolves equal-count ties."""
    counts = Counter(c for row in grid for c, value in enumerate(row) if value == 0)
    patterns = {4: (2, 4, 3, 1), 5: (2, 4, 3, 1, 2), 6: (2, 5, 4, 1, 3, 2),
                7: (2, 5, 4, 1, 3, 2, 4), 8: (2, 5, 4, 1, 3, 2, 4, 5)}
    pattern = (3, 5, 2, len(grid), 4, 6) if len(grid) in counts.values() else patterns.get(len(counts), ())
    ranks = {}
    for count in set(pattern):
        columns = sorted(c for c, value in counts.items() if value == count)
        labels = [i + 1 for i, value in enumerate(pattern) if value == count]
        if len(columns) != len(labels):
            return deepcopy(grid)
        ranks.update(zip(columns, labels, strict=True))
    if set(ranks) != set(counts):
        return deepcopy(grid)
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)] for row in grid]


def erase_nonmodal(grid):
    """Correct zero ranks, but wrong preservation of nonmodal nonzero cells."""
    counts = Counter(value for row in grid for value in row if value != 0)
    modal = min(counts, key=lambda color: (-counts[color], color))
    columns = sorted({c for row in grid for c, value in enumerate(row) if value == 0})
    ranks = {column: rank + 1 for rank, column in enumerate(columns)}
    return [[ranks[c] if value == 0 else modal for c, value in enumerate(row)] for row in grid]


PROBE_RIVALS = {"probe_first_seen_template": first_seen_template,
                "probe_frequency_template": frequency_template,
                "probe_erase_nonmodal": erase_nonmodal}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", default="0,17,99173", help="Comma-separated integer seeds")
    parser.add_argument("--bands", default="none,easy,medium,hard", help="Comma-separated none/easy/medium/hard")
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    try:
        seeds = list(dict.fromkeys(int(value.strip()) for value in args.seeds.split(",")))
        bands = list(dict.fromkeys(None if value.strip() in ("none", "mixed") else value.strip()
                                   for value in args.bands.split(",")))
        if not seeds or not bands or any(band not in (None, "easy", "medium", "hard") for band in bands):
            raise ValueError("invalid seeds or bands")
    except ValueError as exc:
        parser.error(str(exc))

    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator(TASK_ID, root=root)
    helper_path = Path(__file__).with_name("reference_probe.py")
    spec = importlib.util.spec_from_file_location("rank_shortcut_reference_probe", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    program = helper.canonical_record()["program_solution"]
    actual_rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    period, demo_count = gen.LESSON_SCHEDULE_PERIOD, gen.EXAMPLES_NEEDED
    assert type(period) is int and period > 0 and type(demo_count) is int and demo_count > 0
    report = {
        "schema": "af840d59f24c-rank-shortcut-probe-v1", "task_id": TASK_ID,
        "source_path": str(source), "source_sha256": source_sha,
        "declared_rule_hash": gen.RULE_HASH, "executed_rule_hash": actual_rule_hash,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_helper_sha256": hashlib.sha256(helper_path.read_bytes()).hexdigest(),
        "command": shlex.join([sys.executable, *sys.argv]), "cwd": str(Path.cwd()),
        "seeds": seeds, "bands": bands, "schedule_period": period,
        "schedule_profiles": list(gen.SCHEDULE_PROFILES), "demonstrations": demo_count,
        "rival_scope": "Declared task rivals plus independent first-seen/frequency/modal probes; shared generic rivals excluded.",
    }
    calls, grids, streams = [], [], {}
    for seed in seeds:
        for band in bands:
            stream = []
            for index in range(period + demo_count):
                stream.append(len(grids))
                calls.append({"seed": seed, "sample_index": index, "difficulty": band})
                grids.append(gen.generate(seed, index, difficulty=band))
            streams[seed, band] = stream
    canonical = list(canonical_pairs(TASK_ID, root=root, labeled_only=True))
    try:
        outputs = helper.racket_outputs(grids + [pair["input"] for pair in canonical])
    except Exception as exc:
        report.update(status="blocked_racket", error=f"{type(exc).__name__}: {exc}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "error": report["error"], "out": str(args.out)}))
        return 2
    assert len(outputs) == len(grids) + len(canonical)
    labels, canonical_labels = outputs[:len(grids)], outputs[len(grids):]
    rivals = {**getattr(gen, "SEMANTIC_RIVALS", {}), **gen.LESSON_COMPETITORS, **PROBE_RIVALS}
    matches = {name: [rival(grid) == label for grid, label in zip(grids, labels, strict=True)]
               for name, rival in rivals.items()}
    report["racket_grids_checked"] = len(outputs)
    report["canonical_reference_agreements"] = [pair["output"] == label
                                                for pair, label in zip(canonical, canonical_labels, strict=True)]
    report["rival_rates"] = {
        name: {"generated_matches": sum(matches[name]), "generated_total": len(grids),
               "generated_match_rate": sum(matches[name]) / len(grids),
               "canonical_matches": sum(rival(pair["input"]) == label
                                        for pair, label in zip(canonical, canonical_labels, strict=True)),
               "canonical_total": len(canonical)} for name, rival in rivals.items()
    }
    report["generated"] = [
        {"call": call, "input_sha256": digest(grid), "racket_output_sha256": digest(label),
         "observed": gen.observe_overrides(grid), "self_check": gen.self_check(grid),
         "mirror_matches_racket": gen.rule_mirror(grid) == label}
        for call, grid, label in zip(calls, grids, labels, strict=True)
    ]
    report["reference_examples"] = {}
    for call, grid, label in zip(calls, grids, labels, strict=True):
        profile = gen.observe_overrides(grid)["scene_profile"]
        report["reference_examples"].setdefault(profile, {"call": call, "input": grid, "racket_output": label})
    rotations, witnesses = [], {}
    for (seed, band), stream in streams.items():
        for start in range(period):
            window = stream[start:start + demo_count + 1]
            for held_out, query_index in enumerate(window):
                demo_indices = [i for i in window if i != query_index]
                survivors = [name for name in rivals if all(matches[name][i] for i in demo_indices)]
                ambiguous = [name for name in survivors if not matches[name][query_index]]
                demos = [{"input": grids[i], "output": labels[i]} for i in demo_indices]
                query = {"input": grids[query_index], "output": labels[query_index]}
                row = {"seed": seed, "difficulty": band, "start": start, "held_out": held_out,
                       "demo_indices": [calls[i]["sample_index"] for i in demo_indices],
                       "query_index": calls[query_index]["sample_index"], "surviving_rivals": survivors,
                       "ambiguous_rivals": ambiguous, "hook_reasons": gen.lesson_identifiable(demos, query)}
                rotations.append(row)
                for name in ambiguous:
                    witnesses.setdefault(name, {"rotation": row, "demos": demos, "query": query,
                                                "rival_query_output": rivals[name](query["input"])})
    residual = [name for name in ("probe_first_seen_template", "probe_frequency_template")
                if all(matches[name]) and report["rival_rates"][name]["canonical_matches"] < len(canonical)]
    source_unchanged = hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    findings = (bool(residual) or any(row["ambiguous_rivals"] or row["hook_reasons"] for row in rotations)
                or any(row["self_check"] or not row["mirror_matches_racket"] for row in report["generated"])
                or not all(report["canonical_reference_agreements"]) or actual_rule_hash != gen.RULE_HASH
                or not source_unchanged)
    report.update(status="findings" if findings else "passed_targeted_probe",
                  source_unchanged=source_unchanged, residual_template_shortcuts=residual,
                  rotation_total=len(rotations),
                  ambiguous_rotation_count=sum(bool(row["ambiguous_rivals"]) for row in rotations),
                  ambiguity_counts={name: sum(name in row["ambiguous_rivals"] for row in rotations) for name in rivals},
                  hook_rejection_count=sum(bool(row["hook_reasons"]) for row in rotations),
                  rotations=rotations, first_ambiguity_witnesses=witnesses)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "source_sha256", "racket_grids_checked",
                     "rival_rates", "rotation_total", "ambiguous_rotation_count", "hook_rejection_count",
                     "residual_template_shortcuts")}, indent=2))
    return int(findings)


if __name__ == "__main__":
    raise SystemExit(main())
