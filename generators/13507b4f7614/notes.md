# Working notes: 13507b4f7614

## Native parametric join family (current reviewer work)

`workspace/parametric/adapter.py` adds the private, episode-fixed
`join_axis=none|horizontal|vertical`. The default program is the exact selected
canonical source. Alternate programs join every eligible original solid yellow
rectangle pair across a one-cell gap, then recompute components and execute the
canonical odd-by-odd center-cross rule. Production `generator.py` and all
canonical bytes stay unchanged; native reviewer qualification and owner
acceptance remain separate.

The intermediate changes membership and parity: two even-width pieces can form
an odd-width cross, while three even-width pieces form an even rectangle left
solid. Constructive examples teach both outcomes, repeated joins, multiple
independent groups and mixed-parity guards within the first two demonstrations.
Requests support 2–6 demos (default three), independently 1–4 novel queries
(training four); inputs are setting-independent and count-prefix stable.
The separate parametric grammar has 6–12 input rectangles and 16×16 through
30×30 canvases. Its maximum query has substantial content in every quadrant and
contacts all four edges. The original sampler's smaller grammar is unchanged.

Self-review found and repaired a real hole before qualification: a Racket rival
joining only the first pair fit the first two demonstrations yet differed by
31 cells on a longer query chain. The earlier design used only pairs in short
lessons. It now teaches three-part chains and two independent groups in the
second example, preserving the two-demo minimum. Nine finite rival families,
including first-pair, first-group, height-only and width-only shortcuts, are
executed on the retained episodes. This is bounded evidence, not universal
identifiability. `checks/13507b4f7614/self-review-before.json` retains the minimal
pre-repair failure; final private teaching certificates retain the repair.

The selected production sampler still has its inherited unresolved scalar
validation audit; it is not silently closed. A new source inspection also finds
its parity choices are coupled, so height-only/width-only guards fit that sampled
support. The parametric grammar fixes that teaching gap with mixed parity while
preserving the approved production source for native qualification.

See `workspace/parametric/README.md` for reproduction and the public/private
consumer contract. Full dataset challenges are controller-owned;
`build_evidence.observation(episode, index)` emits only one query per turn with
no count/future-input hints. All query answers, programs and settings stay private.

## Intended rule and authority

The selected Racket authority, pinned by `RULE_HASH = "812105731900"`, replaces
each solid color-4 rectangle with its middle row plus middle column **only when
both rectangle dimensions are odd**. A rectangle with an even height or width is
left unchanged. The Racket authority and canonical data were not edited in this
review.

Final generator SHA-256:
`fb2750a16ab6e2c12a10f0cd30f6526e411213043857f8ff2680ac4864831a77`.

## Reversed baseline choices

The selected v1.3.1 baseline exposed many nominal controls and negative fixtures
as ordinary axes. In particular, `texture=hollow_rect` violated the stated solid-
rectangle grammar while passing `self_check`; `n_rects` and `palette_kind` were
inert in measured combinations; unknown overrides were accepted; the hard band
had zero canonical-profile hits in the pinned 20-draw check; and there was no
executable semantic contract. The before battery recorded 4 failed stages and 2
advisories. These choices were removed rather than preserved as misleading API.

Version 2.0.0 advertises one exact, observable axis: `grid_profile`. It selects one
of six named canvas shapes, including all three canonical profiles. Unknown or
retired overrides fail closed. Internal scene variation is deliberately not
advertised as an exact override.

## Current input grammar

- Canvas profile: canonical 9x12, 11x11, or 12x13; or wider/taller 10x16,
  16x10, or 16x18 generalization profiles.
- Two or three separated solid color-4 rectangles on background 0.
- Rectangle dimensions are 2..7, with a one-cell canvas margin and at least one
  blank cell between components.
- Every input has at least one odd-by-odd rectangle.
- A deterministic four-scene schedule cycles through `odd_two`, `mixed_two`,
  `odd_three`, and `mixed_three`. Mixed scenes contain an even-dimension rectangle
  that remains unchanged under the authority.

