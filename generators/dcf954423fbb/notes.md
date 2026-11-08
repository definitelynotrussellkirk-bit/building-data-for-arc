# Working notes: dcf954423fbb

## Selected baseline and authority

The immutable selected baseline was generator version 1.2.0, SHA-256
`d8029ff4188c5c97b29648ad388508540ebe106fba64d5b42f9d345bea08c6ed`.
Prior return `review-df404da564d3592d:v0001` was used only as a lead; every
claim below was remeasured against the selected source.  The selected Racket
rule remained unchanged.  The generator pins `RULE_HASH = "77b049629337"`.

## Reproduced baseline defects

The completed before battery (`checks/before-complete/`) had five blocking
stages: lint, self-check, defect lint, profile floor, and overrides.  The source
omitted `RULE_HASH`, rejected lawful canonical decoration colors, advertised
four ineffective/overlapping texture choices, ignored `n_blobs`, accepted
unknown controls, and did not expose an executable semantic teaching contract.

## Repair choices

Version 2.0.0 replaced the dead texture surface with three exact observable
axes: `grid_h` 8..10, `grid_w` 10..13, and `n_blobs` 3..6.  It constructs
separated 4-connected blue components at canonical dimensions, includes a
left/right-only border witness, a top/bottom witness, a distance-one interior
decoy, an inward-extending border component, and a preserved decoration.  An
independent oracle/probe in `workspace/semantic_probe.py` checks replay,
validator cleanliness, plausible rivals, and Racket parity.

A first 100-lesson-per-band census was green for the four declared geometric
rivals but a later undeclared-rival self-review found a fixed-count shortcut:
"recolor the two nearest components" survived all 100 easy lessons and was a
genuine demo/query ambiguity in 25 of 100 medium lessons.  Independently,
"recolor the three nearest components" fit all five canonical pairs.  The
reproducer is `checks/fixed-count-shortcut-before.json`.

Version 2.1.0 therefore declares both fixed-count rivals at lesson level and
makes the number of true border components vary in every cyclic three-demo
window.  Default blob-count schedules are now easy 3/4/3/4, medium 3/4/5/3,
hard 4/5/6/6, and unbanded 3/4/5/6; four-blob scenes use a third border
component, five-blob scenes add a deep interior component, and six-blob scenes
add a fourth border component.  This preserves the rule while preventing a
fixed transformed-count curriculum.

## Tests and limits

Focused tests cover canonical acceptance, independent-rule parity, exact and
invalid overrides, deterministic replay, structural witnesses, declared rivals,
all cyclic query starts in every band, malformed grids, hash-seed independence,
and real Racket parity.  The reusable probe now reports lesson-level rival
survival rather than only per-grid witness frequency.

The generated grammar is intentionally narrower than the abstract rule:
8..10 by 10..13 grids, 3..6 blue components of 2..4 cells, and one connected
1..5-cell decoration in color 4, 5, 6, 7, or 9.  Every ordinary draw is highly
pedagogical and therefore more explicit than a natural random scene.  Finite
rival checks do not prove universal identifiability; new data-driven rivals
should be added when they are found.
## Current reviewer considerations

Source SHA-256: `abf44717927649e9efbedb482a956ec612b4f72a349ed74af831b8ead275f524`.

# Decisions: dcf954423fbb

## D1 — Keep the selected Racket authority unchanged

**Input choice.** The label rule remains the selected canonical Racket program,
pinned by `RULE_HASH = "77b049629337"`.

**Original rationale.** Unknown. The selected baseline did not pin the hash, but
its rule smoke and authority synchronization already passed.

**Alternatives considered.** Rewrite or simplify the rule; add a Python rule as
a replacement authority.

**Probe.** Canonical outputs, rule smoke, authority synchronization, and 37-grid
Racket-versus-independent-oracle parity all passed. See
`checks/after-final2/` and `checks/final-semantic-probe-v3.json`.

**Failure mode avoided.** A generator repair should not silently redefine the
ARC task or create a split authority.

**Limitation.** The Python `_apply_rule` and probe oracle are audit mirrors only;
the Racket program remains authoritative.

## D2 — Replace texture with three exact observable axes

**Input choice.** Advertise only `grid_h` 8..10, `grid_w` 10..13, and
`n_blobs` 3..6. Reject unknown, non-integer, and out-of-range overrides.

**Original rationale.** The v1.2.0 `texture` choices had no reliable observable
semantics, `n_blobs` was ignored, height/width controls were not honored, and
unknown keys were accepted.

**Alternatives considered.** Retain texture names and implement four arbitrary
visual styles; keep controls advisory rather than exact; remove overrides
entirely.

**Probe.** The baseline override gate recorded thousands of mismatches and
generation errors. Final exact-control tests span both domain endpoints in all
bands, and the final override stage passes with unknown keys rejected.

**Failure modes.** Exact joint extremes must remain constructible; the tests
cover 8x10/3 blobs and 10x13/6 blobs in every band.

**Limitation.** The axes intentionally describe only measurable task structure,
not every possible aesthetic variation.

## D3 — Use canonical-scale profiles rather than unrestricted dimensions

**Input choice.** Default dimensions cycle through `(8,10)`, `(9,12)`,
`(8,11)`, `(10,13)`, and `(9,12)`.

**Original rationale.** Unknown; the selected baseline missed the canonical
profile floor.

**Alternatives considered.** Uniformly sample every dimension pair; copy one
canonical size only; expand to much larger grids.

**Probe.** Final profile-floor and strict-canonical stages pass in every band;
the independent probe observed four distinct dimension profiles per band.

**Failure modes.** A broad sampler can be technically lawful but never resemble
canonical examples; a single fixed size can invite size-specific shortcuts.

