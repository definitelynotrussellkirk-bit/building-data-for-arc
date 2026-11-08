# Working notes: 7e7614405852

## Baseline

No prior retained return or associated design note was available as a lead;
`evidence/associated_notes.jsonl` was empty. The canonical Racket authority and
all canonical outputs were healthy, so the repair stayed in the generator and
tests.

Baseline battery blockers:

- missing `RULE_HASH`;
- dead/overlapping texture branches and decorative axes;
- exact controls ignored, silently narrowed by difficulty, or accepted under
  unknown names;
- a weak validator that only looked for one exact triple;
- no executable semantic rivals or witnesses.

## Repair

Version `2.0.0` uses a constructive row-run packer with exact public axes
`grid_h`, `grid_w`, `n_len2`, `n_len3`, `n_len4`, `n_len5`, and
`n_vertical3`. Each nonzero object gets a distinct source color, which makes the
axis observer and strict grammar unambiguous. Exact overrides are type/range
checked and unknown keys fail loudly.

Ordinary draws include a length-5 horizontal run and a vertical length-3
object. Declared rivals model three plausible bad rules: mark every horizontal
run of length at least three, mark every odd horizontal run, and mark exact
triples in both orientations. The lesson hook rejects any demonstration set in
which one of those rivals survives.

## Evidence

- Final battery: 12/12 green at generator SHA
  `8d49b1a81531cd0d81d545fe4966af281296f9fe3c58c187e08bc076c3646f3b`.
- Portable task tests: 47 passed.
- Lesson census: 300 lessons, 1,200 query rotations, zero ambiguities, 1,192
  unique inputs.
- Independent probe: 400 ordinary draws, zero failures; all three rivals
  refuted on every sampled draw, with full counterexamples retained.

The checks are finite and cover declared rivals, not every imaginable induction
shortcut. The Racket rule and canonical data were not changed.
## Current reviewer considerations

Source SHA-256: `8d49b1a81531cd0d81d545fe4966af281296f9fe3c58c187e08bc076c3646f3b`.

# Decisions for 7e7614405852

## D1 — Preserve the canonical authority

**Choice.** Leave the Racket rule and canonical JSONL unchanged and pin
`RULE_HASH = "5eb06a6d574a"`.

**Rationale.** Baseline rule smoke and authority synchronization passed, and an
independent row scanner reproduced every canonical output. The failures were in
the sampler contract and curriculum, not labels.

**Rejected alternative.** Changing the Racket source would expand scope and
risk altering a correct rule.

**Limits.** Python mirrors are regression aids only; Racket remains authority.

## D2 — Replace decorative controls with exact structural axes

**Choice.** Publish only `grid_h`, `grid_w`, `n_len2`, `n_len3`, `n_len4`,
`n_len5`, and `n_vertical3`.

**Rationale.** Each value is recoverable from the returned grid and directly
controls a semantic or geometric property. The old palette, density, position,
and texture controls were ignored, constant, aliases, or fixed side paths.

**Rejected alternatives.** Keeping old names as aliases would preserve silent
coercion; marking them diagnostic would still advertise controls with no useful
training effect.

**Failure modes.** Distinct-color objects constrain scenes to at most eight
objects. That is explicit in the current axis bounds and sufficient for the
canonical curriculum.

## D3 — Construct layouts rather than retry random placement

**Choice.** Backtrack-pack requested run lengths into row capacities, then
randomize row order, slack, side, vertical span, and colors.

**Rationale.** Every declared boundary combination, including the 5×8 maximum
object count, must be realizable without silently lowering counts.

**Rejected alternative.** Retry-only placement can become seed-dependent and
turn a valid exact override into an intermittent rejection.

**Probe.** The boundary Cartesian test covers all declared count combinations,
both shape extremes, and all four difficulty settings.

## D4 — Make exactness and orientation counterexamples ordinary

**Choice.** Default `n_len5=1` and `n_vertical3=1`, while supporting exact zero
overrides.

**Rationale.** Canonical examples contain lengths 2/3/4 but no length 5 or
vertical triple. Without these two additions, “mark every odd run” and “mark
triples in either orientation” remain plausible.

**Rejected alternative.** Sampling the witnesses occasionally would allow
unlucky three-demo lessons with no disambiguating example.

**Limits.** This guarantees coverage of the declared rivals, not all possible
hypotheses.

## D5 — Validate the complete object grammar

**Choice.** Require rectangular ARC-color grids, no input 8, background 0,
unique-color straight objects, horizontal lengths 2–5 in declared counts, at
least one exact horizontal triple, and at most one vertical triple.

**Rationale.** The former validator returned success after seeing the first
triple and was insensitive to most destructive mutations.

**Rejected alternative.** A loose canonical-like validator would make exact
axis recovery ambiguous and allow generated-domain drift.

## D6 — Encode teaching claims as executable rivals

**Choice.** Declare three pure rivals plus two witnesses and implement
`lesson_identifiable` against the live declarations.

**Rationale.** Prose cannot prevent a later generator edit from removing the
counterexamples. Executable outputs make the curriculum claim replayable.

**Rejected alternative.** A single generic “wrong rule” would not identify
whether length exactness or orientation caused the ambiguity.

## D7 — Retain an independent future-reviewer probe

**Choice.** Add `workspace/reference_probe.py`, which implements its own row
scanner, samples all difficulty settings, verifies strict inputs/observer, and
saves one full counterexample per live lesson competitor.

**Rationale.** It gives future agents a cheap source-bound diagnostic without
copying a stale rival-name list or invoking private labels.

**Limits.** The 400-draw retained run is empirical and declaration-bounded.

## D8 — Preserve solve isolation and exposure honesty

**Choice.** Finish the unrelated blind episode first. During the final task
solve, use only the newly presented visible examples and declare earlier rule
exposure `yes`.

**Rationale.** The repair necessarily exposed task semantics; calling the later
record blind would be misleading.

## Prior evidence lead

No prior return was used. `evidence/associated_notes.jsonl` contained no record,
so all baseline claims were remeasured from the pinned source in this packet.
