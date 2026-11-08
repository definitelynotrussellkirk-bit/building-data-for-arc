"""Bounded changed-scope probe, run through the packet's review.py run."""
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


def main():
    root = find_root(__file__)
    module, source, source_hash = load_selected_generator("96ebf3053dbe", root=root)
    evidence = root.parent / "checks/96ebf3053dbe"
    before_path = evidence / "before.json"
    before = json.loads(before_path.read_text())
    witness = before["witness"]
    errors = module.self_check(witness)
    assert "every lower color-2 marker must anchor exactly one 6-component" in errors
    rejections = {}
    for name in ("rule_mirror", "observe_overrides"):
        try:
            getattr(module, name)(witness)
        except ValueError as exc:
            rejections[name] = str(exc)
        else:
            raise AssertionError(f"{name} accepted the shared marker")
    pairs = canonical_pairs("96ebf3053dbe", root=root)
    for pair in pairs:
        assert module.self_check(pair["input"]) == []
        assert module.rule_mirror(pair["input"]) == pair["output"]
    profiles = []
    for profile in module.GENERAL_PROFILES:
        grid = module.generate(17, 23, difficulty="medium", scene_profile=profile)
        assert module.self_check(grid) == [], profile
        records = module._analysis(grid)["records"]
        assert len({record["anchor"] for record in records}) == len(records), profile
        profiles.append(profile)
    result = {
        "task_id": "96ebf3053dbe",
        "generator_sha256": source_hash,
        "before_evidence_sha256": hashlib.sha256(before_path.read_bytes()).hexdigest(),
        "witness_errors": errors,
        "rejected_entry_points": rejections,
        "canonical_pairs_preserved": len(pairs),
        "generated_profiles_preserved": profiles,
        "generated_settings": {"seed": 17, "sample_index": 23, "difficulty": "medium"},
        "reference_execution": "not rerun; validator-only change, canonical outputs compared with retained labels",
    }
    (evidence / "after.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
