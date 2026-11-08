#!/usr/bin/env python3
"""Compare the optional isolated calibration patch without changing shared code."""
from pathlib import Path
import hashlib
import json
from reproduce import HERE, ROOT, TASK, canonical_pairs, load_detector, load_selected_generator


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


original_path = HERE / "original/scripts/generator_defect_lint.py"
proposed_path = HERE / "proposed/scripts/generator_defect_lint.py"
assert digest(original_path) == digest(ROOT / "shared/tools/generator_defect_lint.py")
original = load_detector(original_path, "comparison_original")
proposed = load_detector(proposed_path, "comparison_proposed")
generator, generator_path, generator_hash = load_selected_generator(TASK, root=ROOT)
pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
train = [(p["input"], p["output"]) for p in pairs if p["split"] == "train"]
inputs = [p["input"] for p in pairs]
bands = [None] * len(inputs)
old_named = original.probe_selfcheck_minimal_impostors(generator, inputs, bands, train)
new_named = proposed.probe_selfcheck_minimal_impostors(generator, inputs, bands, train)
old_power = original.probe_selfcheck_power(generator, inputs, bands)
new_power = proposed.probe_selfcheck_power(generator, inputs, bands)
assert "solid_2x2" in old_named[0] and "solid_2x2" not in new_named[0]
assert all(name in new_named[0] for name in ("singleton 5/5", "short_line 5/5"))
assert old_power == new_power
report = {"status": "optional proposal tested in isolated module copies only; NOT APPLIED",
          "original_detector_sha256": digest(original_path),
          "proposed_detector_sha256": digest(proposed_path),
          "proposal_patch_sha256": digest(HERE / "proposal.patch"),
          "test_source_sha256": digest(HERE / "test_proposed_calibration.py"),
          "comparison_source_sha256": digest(Path(__file__)),
          "generator_source": str(generator_path.relative_to(ROOT)),
          "generator_sha256": generator_hash,
          "canonical_pairs": len(pairs),
          "canonical_minimal_kinds_before": sorted(original._canonical_minimal_kinds(train)),
          "canonical_minimal_kinds_proposed": sorted(proposed._canonical_minimal_kinds(train)),
          "minimal_warning_before": old_named, "minimal_warning_proposed": new_named,
          "power_warning_before": old_power, "power_warning_proposed": new_power,
          "shared_source_unchanged": True,
          "remaining_warnings": "singleton/short_line named acceptance and aggregate selfcheck-power remain; this proposal only calibrates exact canonical minimal probe matches."}
(HERE / "proposal-comparison.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, sort_keys=True))