`self_check` now verifies rectangularity, palette, component count, solidity,
dimensions, margins, separation, and presence of an odd-by-odd rectangle. It
rejects blank, hollow, punctured, wrong-palette, touching, and parity-hidden
impostors.

## Teaching contract

The strongest canonical-fitting shortcut found is
`reduce_even_rectangles_too`: replace every rectangle by a center cross and
ignore the odd-dimension guard. It fits all three canonical pairs because those
pairs contain only odd-by-odd rectangles. The generator declares that rival and
the structural witness `even_rectangle_unchanged`.

Lessons use three demonstrations from a four-scene period. Two of every four
scenes are mixed, so every cyclic start and every single query holdout leaves at
least one mixed demonstration. The source-bound Racket census materialized 300
lessons (100 per band), 1,200 pairs and 1,200 query rotations, with 1,106 unique
inputs and zero declared-rival ambiguities or hook/scoring errors. The task-local
probe exhaustively checked all 48 band/start/query rotations and all 18 exact
profile/band combinations.

## Verification and limits

The final battery is 12/12 green, the portable task-test stage is 19/19 green,
and the required-rotation semantic stage passes. The post-repair visible-only
solve passed all 3 demonstrations in one revision; earlier rule exposure was
reported honestly and no reference was consulted during that solve.

The generated grammar is intentionally narrower than the full abstract input
space: only background 0, foreground 4, separated solid rectangles, sizes 2..7,
and the six named canvas profiles are produced. Finite tests establish support
against the declared rival, not unique induction against every imaginable rule.
Future model failures should be converted into new source-bound rivals and
witnesses rather than treated as proof that this finite contract is complete.
## Current reviewer considerations

Source SHA-256: `fb2750a16ab6e2c12a10f0cd30f6526e411213043857f8ff2680ac4864831a77`.

# Decisions: 13507b4f7614

## D1 — Keep the selected Racket authority unchanged

**Choice.** Preserve the canonical rule and data; pin
`RULE_HASH = "812105731900"` in the generator.

**Rationale.** Baseline rule smoke and authority synchronization already passed,
and direct canonical comparison showed the defect was in sampling, validation,
and public metadata rather than labels.

**Alternatives considered.** Rewrite the Racket rule; reinterpret hollow
rectangles or even rectangles as lawful ordinary inputs.

**Evidence and failure mode.** Final rule smoke, Racket lint, and authority sync
all pass. Rewriting the rule would silently change the task to accommodate a
bad generator fixture.

## D2 — Replace the broad legacy axis surface with one exact profile axis

**Choice.** Advertise only `grid_profile`, with six exact values mapping one-to-
one to canvas dimensions. Reject unknown, retired, or invalid overrides.

**Prior choice reversed.** The baseline exposed grid dimensions, rectangle count,
palette, density, and texture controls, including negative fixtures. Measured
combinations were inert, range-inconsistent, or unlawful.

**Alternatives considered.** Repair every legacy aesthetic control; retain
negative textures as ordinary axes; remove all controls.

**Evidence and failure mode.** The before override gate found 6,990 issues. The
final override stage and 18-case profile/band probe pass. A small truthful API is
preferable to a wide contract that cannot be observed or honored.

**Limitation.** Object count and parity mix are scheduled internal curriculum
choices, not caller-controlled exact axes.

## D3 — Construct scenes from four separated slots

**Choice.** Divide the canvas into four interior bands separated by guaranteed
blank coordinates; place two or three solid rectangles in distinct slots.
Rectangle dimensions are selected by requested odd/even parity from 2..7.

**Rationale.** Constructive separation prevents merged components and makes
geometry validation deterministic. It supports all six canvases without retry
loops or hidden incompatibility tables.

**Alternatives considered.** Random placement with rejection; allow touching or
overlapping rectangles; use only canonical dimensions.

**Failure modes.** Touching objects collapse into one component; rectangles on
the edge weaken bounding-box reasoning; unrestricted sizes can make small
profiles infeasible. The final grammar enforces a one-cell canvas margin and at
least one blank cell between components.

**Limitation.** The arrangement is pedagogical and more regular than arbitrary
lawful rectangle scenes.

## D4 — Teach the hidden odd-dimension guard with a four-scene schedule

