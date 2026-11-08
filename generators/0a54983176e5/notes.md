# Working notes: 0a54983176e5

## Review repair `review-41de4f2ccdbecacf`

Baseline source SHA-256 was
`ff5457c0e35d8b762f8c1357f991bf8dc7d1cf1219498d23ebd9b3739bc28d67`.
The retained prior audit in `evidence/review_index.json` was used only as a lead;
all findings were reproduced against the selected baseline. The before battery
recorded 7 green, 2 advisory and 3 failed stages. The blocking defects were an
unpinned rule hash, advertised texture values rejected by `self_check`, and a
broken exact-control contract (3,063 findings across 29,340 override draws).
Canonical-scale support was only 1/60 exact and 1/60 in-envelope, and there was
no executable semantic contract.

The selected `3.0.0` repair:

- pins `RULE_HASH = "e266f9b65f93"` and leaves the canonical/Racket authority unchanged;
- honors every declared dimension/orientation override in every difficulty band,
  rejects unknown keys, and removes invalid degenerate textures from the domain;
- anchors ordinary sampling to the three canonical size/palette profiles while
  retaining the full declared dimension range;
- exposes pure-Python rule, observables, strict validator, two canonical-fitting
  rivals, paired witnesses, and `lesson_identifiable`;
- schedules `both_sides` and `clip` in every three consecutive examples so the
  overwrite and geometric-center shortcuts cannot survive a normal lesson;
- adds focused regression tests and a declaration-driven cyclic-window probe in
  `workspace/semantic_window_probe.py`.

Final generator SHA-256 is
`63431735aebb18e582a5a8ce9ccdc2cfc8cbb53f3c70513b1e2ecc48adb2979e`.
The final battery is 12/12 green, portable task tests are 32/32, the Racket-backed
lesson census has 300/300 identifiable lessons and 1,200 unique inputs, and the
local window probe has 432/432 passing windows (864 rival evaluations).

Limits: the rival set is finite, canonical-weighted dimensions intentionally do
not sample the full exact-control range uniformly, and deterministic scheduling
establishes coverage only for the declared competitors. It is not a proof that
no other wrong rule can fit the generated lessons.
## Current reviewer considerations

Source SHA-256: `63431735aebb18e582a5a8ce9ccdc2cfc8cbb53f3c70513b1e2ecc48adb2979e`.

# Decisions for `0a54983176e5`

## D1 — Preserve the selected rule; pin its identity

**Original state/rationale:** the Python generator described the intended rule
but did not declare `RULE_HASH`; no evidence justified changing the canonical
Racket authority. **Decision:** set `RULE_HASH = "e266f9b65f93"`, implement a
pure-Python mirror for testing, and leave all canonical/base authority files
byte-identical. **Alternatives rejected:** changing Racket to fit generator
quirks, or omitting the pin. **Probe:** rule smoke, Racket lint, authority sync,
and 3/3 canonical Python parity. **Failure mode:** any future authority edit must
update the pin and rerun all source-bound checks.

## D2 — Make every declared exact control total and observable

**Original state/rationale:** AXES advertised heights 5..14 and widths 7..16,
but difficulty-local `draw_int` ranges rejected many endpoints; unknown keys
were silently accepted. The prior audit supplied a lead, but the packet baseline
reproduced it independently. **Decision:** use complete choice domains in every
band, observe dimensions/orientation from pixels, and reject unknown keys before
sampling. **Alternatives rejected:** narrowing AXES to old local ranges (would
hide rather than repair the contract), or declaring dozens of band-specific
incompatibilities. **Probe:** endpoint tests across 3 bands × 2 heights × 2
widths × 2 orientations and the exhaustive override gate. **Failure mode:** a new
axis without an observer can again become inert or silently ignored.

## D3 — Advertise only lawful textures

**Original state/rationale:** `no_axis` and `no_content` were listed as valid but
necessarily rejected by `self_check`, producing a texture-domain contradiction.
**Decision:** remove those values and keep `plain`, `both_sides`, `clip`,
`on_axis`, and `dense`, each with a positive rule-relevant contract.
**Alternative rejected:** weakening `self_check` to accept examples that cannot
teach the rule. **Probe:** defect lint plus per-texture witness tests. **Failure
mode:** adding a caller-only degenerate to `AXES` will make the exact-control gate
correctly fail unless it is explicitly modeled as incompatible.

