# Current generator notes: `ae0a295c2271`

## Intended rule

Treat each 4-connected nonzero component as an object. Normalize occupied cells
by translation only; rotations and reflections remain distinct shapes. Objects
whose exact shape occurs once become red (`2`), and objects whose exact shape
occurs twice become blue (`1`). Background remains `0`. The selected Racket
authority is unchanged and pinned by `RULE_HASH = "6c9ec74ee7cf"`.

## Current generator contract

- Version `5.0.0`; final generator SHA-256
  `c14282044b5908ab0d49a53920dd5a8c611a3a43156f59fa71c43fe825069071`.
- Strict literal-integer `seed` and nonnegative literal-integer `sample_index`;
  difficulty is `None|easy|medium|hard`; unknown or invalid overrides reject.
- Five exact observable axes: `grid_h`, `grid_w`, `n_twin_pairs`, `n_uniques`,
  and `input_color`.
- Four deterministic curriculum profiles preserve both canonical 10x10/color-8
  anchors and two non-8 profiles. Every four consecutive pairs contain two
  examples with a non-8 palette and two with multiple repeated classes.
- Row-major first-object role alternates by `sample_index` parity, so every
  four-pair window contains two singleton-first and two repeated-first inputs.

## Audit lead and repair

The repair used the unresolved source-bound audit retained at
`counterexamples/review-9c93d6a9269c5c94-v0001/retained/checks/audit/ae0a295c2271/`
as its lead. Baseline source `3e0743845ba77d040a4b108af6cd6d00eb5614e1dc31b6f1ef5cfe22c4a3b19d`
made the first row-major object a singleton in 300/300 sampled inputs, allowing
an exception rule that forced the first object red.

The repaired placement accepts an explicit lead shape and alternates between a
repeated and singleton class. Executable rivals now include both opposite
first-object exceptions, with matching witnesses. A 300-draw role census gives
150 singleton-first and 150 repeated-first inputs; all 291 measured four-pair
windows satisfy the two-witness redundancy requirement.

## Teaching schedule and failed iteration retained

The first repaired three-profile schedule passed all 300 production lessons but
failed 269/1,200 leave-one-out query rotations: holding out the only non-8 or
only multiple-repeated-class example could leave the palette-only or
only-first-repeated-class rival viable. Version 5 replaces that schedule with a
four-profile cycle containing two independent witnesses for each obligation.
The final census materialized 300 lessons / 1,200 pairs and checked all 1,200
query rotations with zero ambiguity, hook warning, scoring error, or
materialization error (`checks/lesson-census-final-v2.summary.json`).

## Semantic declarations and call contract

`CANONICAL_SHORTCUTS` contains only the color-8-conditioned shortcut, which
fits all eight retained canonical pairs. Other executable hypotheses remain in
`LESSON_COMPETITORS`/`SEMANTIC_RIVALS`; they are partial competitors, not
canonical-equivalent shortcuts. Strict call validation rejects bool/float/string
seeds, bool/negative sample indices, invalid difficulty values, unknown axes,
and out-of-domain overrides.

## Parametric extension

A proposed, non-production extension lives in `workspace/parametric/`:
`shape_equivalence = exact|d4`, with canonical/default `exact`. It instantiates
and executes two Racket programs, chooses one setting once per episode, and uses
three demonstrations that distinguish the selected rule from the alternative.
Final evidence at `checks/parametric/ae0a295c2271-shape-equivalence-v2/` checks
8/8 canonical labels, two four-pair episodes, and all eight query rotations with
zero ambiguity. This prototype does not alter selected authority or approval.

## Validation and limits

- Final strict battery: 12/12 green in `checks/after-final-v2/`.
- Focused patchable suite: 37/37 pass in `checks/focused-tests-final.log`.
- Profile floor: 31/60 exact canonical-profile hits, with easy 9/20, medium
  12/20, hard 10/20.
- Rule smoke: 120/120 applied, 120 mirror-parity checks, zero mismatches/crashes.
- The inherited frozen root fixture is still nonportable: it imports the retired
  `scripts.canonical_profile_gate` namespace and hard-codes
  `/tmp/data/canonical/puzzles.jsonl`. It was not edited; maintainer migration is
  required. New task-local tests remain independently green.
