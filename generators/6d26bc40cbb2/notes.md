# Working notes: 6d26bc40cbb2

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `1ba4607de347feb071ff544d510292e642881d2a8e8ecd91f149a8b966b83ee7`.

# Decisions: 6d26bc40cbb2

## Context and prior leads

I reviewed the pinned selected baseline with generator SHA-256
`5076571aea2b299901e16acc113806bcabb977abc601f826c1a88ffa82d23544`.
The retained associated-notes file was empty, so no prior return was treated as
evidence.  Standard baseline stages passed when run separately, which made a
source-bound adversarial rival probe necessary rather than a broad rewrite.

## D1 — Model the shortcut that a learner could actually use

**Choice.** Redefine `rival_modal_color_only` to begin with the complete original
payload (markers removed) and add translated copies only for modal-colored cells.

**Rationale.** “Copy only the modal color” should differ from the authority only
in what is copied.  The baseline rival also deleted non-modal original cells, so
retaining the input object was enough to refute it.  That measured a different,
less plausible rule.

**Rejected alternatives.** I did not remove the rival, weaken its claim, or mark
it diagnostic-only.  Those choices would hide a real canonical-fitting shortcut
rather than improve training evidence.

**Probe.** The test `test_modal_color_only_rival_keeps_the_complete_original_payload`
failed before the source change and passes afterward.  The baseline broad probe
found 1,139 non-refuting multicolor samples and 1,299 ambiguous lesson windows.

## D2 — Guarantee one visible non-modal copied cell without narrowing structure

**Choice.** Preserve the sampled palette and exact sampled color multiset, then
assign one non-modal color to a randomly selected source cell whose translated
destination is in bounds and outside the original payload.  Shuffle the remaining
unchanged colors over the remaining unchanged shape cells.

**Rationale.** One such cell is the minimal direct witness that all colors—not
only the mode—must be copied.  `_find_layout` already guarantees a newly visible
copied destination, so no shape, grid, marker, vector, clipping, payload-size, or
palette-size rejection loop was added.

**Rejected alternatives.** I rejected forcing every scene to be multicolor,
forcing a fixed minority color, adding a fixed shape cell, or changing the
three-example schedule.  Each would either narrow other axes or teach the answer
through a conspicuous template.  I also rejected changing color counts; the final
implementation uses the same “one of each, then free draws” bag as v3.0.0.

**Probe.** `test_multicolor_generation_exposes_a_nonmodal_color_in_new_copy_area`
uses the deterministic baseline counterexample easy seed 1/sample 1.  The final
large probe reports 24,300/24,300 multicolor refutations and 0/46,800 ambiguous
three-example windows.

## D3 — Leave Racket and canonical authority unchanged

**Choice.** Modify only Python generator/rival behavior, task-local tests, and the
workspace probe/documentation.

**Rationale.** Rule smoke, canonical execution, and the solver semantics were
already correct.  The defect was training-data identifiability, not authority.
Authority-sync execution parity remains green.  No canonical JSONL row changed.

## D4 — Keep both broad and focused evidence

**Choice.** Retain:

- failing red tests and baseline realistic-rival probe;
- final task tests;
- a source-bound, reusable CLI probe;
- the twelve-stage isolated battery summary; and
- the genuine exposed solve record.

**Rationale.** The standard semantic gate passed the malformed rival.  A focused
probe is therefore necessary to show both the original false assurance and the
repair’s intended guarantee.  The CLI derives behavior from the selected source
and records the source hash, sampler, unique-input count, witnesses, and all
sliding three-example windows.

## D5 — Treat the aggregate-runner stall as tooling, not a task failure

**Choice.** Preserve the interrupted aggregate logs, rerun each stage in its own
process, and report both facts.

**Rationale.** The monolithic parent repeatedly stopped progressing while entering
`defect_lint`, yet `defect_lint` completed in about ten seconds by itself and the
complete isolated battery is 12/12 green.  Concealing the interruption would be
misleading; treating it as a generator failure would also be incorrect.

## Limitations

The final exhaustive claim is bounded to the recorded deterministic sampler:
300 seeds per difficulty, indices 0–53, and consecutive windows of length three.
Single-color scenes necessarily cannot distinguish full-copy from modal-only-copy;
the lesson schedule supplies multicolor evidence.  The new conditional placement
correlation is intentional and minimal, but future data-quality gates should
continue testing for shortcut interactions beyond this named rival.