## D4 — Weight ordinary sampling toward canonical profiles without shrinking controls

**Original state/rationale:** only 1/60 baseline draws exactly matched a canonical
height/width/palette profile and medium/hard had zero support. The original
reason for the broad near-uniform ranges was not recorded. **Decision:** retain
all exact dimensions but weight ordinary heights toward 6/7 and widths toward
9/10/11; use one or two content colors so total palettes align with the three
canonical profiles. **Alternatives rejected:** hard-locking all draws to the
three canonical shapes (too restrictive), or retaining the old distribution
(profile floor remained weak). **Probe:** profile floor and focused 24-draw
per-band regression. **Failure mode:** weighted support is not uniform coverage;
downstream consumers needing balanced dimensions should request exact overrides.

## D5 — Guarantee lesson-level counterexamples, not just pooled witness frequency

**Original state/rationale:** the canonical pairs admit two wrong rules:
reflecting about the geometric center and overwriting occupied targets. Baseline
occasionally contained blocking examples but had no lesson contract and no
reliable off-center schedule. **Decision:** set `EXAMPLES_NEEDED = 3`; every
three consecutive indices contain `both_sides` and `clip`, while the third slot
rotates through ordinary profiles. **Alternatives rejected:** independent random
texture draws (nonzero witness frequency still permits witness-free lessons), or
forcing every single pair to contain every witness (less diverse and visually
busy). **Probe:** 300 Racket-backed lessons plus 432 declaration-driven windows.
**Failure mode:** a downstream sampler that assembles nonconsecutive demos can
break this guarantee; it should run the lesson hook after assembly.

## D6 — Declare only rivals demonstrated to fit all canonical pairs

**Original state/rationale:** no executable rivals existed. **Decision:** declare
`use_grid_center_axis` and `overwrite_occupied_target` in
`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`, and bind them
to visible-pixel witnesses. Both fit 3/3 canonical pairs. **Alternatives
rejected:** a long speculative rival list with no canonical-fit proof, and only
human prose. **Probe:** focused canonical-fit test, semantic gate, and the
window probe, which iterates the declarations rather than copying names.
**Failure mode:** undeclared plausible rules remain outside this proof.

## D7 — Use one strict grammar for canonical and generated inputs

**Original state/rationale:** validation did not fully state axis geometry,
visible reflection support, override realization, or horizontal single-marker
ambiguity. **Decision:** derive `_axis_facts` from pixels; require rectangular ARC
colors, one coherent marker row/column, 1–3 markers (at least 2 for a horizontal
axis), background, content, and at least one visible empty reflection target.
`strict_canonical_like` delegates to this grammar. **Alternative rejected:**
separate permissive validators that could drift. **Probe:** 3/3 canonical
acceptance, 600/600 strict generated draws, grammar gate. **Failure mode:** this
is intentionally a generated-distribution grammar, not a claim that every
mathematically solvable edge case should be trainable.

## D8 — Add task-local tests and a reusable window probe

**Original state/rationale:** no selected-task tests existed. **Decision:** add
32 focused tests and `workspace/semantic_window_probe.py`. The probe reads the
actual rival declarations, canonical pairs, `EXAMPLES_NEEDED`, and lesson hook.
**Alternatives rejected:** relying only on the 12-stage battery, whose lesson
sample is deliberately small, or hard-coding rival names in a one-off script.
**Probe:** red logs in `checks/tdd/`, portable task-test receipt, and
`checks/0a54983176e5_semantic_window_probe.json`. **Failure mode:** the Python
probe is cheaper but not an authority substitute; final labels still need the
Racket-backed census.

## D9 — Do not modify shared tools or audit targets in the task patch

The repair stays inside the assigned generator's allowed source tree. General
improvements are documented in `FEEDBACK_TO_CODEX.md`; audit targets
`978ea94724d3` and `10fa03869a44` were inspected and left unchanged.