- Finite declared rivals and sampled windows are strong bounded evidence, not a
  universal proof against every possible induction rule.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-9c93d6a9269c5c94:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3e0743845ba77d040a4b108af6cd6d00eb5614e1dc31b6f1ef5cfe22c4a3b19d`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit assessment of old audited source 3e0743845ba77d040a4b108af6cd6d00eb5614e1dc31b6f1ef5cfe22c4a3b19d against accepted current c14282044b5908ab0d49a53920dd5a8c611a3a43156f59fa71c43fe825069071. Placement alternates singleton-first and repeated-first, declares both positional rivals and uses redundant witness profiles. Reported37 focused tests,300 lessons/1200 rotations and exact counterexample regression cover the old first-object exception. Evidence is reviewer-reported from the current return; no owner task rerun.

### Assessment or prior finding

## ae0a295c2271

**Suspected shortcut reproduced: positional exception for the first object.**
The generator's placement routine deliberately pins a singleton shape as the
row-major first object. A probe over seed `918273`, sample indices `0..99` in
each of easy/medium/hard found the first object singleton in **300/300** samples,
with zero generation errors (`checks/audit/ae0a295c2271/sampler_probe.json`).

A rival can therefore apply the intended exact-shape-frequency rule everywhere
except “force the first row-major object red (`2`)”. It agrees with every probed
generated scene because that first object is always genuinely unique.

The retained 10×10 counterexample puts one member of a repeated L-tromino class
first, a second translated copy later, and one unique horizontal triomino. It
passes the target `self_check` with no errors, but the current sampler cannot emit
it because of the first-singleton pin. The canonical Racket rule (hash
`6c9ec74ee7cf`) colors both L objects blue (`1`); the rival wrongly colors the
first L red. Exact input, Racket output, rival output, generator/rule hashes, and
command are in `checks/audit/ae0a295c2271/counterexample.json` and `racket.json`.

This is a generator-support/teaching gap, not a defect in the Racket authority.
No fix was made because this task is audit-only.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-9c93d6a9269c5c94-v0001/audit_assets.json), manifest SHA-256 `1a675591dd79fc46ae8f20f35b457bc9667bfde282777ded2f112bfba5a7b0a9`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `c14282044b5908ab0d49a53920dd5a8c611a3a43156f59fa71c43fe825069071`.

# Decisions for `ae0a295c2271`

## D1 — Preserve the selected Racket authority

**Decision.** Keep the canonical exact-translation shape-frequency rule and
`RULE_HASH = "6c9ec74ee7cf"` unchanged.

**Reason.** The retained counterexample shows a Python sampling/teaching defect,
not a labeling defect. Final rule smoke, mirror parity, Racket lint, and authority
sync all pass.

**Rejected alternative.** Change the Racket rule so the first object is always
red. That would encode the sampler shortcut and contradict a lawful retained
input whose first object belongs to a repeated shape class.

## D2 — Alternate the first semantic role deterministically

**Decision.** Pass an explicit lead shape into placement: repeated on even
`sample_index`, singleton on odd `sample_index`.

**Reason.** Deterministic parity gives measurable coverage and guarantees both
roles in every three-demo window and twice each in every four-pair window.

**Prior choice reversed.** Version 3 always placed the first singleton class
first. The source-bound audit measured 300/300 singleton-first draws.

**Rejected alternative.** Randomize the lead role independently. Randomness
would improve marginal coverage but would not guarantee every lesson refutes
both opposite positional exceptions.

## D3 — Use a four-profile, two-witness curriculum

**Decision.** Cycle through two canonical color-8 profiles and two non-8
profiles. One canonical and one varied profile contain two repeated and two
singleton classes; the other pair preserves the simpler one-pair structure.

**Reason.** Any one held-out query leaves at least one non-8 demonstration and
at least one multiple-repeated-class demonstration. Parity independently leaves
both first-object roles. This closes every measured rotation without changing
the rule.

**Failed alternative retained.** The three-profile cycle passed production order
but failed 269/1,200 query rotations (`checks/lesson-census-final.json`). It had
only one witness for some obligations.

## D4 — Validate call scalars before entering generation context

**Decision.** Require `type(seed) is int`, `type(sample_index) is int`, and
`sample_index >= 0`, plus the declared difficulty and exact override domains.

**Reason.** The strict defect linter demonstrated accepted bool/float/string
seeds and bool/negative indices. Rejecting at the public call boundary makes the
contract deterministic and diagnostic.

**Rejected alternative.** Coerce with `int(...)`. That silently aliases distinct
invalid inputs and makes keyed generation/replay ambiguous.

## D5 — Separate canonical shortcuts from lesson competitors

**Decision.** Keep only `apply_rule_only_when_input_color_is_8` in
`CANONICAL_SHORTCUTS`; retain all executable partial hypotheses in
`LESSON_COMPETITORS` and `SEMANTIC_RIVALS`.

**Reason.** A canonical shortcut must fit every labeled canonical pair. The
other rivals intentionally disagree with some canonical examples, so declaring
them canonical-equivalent made the semantic contract false even though they are
useful generated-lesson competitors.

## D6 — Add exact/D4 equivalence only as a proposed parameter

**Decision.** Implement `shape_equivalence=exact|d4` in
`workspace/parametric/`, with `exact` as default and canonical authority. Bind
one value per episode and execute both instantiated Racket programs.

**Reason.** It is the smallest meaningful rule parameter: it preserves object
roles and frequency reasoning while changing one explicit equivalence relation.
The generated witness family separates the values in every demonstration.

**Rejected alternative.** Wire D4 into production now. The canonical labels and
selected authority specify exact orientation; the prototype is evidence for a
future family, not approval to broaden the current task.

## D7 — Do not patch the frozen inherited fixture

**Decision.** Leave
`test_generator_ae0a295c2271.py` unchanged and report its portable preflight
failure separately.

**Reason.** Packet duties explicitly freeze that fixture. Its legacy `scripts`
import and `/tmp/data` path require maintainer migration. New tests use
`reviewer_support` and pass 37/37.

## D8 — Keep audit targets findings-only

**Decision.** Do not edit `d2f8cb1c91b2` or `66ba1145a9b7`.

**Reason.** The assignment reserves both for adversarial review. Exact probes and
source hashes are retained under `checks/audit/`; the first had no new finding,
and the second has reproducible contract defects for later triage.
