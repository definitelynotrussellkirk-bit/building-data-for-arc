# Working notes: 95fb3503a9be

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-09-28 review-c4014dc571c9792f

- The inherited 3.0.0 generator passed its battery, but a 2,000-scene census
  found that every generated input consisted of exactly three disjoint occupied
  column runs. All five canonical inputs instead have overlapping component
  bbox column ranges, so a vertical-band parser was a reproducible shortcut.
- The declared size-four line shape was unreachable: no generated crop was
  four columns wide, although two canonical demonstrations contain a 1x4 bar.
- Version 3.1.0 makes schedule cell 1 use a 2x3 rectangle, 3x3 plus, and
  horizontal 1x4 bar in a two-dimensional layout with overlapping column
  projections. The old shortcut is retained as a named semantic competitor.
- Unknown override names now fail closed instead of being silently ignored.
- The first 3.1.0 after-battery exposed a contract integration error: semantic
  rivals were private (`_LESSON_COMPETITORS`), so all seven witnesses were
  reported WEAK under strict policy. Public `SEMANTIC_RIVALS`,
  `LESSON_COMPETITORS`, and `WITNESS_RIVALS` now bind eight witnesses to
  executable wrong rules; the strict gate verified all eight claims.
- `workspace/relation_support_census.py` is a reusable matched baseline/candidate
  probe. At 500 seeds × four schedule cells × three bands, the baseline had
  0/6,000 overlap scenes, 0/6,000 width-four crops, and no counterexample to
  either shortcut. The candidate has 1,500/6,000 of each and covers both in
  every one of 1,500 four-sample lessons.
## Current reviewer considerations

Source SHA-256: `71053fe0c21cc2c1b0d291a069bf6ce7d1f50e1b755b4b5fe2aad23b211d192d`.

# Decisions for 95fb3503a9be

## D1 — Keep the selected rule and Racket authority unchanged

**Input choice.** Treat every monochrome 4-connected nonzero component as an object; crop true bounding boxes; sort by cell count descending and color ascending on ties; pack top-aligned with one zero separator column.

**Original rationale.** This is explicit in the canonical written solution, all five canonical pairs, the selected Racket program, and the inherited Python mirror. The inherited generator already reproduced the rule correctly.

**Alternatives considered.** Change the Racket implementation or reinterpret objects as occupied column bands. Both were rejected: canonical outputs already match the authority, and a column-band interpretation fails canonical geometry.

**Probe.** Canonical tests and official rule smoke: 5/5 canonical Python mirror matches and 120/120 generated Racket/Python mirror matches.

**Failure modes / limitations.** The Racket BFS/path machinery is irrelevant to this task; no authority change was warranted. Python mirror correctness is still anchored by finite canonical and generated parity checks.

## D2 — Put canonical relational geometry into one deterministic schedule cell

**Input choice.** In schedule cell 1, place a 2×3 rectangle and horizontal 1×4 bar in overlapping column projections, separated vertically, with a 3×3 plus at the left.

**Original rationale.** The inherited schedule intentionally used four cells to teach distinct semantic branches, but its placement algorithm always allocated independent x-slots. The exact reason for excluding 2D overlap is not recorded; it appears to be a convenience of constructive placement rather than a semantic requirement.

**Alternatives considered.** Randomly allow overlaps in column projection; redesign all four cells; place components in overlapping rows instead; inject literal canonical layouts. Random support was rejected because a four-example lesson could miss it. Redesigning every cell would reduce diversity and create unnecessary source drift. Row overlap does not defeat the observed x-band parser. Literal canonical copies would leak fixtures and reduce generality.

**Probes.** A 6,000-scene matched census and complete-lesson coverage test. Candidate: 1,500 overlap scenes and 1,500/1,500 lessons covered; baseline: zero of each. The `column_bands` rival differs on all 1,500 repaired cells.

**Failure modes / limitations.** A sampler that does not preserve consecutive four-cell lessons may lose the guarantee. The coarse mode-1 layout is intentionally fixed, so uniqueness comes mainly from dimensions, margins, and colors in that cell.

## D3 — Make the horizontal 1×4 canonical crop reachable

**Input choice.** Emit the declared four-cell line horizontally in schedule cell 1 instead of sending it through the general orientation sampler capped at width three.

**Original rationale.** The inherited shape table already contained the line, indicating intended support, but the width cap made the canonical orientation dead code. No rationale for that contradiction was recorded.

