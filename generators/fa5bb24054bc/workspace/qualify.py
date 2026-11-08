"""Independent qualification probe for fa5bb24054bc.

The repository lesson census checks production lessons against declared rivals.
This companion adds two task-specific checks the generic census does not own:
all cyclic four-demo starts and the complete Cartesian product of exact axes.
It uses the independent oracle in reference_probe.py and emits replayable JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reference_probe import (
    canonical_pairs,
    load_generator,
    observed_axes,
    off_diagonal_codes,
    profile,
    relation_output,
)

TASK = "fa5bb24054bc"


def _digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def audit(module, *, per_band: int = 100, window_starts: int = 32) -> dict:
    if per_band < 1 or window_starts < 1:
        raise ValueError("per_band and window_starts must be positive")

    report = {
        "schema": "fa5bb24054bc-task-local-qualification-v1",
        "task_id": TASK,
        "generator_version": module.VERSION,
        "per_band": per_band,
        "window_starts": window_starts,
        "limits": [
            "Finite replayable sampling is evidence against named shortcuts, not universal induction.",
            "The Python oracle is independent test tooling; canonical Racket remains label authority.",
        ],
    }

    # The canonical set's exact semantic gap: both shortcuts fit all five pairs.
    canonical = canonical_pairs()
    fitting = []
    canonical_status = {}
    for name, rival in sorted(module.CANONICAL_SHORTCUTS.items()):
        fits = sum(rival(deepcopy(pair["input"])) == pair["output"] for pair in canonical)
        canonical_status[name] = {"fits": fits, "pairs": len(canonical)}
        if fits == len(canonical):
            fitting.append(name)
    report["canonical_shortcut_fit"] = canonical_status
    report["canonical_fitting_shortcuts"] = fitting

    # Every cyclic start gets four consecutive profile residues. Force N=2 so
    # each demo isolates one relation label instead of relying on larger scenes.
    cyclic_failures = []
    cyclic_rows = []
    for start in range(window_starts):
        seed = int(hashlib.sha256(f"qualify:window:{start}".encode()).hexdigest()[:12], 16)
        labels = set()
        profiles = []
        for sample_index in range(start, start + 4):
            grid = module.generate(
                seed,
                sample_index,
                grid_h=3,
                n_panels=2,
                sep_width=1,
            )
            output = relation_output(grid)
            labels.update(off_diagonal_codes(output))
            profiles.append(module.schedule_profile(seed, sample_index))
        row = {"start": start, "profiles": profiles, "labels": sorted(labels)}
        cyclic_rows.append(row)
        if labels != {0, 2, 3, 6}:
            cyclic_failures.append(row)
    report["cyclic_windows"] = cyclic_rows
    report["cyclic_window_failures"] = cyclic_failures

    # Exhaust the complete legal Cartesian product of exact axes.  This is only
    # 6*5*2=60 cases and proves there are no hidden width/height incompatibilities.
    override_failures = []
    max_width = 0
    for grid_h in range(3, 9):
        for n_panels in range(2, 7):
            for sep_width in range(1, 3):
                expected = {
                    "grid_h": grid_h,
                    "n_panels": n_panels,
                    "sep_width": sep_width,
                }
                sample_index = grid_h * 100 + n_panels * 10 + sep_width
                try:
                    grid = module.generate(8128, sample_index, difficulty="hard", **expected)
                    max_width = max(max_width, len(grid[0]))
                    issues = module.self_check(grid)
                    observed = observed_axes(grid)
                    if issues or observed != expected or len(grid[0]) > 30:
                        override_failures.append(
                            {
                                "expected": expected,
                                "observed": observed,
                                "issues": issues,
                                "width": len(grid[0]),
                            }
                        )
                except Exception as exc:  # keep exact replay details
                    override_failures.append(
                        {"expected": expected, "exception": f"{type(exc).__name__}: {exc}"}
                    )
    report["joint_override_cases"] = 60
    report["joint_override_failures"] = override_failures

    # Broad production sampling: exact uniqueness, profiles, output labels and
    # direct disagreement rates for every declared canonical-fitting shortcut.
    unique_inputs = set()
    unique_outputs = set()
    relation_counts = Counter()
    profile_counts = Counter()
    panel_counts = Counter()
    self_check_failures = []
    rival_refutations = Counter({name: 0 for name in module.CANONICAL_SHORTCUTS})
    by_band = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        band_counts = Counter()
        for index in range(per_band):
            seed = int(
                hashlib.sha256(f"qualify:broad:{band}:{index}".encode()).hexdigest()[:12],
                16,
            )
            sample_index = index * 7 + band_index
            grid = module.generate(seed, sample_index, difficulty=band)
            output = relation_output(grid)
            max_width = max(max_width, len(grid[0]))
            issues = module.self_check(grid)
            if issues:
                self_check_failures.append(
                    {"band": band, "index": index, "seed": seed, "issues": issues}
                )
            unique_inputs.add(_digest(grid))
            unique_outputs.add(_digest(output))
            panel_counts[len(output)] += 1
            profile_counts[str(profile(grid))] += 1
            for code in off_diagonal_codes(output):
                relation_counts[code] += 1
            for name, rival in module.CANONICAL_SHORTCUTS.items():
                if rival(deepcopy(grid)) != output:
                    rival_refutations[name] += 1
                    band_counts[f"refutes:{name}"] += 1
            band_counts["samples"] += 1
            # strict_canonical_like returns [] on a canonical profile.
            if module.strict_canonical_like(grid) == []:
                band_counts["canonical_profile"] += 1
        by_band[band] = dict(band_counts)

    report["max_generated_width"] = max_width
    report["unique_inputs"] = len(unique_inputs)
    report["unique_outputs"] = len(unique_outputs)
    report["relation_code_presence_counts"] = {str(k): v for k, v in sorted(relation_counts.items())}
    report["input_profile_counts"] = dict(sorted(profile_counts.items()))
    report["panel_count_distribution"] = {str(k): v for k, v in sorted(panel_counts.items())}
    report["generated_shortcut_refutations"] = dict(rival_refutations)
    report["self_check_failures"] = self_check_failures
    report["by_band"] = by_band

    report["status"] = (
        "fail"
        if cyclic_failures or override_failures or self_check_failures
        or any(count == 0 for count in rival_refutations.values())
        else "pass"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--window-starts", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = audit(module, per_band=args.per_band, window_starts=args.window_starts)
    report["generator_sha256"] = hashlib.sha256(
        (args.generator or Path(module.__file__)).read_bytes()
    ).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "unique_inputs": report["unique_inputs"],
                "unique_outputs": report["unique_outputs"],
                "cyclic_window_failures": len(report["cyclic_window_failures"]),
                "joint_override_failures": len(report["joint_override_failures"]),
                "generated_shortcut_refutations": report["generated_shortcut_refutations"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
