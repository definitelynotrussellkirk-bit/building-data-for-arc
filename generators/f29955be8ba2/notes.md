# Working notes: f29955be8ba2

## 2026-10-03 review `review-aaa85ba03a1bbb23`

No prior return patch was adopted. The current pinned baseline was measured
directly; `b90d4c3d5553` and `3f2ed19e5882` were read only as retained examples
of the current contract style.

### Baseline diagnosis

The v2 generator produced valid rule inputs, but it had no `RULE_HASH`, no
callable `self_check`, no semantic contract, and no exact override observer.
Several declared controls were inert or misleading: `block_h`/`block_w` were
not honored across their advertised domains, helpful texture names did not
change output, and malformed textures overlapped the ordinary texture domain.
The initial aggregate before battery was interrupted after checkpointing lint,
self-check, and rule-smoke evidence; isolated before-stage runs reproduced the
blocking lint, self-check, profile, semantic, override, and defect-lint findings.
The canonical Racket rule itself passed smoke, grammar, Racket lint, and
authority-sync checks, so no authority change was justified.

### Strongest canonical rival

All three usable canonical pairs order source-block foreground colors
monotonically by source position. Therefore the wrong rule “header `1/2/3`
means first/second/third block in ascending foreground-color order” fits every
canonical pair. A generated witness at seed 19, sample index 1, overrides
`block_h=3`, `block_w=7`, `permutation=213`, `palette_profile=varied` has source
colors `(6,4,2)` and refutes that rule. The canonical Racket output and Python
mirror agree; retained evidence is under `checks/shortcut-counterexample/`.

### Repair decisions

- Keep the selected Racket authority byte-for-byte unchanged and pin its hash.
- Expose only four real exact axes: block height 2–5, body width 3–18, all six
  permutations, and three palette profiles.
- Remove ordinary texture axes rather than preserve dead aliases or mix
  malformed cases into the teaching domain.
- Use a non-identity five-permutation ordinary schedule while still accepting
  identity exactly when explicitly overridden.
- Schedule `canonical_low`, `varied`, `canonical_high` in every three samples;
  `varied` is forced non-monotone so every ordinary lesson window contains the
  color-rank counterexample.
- Add two sparse shape anchors per 12 samples for the two canonical
  size/palette profiles without freezing the broader distribution.
- Require three nonempty, non-solid, pairwise-distinct masks and three distinct
  foreground colors, making block identity visually recoverable.
- Add structural analysis, mutation-sensitive validation, exact override
  observation, executable semantic rivals/witnesses, and lesson checking.

### Verification and limits

Final generator SHA-256:
`e21d8f4ee17093011230fa3cddecc7ee18193f3694e01bb449d0cbd1994f22bf`.
The official after battery is 12/12 green, selected task tests are 34/34 green,
rule smoke is 120/120 with 120/120 mirror parity, semantic strict support is
600/600, canonical-profile support is present in every band, and the source-bound
lesson census materialized 100 lessons per band with zero surviving declared
rivals. These finite checks establish the declared contracts and sampled rival
coverage, not universal ARC induction against every conceivable alternative.
## Current reviewer considerations

Source SHA-256: `e21d8f4ee17093011230fa3cddecc7ee18193f3694e01bb449d0cbd1994f22bf`.

# Decisions for `f29955be8ba2`

## D1 — Keep the Racket authority unchanged

**Choice.** Preserve the selected canonical Racket rule and pin
`RULE_HASH = "7f09fab6403a"`.

**Rationale.** Before-repair rule smoke, grammar, Racket lint, and authority sync
passed. The defects were in sampling and contracts, not transformation
semantics.

**Alternative rejected.** Editing the rule to accommodate generator quirks
would have changed the authority without evidence of a rule defect.

**Probe.** Final rule smoke applied 120 generated inputs and found 120/120
Python-mirror matches (`checks/after/checks/f29955be8ba2_after_rule_smoke.json`).

**Limit.** Mirror parity is sampled, though canonical binding is separately
hash-checked.

## D2 — Replace eight misleading axes with four exact observable axes

**Choice.** Publish only `block_h`, `block_w`, `permutation`, and
`palette_profile`.

**Rationale.** These properties are literal in returned pixels and can be
recovered without hidden metadata. This makes override claims falsifiable.