**Alternatives considered.** Raise `max_width` globally; add an additional random branch; delete width-four support as incidental. A global cap change could alter every schedule cell and reduce packing safety. A random branch could be absent from a lesson. Deletion would preserve a measured canonical support gap.

**Probes.** Canonical inputs contain width-four crops in 2/5 cases. Baseline generated 0/6,000; candidate 1,500/6,000 and every four-sample lesson contains one. The `crop_width_three` rival differs on all repaired cells.

**Failure modes / limitations.** Width four is a support anchor, not the transformation rule. The witness is therefore bound to an executable clipping rival rather than treated as an unconditional morphology target for every scene.

## D4 — Reject unknown override names before generation

**Input choice.** Compute `set(overrides) - set(AXES)` and raise `TypeError` when nonempty.

**Original rationale.** The inherited `**overrides` API was permissive; no explicit rationale was recorded. The override contract showed that permissiveness made misspelled axes indistinguishable from successful controls.

**Alternatives considered.** Let `GenCtx` ignore unknown keys; warn and continue; add every semantic schedule choice as an axis. Silent acceptance was the defect. Warnings are easy to miss in batch generation. The schedule is a versioned curriculum, not an independently supported exact axis.

**Probes.** Red/green test with `grid_width=12`; official override stage changed from advisory to green over 1,800 accepted legal draws and 20 cases.

**Failure modes / limitations.** This validates names, while `GenCtx` remains responsible for value/domain validation. The generator still uses legacy-compatible multi-axis policy because its two declared dimension axes are mutually compatible.

## D5 — Publish executable rivals and bind every semantic witness

**Input choice.** Expose nine rivals in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`; map all eight witnesses through `WITNESS_RIVALS`.

**Original rationale.** The inherited generator had useful witness predicates and private lesson competitors, but the public semantic gate could only see feature presence. The first candidate retained that integration mistake and strict policy correctly failed it.

**Alternatives considered.** Mark witnesses as branch-only; remove witnesses; leave private competitors and document them. These alternatives would make the gate weaker or non-machine-verifiable. The chosen contract lets the authoritative Racket oracle test actual output disagreement.

**Probes.** A 384-scene focused test asserts every firing has at least one named disagreeing rival. The official gate checked 60 authoritative cases per witness claim: 8/8 verified, no violations, 12/12 lessons identifiable.

**Failure modes / limitations.** The named rival library is not exhaustive. Future model errors should be added as executable rivals and schedule support rechecked.

## D6 — Preserve the four-cell semantic schedule and broad canonical envelope

**Input choice.** Keep dimensions 9..11 by 11..14, three distinct colors, object sizes 3..7, four scheduled semantic profiles, and nonrectangular crop support.

**Original rationale.** These choices already gave strong rule coverage, high diversity, exact canonical-profile support, and valid Racket outputs. The review found relational gaps, not a need to replace the whole distribution.

**Alternatives considered.** Sample arbitrary object counts/sizes; make all draws exactly canonical 5/5/4; use purely random profiles. Arbitrary profiles expand scope without evidence. Canonical-only profiles would overfit. Pure randomness can produce lesson-level semantic droughts.

**Probes.** Final profile floor: 25/60 exact and 60/60 envelope. Diversity: 99% unique inputs, 86% unique outputs, 10 colors. Strict canonical rate: 142/600, above the declared 20% floor.

**Failure modes / limitations.** The scheduled profiles are deliberately finite. They teach known distinctions but cannot guarantee robustness to every connected polyomino or object count.

## D7 — Add a lesson-level canonical relation-support census

**Input choice.** Build `workspace/relation_support_census.py` to compare baseline and candidate, run two concrete shortcuts, and judge every complete four-sample lesson.

**Original rationale.** Existing morphology marginals passed while the baseline had a universal relational artifact. A reusable measurement is more valuable than leaving the finding only in prose.

**Alternatives considered.** Add task-specific assertions only; modify shared gates in this review; rely on visual inspection. Tests protect this generator but do not quantify baseline/candidate drift. Shared-tool changes are outside the selected task scope. Visual review is not reproducible.

**Probes.** Tool unit tests pass, and the 12,000-scene matched baseline/candidate run wrote `checks/relation-support-census.json` with no candidate failures.

**Failure modes / limitations.** The current policy is task-specific and uses two hand-selected relations. `QUESTION_ANSWER.md` proposes how to generalize the idea without treating every canonical coincidence as mandatory.
