# Working notes: d8ce64d73f8a

Review assignment `review-4cbe39df361f50d9` replaced the version-1.2 straight-divider family with version 2.0.0.

Key decisions:

- Preserve canonical Racket behavior and pin normalized `RULE_HASH = "2a17285ed2a7"`.
- Expose only observable controls: exact `room_count` and `seed_role`.
- Construct an outer border, one diagonal-contact corner chamber, and zero to two border-backed pockets so the cardinal room count is exact.
- Make every normal draw disagree with both canonical shortcuts that fit all public pairs: eight-connected flood and top-left-component flood.
- Require three demonstrations, declare semantic rivals/witnesses, and test all cyclic query positions.
- Keep independent oracle/Racket probes in `workspace/reference_probe.py` and focused regressions in `tests/test_generator.py`.

Final generator SHA-256: `64650342103ea19e2454f3d79b5cfac7ee4c2a595a309260130884c1a74db471`.
Final battery: 12/12 green. Portable focused tests: 62/62 passed. Expanded lesson census: 300/300 lessons and 1,200/1,200 rotations identifiable against the declared rivals.

The selected base record’s comment-only `target_code` divergence was synchronized to its existing `raw_code`; canonical `puzzles.jsonl` was not changed.
## Current reviewer considerations

Source SHA-256: `64650342103ea19e2454f3d79b5cfac7ee4c2a595a309260130884c1a74db471`.

# Decisions for `d8ce64d73f8a`

## 1. Preserve the authoritative rule

The selected rule already had clear semantics: locate the first red 2, flood its four-connected non-wall region without crossing gray 5, and paint that region 8. I did not change `shared/data/canonical/puzzles.jsonl`. I pinned normalized rule hash `2a17285ed2a7` and synchronized only the selected base record’s comment-only `target_code` difference so strict source authority has one representation.

Rejected alternative: alter the Racket program or broaden traversability semantics. There was no behavioral defect in the authority, and changing it would have obscured that the actual problems were generator topology, contract honesty, and lesson identifiability.

## 2. Replace the one-divider family, not merely randomize it

The old generator created one full vertical divider and put the seed on the left. That family was too narrow and encoded the shortcut “fill the left/top-left side.” The replacement uses:

1. a complete gray outer border;
2. an L-shaped wall backed by the outer border, making a larger isolated corner chamber;
3. a deliberate diagonal-only contact between that corner chamber and the main chamber;
4. zero, one, or two compact U-shaped pockets backed by the top border; and
5. corner transforms to vary orientation.

This construction gives exact 2/3/4 cardinal-component counts by design. The diagonal contact makes an 8-connected solver overreach, while the isolated corner is placed lexicographically before the seeded chamber so a top-left solver fails. A movable free-standing frame was rejected during TDD: an exact failing seed showed that it could align with the L-wall and accidentally split the main chamber, violating the requested room count. Border-backed pockets removed that coupling.

## 3. Keep only observable controls

The public axes are now:

- `room_count`: strict integer 2–4;
- `seed_role`: `largest` or `nonlargest`.

Both are recovered from the generated grid by `observe_overrides`, and the complete cross-product is tested in all difficulty bands. Unknown keys, booleans/floats/strings for integer controls, invalid enum values, and unknown difficulties fail explicitly.

Rejected alternative: retain legacy `palette_kind`, `palette_size`, `n_distinct_colors`, or “texture” names as no-ops. Hidden or inert controls corrupt reproducibility and make downstream data requests untrustworthy. The fixed palette `{0,2,5}` is part of this canonical task and is intentionally not presented as variable.

## 4. Use a small deterministic curriculum schedule

`EXAMPLES_NEEDED = 3`. Samples cycle through `canonical_anchor`, `general_a`, and `general_b` by sample index. The anchor profile uses one of the five canonical dimension pairs; the general profiles use wider difficulty-dependent ranges. The profiles are topology-compatible rather than separate semantic branches, so any three consecutive demonstrations contain the same rule with varied scale and placement.

Every individual draw already refutes both declared shortcuts, so the schedule does not rely on a fragile witness appearing once every few lessons. I nevertheless retained the three-profile schedule to guarantee canonical-size coverage and distribution visibility.

Rejected alternative: one demonstration. One generated example does refute both current rivals, but three demonstrations are a safer teaching contract and match the task’s structural variability. Rejected alternative: use the canonical examples as the only lessons; the canonical set itself leaves both rivals observationally equivalent.

## 5. Declare and test the actual ambiguity

A public-pair probe found exactly two simple rivals that fit all five labeled canonical pairs:

- `eight_connected`: cross gray-free diagonal contacts;
- `top_left`: ignore the red seed and flood the lexicographically first chamber.

The generator declares these as semantic rivals, canonical shortcuts, and lesson competitors. It declares two corresponding witnesses and maps each witness to the rival it is meant to refute. `lesson_identifiable` validates labels and rejects a lesson whenever a declared rival survives the demonstrations.

The final semantic battery checked 12 lessons and 48 query rotations. The expanded census checked 300 lessons, 1,200 pair positions, and 1,200 query rotations, with zero ambiguity or scoring/hook/materialization errors. These are finite declared-rival checks, not a proof against all possible hypotheses.

## 6. Separate production logic from independent evidence

`workspace/reference_probe.py` reimplements four- and eight-connected regions independently of the generator’s helpers. It reads canonical pairs through `reviewer_support`, computes the top-left rival independently, observes room/seed properties, resolves the selected base record portably, and can batch inputs through the real Racket authority.

The 62-test suite covers canonical ownership, exact source/hash synchronization, all public override combinations, invalid controls, deterministic RNG isolation, distribution/profile coverage, destructive validator mutations, every rival counterexample, all cyclic query positions, and real-Racket parity. Tests were written before the production rewrite and first failed on the missing contract and topology behavior.

## 7. Distribution choices and limits

- Easy dimensions: 10–12 by 12–15.
- Medium/default dimensions: 11–15 by 13–18 (default additionally permits 10–16 by 12–19).
- Hard dimensions: 13–18 by 16–22.
- Canonical anchors use `(10,12)`, `(11,13)`, `(12,12)`, `(10,14)`, or `(12,10)`.
- Room counts are 2–4; seed role is largest/nonlargest.
- The nonlargest seed chamber rotates among three non-top-left corners; largest-role scenes put the isolated chamber top-left and seed the main chamber.

The domain intentionally remains bordered, uses only colors 0/2/5, and has compact auxiliary pockets. It does not claim to cover every conceivable wall maze. This restriction is supported by the canonical examples and keeps exact topology, rival witnesses, and override behavior auditable.

## 8. Failed and operational iterations retained

The original before battery, the output-path-collision launch failure, and incomplete audit battery attempts remain under `checks/`. The output-path failure was operational—the checker refuses a pre-existing output directory—not a source failure. The substantive final battery and task tests are separately source-bound and green.