**Alternatives rejected.** Retaining singleton `palette_size`/
`n_distinct_colors`, a vague `density`, or dead texture aliases would preserve
nominal variety without controllable behavior. Keeping malformed textures in
the ordinary domain would conflate teaching inputs with validator negatives.

**Probe.** `observe_overrides` reconstructs every exact value; boundary,
invalid-input, and mutation tests are in
`repo/generators/f29955be8ba2/tests/test_generator.py`. The official override
gate is green at `checks/after/checks/f29955be8ba2_after_override.log`.

**Limit.** Sparse-mask density is intentionally internal rather than promised as
an exact public control.

## D3 — Use non-identity ordinary permutations, but honor explicit identity

**Choice.** Ordinary draws cycle through `132,231,213,312,321`; an explicit
`permutation="123"` remains valid and exact.

**Rationale.** A default identity instance does not visibly teach reordering,
while exact override semantics require the full rule domain.

**Alternative rejected.** Banning identity entirely would narrow the lawful task
domain and make the advertised six-permutation axis false.

**Probe.** `strict_canonical_like` rejects identity as a teaching draw, while
`self_check` accepts it structurally and override tests recover it exactly.

**Limit.** The default distribution intentionally differs from a uniform draw
over all six permutations.

## D4 — Schedule a non-monotone palette witness every three samples

**Choice.** Cycle `canonical_low → varied → canonical_high`; force `varied`
source colors to be non-monotone.

**Rationale.** Every usable canonical demonstration has foreground colors
ascending with source-block position. Thus a solver can wrongly interpret
header numbers as color ranks. Non-monotone colors separate rank from position
without changing the intended rule.

**Alternatives rejected.** Merely expanding the random palette without a
schedule could leave complete lessons accidentally monotone. Randomly shuffling
canonical profiles would not guarantee a witness in each three-example window.

**Probe.** The exact generated witness and canonical Racket receipt are in
`checks/shortcut-counterexample/`; all 300 source-bound census lessons refute
the rival (`checks/lesson-census-summary.json` (full lossless evidence: `checks/lesson-census.json.gz`)).

**Limit.** The schedule is deterministic by sample index, which is transparent
and testable but not IID.

## D5 — Add sparse canonical-profile anchors

**Choice.** At sample-index residues 0 and 5 modulo 12, use body sizes 3×7 and
3×8; combined with the palette schedule these realize canonical profiles
9×8/palette 5 and 9×9/palette 7.

**Rationale.** Canonical scale should remain represented in every difficulty
band, but most draws should still explore broader legal dimensions.

**Alternatives rejected.** Fixing all draws to canonical dimensions would erase
useful geometry coverage. Relying on chance failed the baseline profile gate.

**Probe.** The final profile floor reports exact hits easy 7/20, medium 1/20,
hard 4/20, with zero crashes.

**Limit.** Medium support is deliberately sparse (1/20 in the pinned audit), so
future changes to schedules should retain an explicit floor test.

## D6 — Require distinguishable block contents

**Choice.** Each block is nonempty, non-solid, single-color, and uses a mask
distinct from the other two; all three foreground colors are distinct.

**Rationale.** The task is about reordering whole blocks. Identical/empty blocks
can make different permutations observationally equivalent and weaken teaching
signals.

**Alternative rejected.** Allowing arbitrary Bernoulli masks without constructive
checks risks duplicates, empty blocks, or fully filled rectangles.

**Probe.** The generator constructs masks with anchored cells and bounded
occupancy; `self_check` rejects targeted empty, solid/multicolor,
duplicate-color, and duplicate-mask mutations. Diversity and self-check gates
are green.

**Limit.** The masks are not intended to span every possible binary pattern.

## D7 — Make semantic claims executable

**Choice.** Add a Python rule mirror, two rivals, two witnesses, explicit
witness-to-rival mappings, and `lesson_identifiable`.

**Rationale.** Prose claims cannot establish that a complete lesson refutes a
shortcut. Executable contracts let the shared gate and census score actual
predictions.

**Alternative rejected.** Witness-frequency checks alone were insufficient:
a witness name must correspond to an output disagreement. A regression test was
added after an intermediate overbroad witness produced only 36/60 disagreements.

**Probe.** The final task suite includes
`test_every_declared_witness_rival_claim_is_true_when_the_witness_fires`; the
semantic gate is clean and the lesson census has no surviving rival.

**Limit.** The rival set is finite and task-specific, not an exhaustive program
search.