**Choice.** Cycle `odd_two`, `mixed_two`, `odd_three`, `mixed_three`; set
`EXAMPLES_NEEDED = 3`.

**Rationale.** All canonical pairs contain only odd-by-odd rectangles, so the
plausible shortcut “reduce every rectangle” fits them. Mixed scenes supply the
counterexample: an even-dimension rectangle stays unchanged.

**Alternatives considered.** Randomly include even rectangles; require one mixed
scene only at a fixed lesson position; increase lesson length.

**Evidence and failure mode.** Two mixed scenes per four-item period ensure that
any single holdout leaves a mixed demonstration. Required-rotation semantic
checks, a 300-lesson Racket census, and exhaustive 48-rotation local probe pass.
Random inclusion would not guarantee a witness in every assembled lesson.

## D5 — Make `self_check` enforce the actual task grammar

**Choice.** Validate rectangular shape, integer palette {0,4}, 1..3 connected
components, solid rectangle occupancy, dimensions 2..7, one-cell margins,
component separation, and at least one odd-by-odd rectangle.

**Prior choice reversed.** The baseline acceptance-only validator rejected none
of 45 destructive mutations and accepted blank, hollow, and parity-hidden
fixtures.

**Alternatives considered.** Keep validation permissive and classify bad
textures elsewhere; validate only generated defaults.

**Evidence and failure mode.** Focused tests begin with retained hollow, blank,
wrong-palette, and punctured examples. The final self-check and defect-lint stages
pass with strict rate 600/600.

**Limitation.** The validator intentionally describes this generator's bounded
grammar rather than every grid on which the abstract Racket rule can execute.

## D6 — Preserve canonical-profile support in every difficulty band

**Choice.** Include the three canonical canvas shapes in every band's weighted
profile options, with larger generalization canvases receiving more weight in
hard.

**Rationale.** The baseline hard band had zero canonical-profile support in the
pinned 20-draw check.

**Alternatives considered.** Uniform six-profile sampling; canonical-only sizes;
allow arbitrary dimensions.

**Evidence and failure mode.** Final profile-floor passes. In the independent
100-draw-per-band probe, every canonical profile appears in every band while all
six profiles remain represented overall.

## D7 — Declare one precise rival and keep the claim bounded

**Choice.** Declare `reduce_even_rectangles_too`, witness it with
`even_rectangle_unchanged`, and use the same registry in
`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`.

**Rationale.** This is the strongest simple rule found that fits all canonical
pairs and disagrees on lawful generated inputs.

**Alternatives considered.** Register generic geometric transforms that do not
fit the canonical pairs; claim universal identifiability; leave the issue in
prose only.

**Evidence and failure mode.** The semantic gate verifies canonical fit and
source-bound counterexamples. The census finds no ambiguity against the declared
rival. The report explicitly does not claim completeness against undeclared
hypotheses.

## D8 — Add a reusable qualification probe

**Choice.** Add `workspace/qualification_probe.py`, reading the generator's own
shortcut, competitor, witness, profile, and schedule declarations.

**Rationale.** The shared battery is a broad bounded sample; this four-scene
schedule is small enough to exhaust every cyclic start and query rotation.

**Alternatives considered.** Keep one-off notebook calculations; duplicate rival
names inside the tool; rely on the 12-lesson semantic smoke test.

**Evidence and failure mode.** The tool is covered by a focused test and its final
100-per-band report has zero errors. Reading declarations avoids stale copied
rival lists. It remains a Python-mirror diagnostic and does not replace Racket
labels.

## Current reconciled parametric family

Four join_axis choices are native-qualified and accepted on the current exact source: none (canonical), horizontal, vertical, and cross_area_cascade. The first three programs and samplers remain byte-for-byte/behaviorally preserved. The cascade retains its independent sampler; its explicit guard defines identity outside its original unique-anchor/unique-match grammar. Hidden-rule teaching is checked across all four programs, not inferred from branch names. See `evidence/owner-variant-reconciliation/current.json` and `parametric/accepted.json`; the earlier conflicting raw return remains supplemental. The production generator, canonical rule, and unresolved canonical audit are unchanged. This does not activate training.
