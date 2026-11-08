"""Verify scalar repair, unchanged valid recipes, and canonical Racket labels."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import types

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


def digest(data):
    return hashlib.sha256(data).hexdigest()


def grid_digest(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("choose a new output path")
    root = find_root(__file__)
    current, source, current_hash = load_selected_generator("5e8e4691afde", root=root)
    raw = args.baseline.read_bytes()
    before = types.ModuleType("scalar_repair_baseline")
    exec(compile(raw, str(args.baseline), "exec"), before.__dict__)

    invalid = []
    for band in (None, "easy", "hard"):
        for field, values in (("seed", (True, False, 1.0, 1.75, "1")),
                              ("sample_index", (True, False, 1.0, 1.75, "1", -1))):
            for value in values:
                call = dict(seed=0, sample_index=0, difficulty=band)
                call[field] = value
                old = before.generate(**call)
                record = dict(field=field, value=value, value_type=type(value).__name__,
                              difficulty=band, baseline_accepted=True,
                              baseline_input_sha256=grid_digest(old), repaired_rejected=False)
                try:
                    current.generate(**call)
                except (TypeError, ValueError) as error:
                    record.update(repaired_rejected=True, exception=type(error).__name__, message=str(error))
                invalid.append(record)

    valid = []
    for band in (None, "easy", "medium", "hard"):
        for profile in (None, *current.SCENE_PROFILES):
            for seed in (-17, 2**80):
                kwargs = {"difficulty": band}
                if profile is not None:
                    kwargs["scene_profile"] = profile
                old = before.generate(seed, 3, **kwargs)
                new = current.generate(seed, 3, **kwargs)
                valid.append(dict(seed=seed, sample_index=3, difficulty=band,
                                  scene_profile=profile, identical=old == new,
                                  input_sha256=grid_digest(new), self_check=current.self_check(new)))

    row = next(json.loads(line) for line in canonical_path(root).read_text().splitlines()
               if json.loads(line).get("task_id") == "5e8e4691afde")
    from arc_repl.racket_bridge import RacketBridge
    program = row["program_solution"]
    # This task's pinned program has one explicit outer rule! wrapper.
    # Evaluate its exact lambda without importing execution-layout scripts.
    stripped = program.strip()
    if not stripped.startswith("(rule! (lambda ") or not stripped.endswith(")"):
        raise ValueError("Unexpected canonical rule wrapper")
    callable_program = stripped[len("(rule! "):-1]
    cases = [(f"canonical-{p['split']}-{p['pair_index']}", p["input"], p["output"])
             for p in canonical_pairs("5e8e4691afde", root=root, labeled_only=True)]
    for index, profile in enumerate(current.GENERAL_PROFILES):
        grid = current.generate(17, index, difficulty=("easy", "medium", "hard")[index % 3],
                                scene_profile=profile)
        cases.append((profile, grid, current.rule_mirror(grid)))
    racket = []
    with RacketBridge(timeout=15.0, startup_timeout=60.0) as bridge:
        bridge.eval_text(f"(define scalar_reference {callable_program})")
        for label, inp, expected in cases:
            bridge.define_grid("scalar_input", inp)
            got = bridge.eval_text("(scalar_reference scalar_input)")
            racket.append(dict(case=label, input=inp, output=got,
                               matches_expected=got == expected,
                               input_sha256=grid_digest(inp), output_sha256=grid_digest(got)))
    passed = (len(invalid) == 33 and all(r["repaired_rejected"] for r in invalid)
              and all(r["identical"] and not r["self_check"] for r in valid)
              and len(racket) == 16 and all(r["matches_expected"] for r in racket))
    report = dict(schema="5e8e4691afde-contract-repair-v1", passed=passed,
                  baseline_sha256=digest(raw), generator_sha256=current_hash,
                  generator_path=source.relative_to(root).as_posix(),
                  probe_sha256=digest(Path(__file__).read_bytes()),
                  rule_sha256=digest(program.encode()), rule_hash=current.RULE_HASH,
                  version_unchanged=before.VERSION == current.VERSION,
                  invalid_calls=invalid, valid_recipe_comparisons=valid, racket_cases=racket,
                  totals=dict(invalid_rejected=sum(r["repaired_rejected"] for r in invalid),
                              valid_recipes_identical=sum(r["identical"] for r in valid),
                              racket_passed=sum(r["matches_expected"] for r in racket)))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": passed, **report["totals"]}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
