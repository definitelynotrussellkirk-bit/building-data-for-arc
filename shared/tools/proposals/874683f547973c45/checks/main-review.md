# Independent main-generator review

**Disposition: accepted after one concrete correction, with bounded verification.** Reviewed `repo/generators/33275a4aae3e/generator.py`, the three main task test files, and `workspace/review-plan.md`. The parametric prototype was outside this review. No main source was edited by this reviewer.

## MR1 — resolved optional-null schedule defect

The reviewed candidate SHA-256 was `2cec2f6f29ea427ef6e770f2ad530dfe7cdc781e6766ee94558dfd5592d175b1`. Its `if "scene_profile" in overrides` branch treated an explicit `None` as an active override, while shared `GenCtx._override` treats `None` as unset. Consequently, an accepted no-op override selected from all ten profiles instead of following the declared period-2 schedule.

The independent reproducer used seed `3`, sample indices `0..3`, default difficulty, and `scene_profile=None`. Profiles were `two_room_lr_22x25`, `two_room_tr_21x24`, `three_room_lr_24x25`, `stepped_l_22x25`. Holding out pair 3 left three demonstrations fitted by both `complete_rectangle_fill` and `eight_connected_exterior`, with each rival changing the Python-mirror query prediction. The same calls with the override omitted followed witness/legacy/witness/legacy. This was a teaching-contract defect for an accepted optional-null call; the ordinary omitted-override census did not exercise it.

The implementer changed the branch to `overrides.get("scene_profile") is not None` and added an omitted-versus-null regression. The final generator SHA-256 is `2b77752aa819ff3d2e1b5214f698055365f4ed747cd083baed087d97751fe67f`. The implementer reports **55 main tests passed / 159 subtests**; those suite receipts are separate from this independent check.

## Independent checks

On the original candidate, bounded supplemental Python probes passed for six invalid non-null profile values; twenty explicit-profile samples covering all ten profiles and both index parities; two hundred deterministic, input-preserving, fresh-output rival calls; and eight held-out rotations spanning both default schedule residues. Seed `-20261022` was used for the twenty explicit-profile samples, and seed `3301` for the rotation windows. Initial probes used the wrapper's unpinned `python3` payload. These are not Racket-parity claims.

On the final source, the exact command below exited **0**. It checked five omitted-versus-null calls at seed `3`, indices `0..4`, plus every holdout of the four-pair windows starting at residues `0` and `1`: **5/5 equality and schedule checks, 8/8 held-out rotations**. The interpreter reported `/workspace/scratch/e99e6bfff21b/packet/WORK/repo/../.venv/bin/python`. Actual outer cwd was `/workspace/scratch/e99e6bfff21b/packet` (`packet_root`); the wrapper's payload cwd was `WORK/repo/`.

```bash
python3 review.py run ../.venv/bin/python - <<'PY'
import json, sys
from pathlib import Path
from reviewer_support import load_selected_generator
m, source, digest = load_selected_generator('33275a4aae3e', root=Path.cwd())
assert digest == '2b77752aa819ff3d2e1b5214f698055365f4ed747cd083baed087d97751fe67f'
pairs = []
profiles = []
for index in range(5):
    omitted = m.generate(3, index)
    explicit_null = m.generate(3, index, scene_profile=None)
    assert explicit_null == omitted
    assert m.self_check(explicit_null) == []
    profile = m.observe_overrides(explicit_null)['scene_profile']
    assert (profile in m.CONNECTIVITY_PROFILES) == (index % 2 == 0)
    profiles.append(profile)
    pairs.append({'input': explicit_null, 'output': m.solve_python(explicit_null)})
for start in (0, 1):
    window = pairs[start:start + 4]
    for query in range(4):
        demos = [pair for index, pair in enumerate(window) if index != query]
        assert m.lesson_identifiable(demos, window[query]) == []
print(json.dumps({'source_sha256': digest, 'runtime_python': sys.executable, 'seed': 3, 'sample_indices': list(range(5)), 'null_equals_omitted_checks': 5, 'heldout_rotations_passed': 8, 'profiles': profiles}, indent=2))
PY
```

The final profile sequence was `stepped_l_22x25`, `two_room_tr_21x24`, `stepped_r_22x25`, `three_room_b_22x25`, `stepped_l_22x25`.

## Review conclusions and limits

The stepped geometry supplies both a nonrectangular enclosure and a diagonally sealed pocket. Its explicit nine-crossing override is used consistently in construction acceptance and profile observation; all ten profile signatures are distinct. Non-null explicit profile requests take precedence over the default schedule. Rival implementations preserve their inputs and return fresh rows in the bounded probes.

The lesson argument assumes four consecutive accepted default samples, three demonstrations, and one query. Every such alternating window contains two connectivity witnesses; a single held-out query leaves at least one. This is a finite declared-rival guarantee, not universal identifiability. Explicit non-null profile overrides can intentionally remove the schedule's witnesses and require their own lesson assessment. `strict_canonical_like` recognizes the four public-form structural signatures conservatively; it does not establish exhaustive canonical visual or distribution equivalence. Racket parity, broader sampling, and final-source census coverage belong to the main verification receipts, not these small independent Python probes.
