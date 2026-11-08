from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "6c68e1b008a5"
ROOT = Path.cwd().resolve()
M, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)


def component_depth(panel):
    return max(M._depths(M._support(panel)).values(), default=0)


canonical = []
for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
    a = M._analysis(pair["input"])
    canonical.append(
        {
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "scene_profile": a.get("scene_profile"),
            "errors": a.get("errors", []),
            "reference_max_depth": a.get("max_depth"),
            "reference_palette_size": len(a.get("palette", [])),
            "query_max_depth": component_depth(a["panels"][2]) if not a.get("errors") else None,
            "panel_height": len(a["panels"][0]) if not a.get("errors") else None,
            "panel_width": len(a["panels"][0][0]) if not a.get("errors") else None,
        }
    )

samples = []
by_band = defaultdict(list)
by_profile = defaultdict(list)
for band in ("easy", "medium", "hard"):
    for profile_index, profile in enumerate(M.GENERAL_PROFILES):
        for seed in range(100):
            sample_index = seed * len(M.GENERAL_PROFILES) + profile_index
            grid = M.generate(seed, sample_index, difficulty=band, scene_profile=profile)
            a = M._analysis(grid)
            row = {
                "band": band,
                "profile": profile,
                "reference_max_depth": a["max_depth"],
                "reference_palette_size": len(a["palette"]),
                "query_max_depth": component_depth(a["panels"][2]),
                "panel_height": len(a["panels"][0]),
                "panel_width": len(a["panels"][0][0]),
                "errors": tuple(a["errors"]),
            }
            samples.append(row)
            by_band[band].append(row)
            by_profile[profile].append(row)


def summarize(rows):
    return {
        "count": len(rows),
        "errors": sum(bool(r["errors"]) for r in rows),
        "reference_depth_counts": dict(sorted(Counter(r["reference_max_depth"] for r in rows).items())),
        "palette_size_counts": dict(sorted(Counter(r["reference_palette_size"] for r in rows).items())),
        "query_depth_counts": dict(sorted(Counter(r["query_max_depth"] for r in rows).items())),
        "panel_width_counts": dict(sorted(Counter(r["panel_width"] for r in rows).items())),
    }

canonical_max = max(r["reference_max_depth"] for r in canonical)
generated_max = max(r["reference_max_depth"] for r in samples)
report = {
    "task_id": TASK,
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "rule_hash": M.RULE_HASH,
    "canonical": canonical,
    "generated": {
        "total": summarize(samples),
        "by_band": {band: summarize(rows) for band, rows in sorted(by_band.items())},
        "by_profile": {profile: summarize(rows) for profile, rows in sorted(by_profile.items())},
    },
    "finding": {
        "canonical_reference_max_depth": canonical_max,
        "generated_reference_max_depth": generated_max,
        "canonical_depth_exceeds_generated": canonical_max > generated_max,
        "generated_never_teaches_depth_3_or_more": all(r["reference_max_depth"] < 3 for r in samples),
        "generated_reference_width_fixed_at_4": all(r["panel_width"] == 4 for r in samples),
        "generated_query_depth_at_most_2": all(r["query_max_depth"] <= 2 for r in samples),
    },
}
Path("../checks/audit/6c68e1b008a5/depth-support.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(report["finding"], sort_keys=True))