**Limitation.** The grammar does not test scale generalization outside 8..10 by
10..13.

## D4 — Construct separated small components by semantic roles

**Input choice.** Build 3..6 separated 4-connected color-1 components from a
small dihedral shape vocabulary. Base roles include one left/right-only border
component, one top/bottom border component, and one distance-one interior
component; higher counts add another border component, a deep interior
component, and a fourth-side border component.

**Original rationale.** Unknown. The baseline distribution did not reliably
exercise all sides or distinguish whole-component recoloring from literal
border-cell recoloring.

**Alternatives considered.** Random walk blobs with rejection; single cells;
allow touching blobs and recover components afterward; corner-only contacts.

**Probe.** Constructive placement was exercised across exact joint override
extremes and 400 default draws. All four sides appeared in every band, every
border component extended inward, and no draw failed validation.

**Failure modes.** Adjacent nominal blobs can merge; corner components can blur
which side matters; border-only single cells fail to teach whole-component
propagation. One-cell blue components are therefore excluded.

**Limitation.** Blue components have only 2..4 cells, so large or highly
irregular connected objects are not represented.

## D5 — Always include a near-border interior decoy

**Input choice.** Every ordinary grid includes a fully interior blue component
whose minimum border distance is exactly one.

**Original rationale.** Canonical examples are answer-equivalent under the
plausible shortcut “distance at most one counts as touching.”

**Alternatives considered.** Rely on occasional random interior blobs; include
only deep interior examples; declare the shortcut without forcing a witness.

**Probe.** `near_border_recolors` fits all 5 canonical pairs but is refuted on
400/400 independent draws and 100/100 production lessons in every band.

**Failure mode.** A model can otherwise learn a one-cell border halo instead of
literal contact.

**Limitation.** Because the decoy is mandatory, the generated distribution is
more didactic than an unconstrained natural scene.

## D6 — Vary transformed-component counts within every lesson window

**Input choice.** Version 2.1 uses default blob schedules easy `3/4/3/4`, medium
`3/4/5/3`, hard `4/5/6/6`, and unbanded `3/4/5/6`. Four-blob scenes contain
three true border components; five-blob scenes contain three; six-blob scenes
contain four.

**Original rationale.** This is a new repair. After an initially green declared-
rival census, an independent rival found that “always recolor two nearest
components” survived 100/100 easy lessons and produced 25/100 demo/query
ambiguities in medium. “Always recolor three nearest” fit all 5 canonical pairs.

**Alternatives considered.** Merely declare the rivals; add a single hard-band
counterexample; increase lesson length; randomize border count without a cyclic
guarantee.

**Probe.** The exact reproducer is `checks/fixed-count-shortcut-before.json`.
After repair, all 64 cyclic three-demo windows in the reusable probe have zero
survivors, and both fixed-count rivals are refuted in 100/100 production lessons
per band.

**Failure modes.** Per-grid witness frequency does not imply each assembled
lesson contains the witness. The deterministic schedules are designed so every
cyclic three-example window changes the true transformed count.

**Limitation.** Count variation is structured and periodic; a more general
shared gate should search additional count/size/rank shortcut families.

## D7 — Keep decoration semantically inert but palette-compatible

**Input choice.** Add exactly one connected 1..5-cell decoration component in
color 4, 5, 6, 7, or 9, preserving it in the output.

**Original rationale.** The baseline validator incorrectly rejected canonical
non-7 decorations, while unrelated colors are part of the task's visual
context.

**Alternatives considered.** No decoration; multiple decoration colors; allow
color 2 in inputs.

**Probe.** All five canonical inputs pass `self_check`; final strict and palette
checks pass. Decoration placement falls back to smaller connected shapes only
when a dense scene has no room for the requested shape.

**Failure modes.** Multiple same-color decoration components or input color 2
could confuse object counting and input/output roles.

**Limitation.** Exactly one decoration object is narrower than the abstract
rule, which would tolerate arbitrary unrelated colors.

## D8 — Make semantic claims executable

**Input choice.** Declare six semantic rivals and six source-bound witnesses:
side-only contact, near-border interior, inward extension, preserved interior,
border count not two, and border count not three. `lesson_identifiable` rejects
any lesson whose demonstrations allow a declared rival to survive.

**Original rationale.** The baseline had no executable semantic contract.

**Alternatives considered.** Put rival descriptions only in prose; test only
canonical pairs; use the generator's own rule implementation as the sole oracle.

**Probe.** The strict semantic gate verifies all witnesses and rival claims;
production census verifies every declared rival over 300 lessons. The reusable
`workspace/semantic_probe.py` independently computes components and Racket
parity.

**Failure modes.** Declaring a canonical shortcut without a generated witness
caused the intermediate semantic-gate warning retained under
`checks/after-final/`; count witnesses fixed it.

**Limitation.** The rival set is finite. New shortcuts should be added when
model errors or adversarial search reveal them.

## D9 — Preserve a baseline copy and reusable probe in workspace

**Input choice.** Keep `workspace/generator-v1.2.0-baseline.py` and the
independent `workspace/semantic_probe.py` in the selected task delta.

**Original rationale.** The packet has a frozen baseline, but a local readable
copy makes the failure reproducer and future rival development easier without
reconstructing source from evidence.

**Alternatives considered.** Report only; tests that import production helpers;
remove the copy to minimize patch size.

**Probe.** The probe is itself covered by a red/green test and its final CLI run
records source/probe hashes, 400 draws, 64 lesson windows, and Racket parity.

**Failure mode.** A probe that reuses production component logic can reproduce
the same defect and create false confidence.

**Limitation.** The baseline copy is historical and must never be imported as
the selected generator.
