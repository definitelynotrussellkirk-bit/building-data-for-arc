# Working notes: 5949237e2737

## 2026-10-03 review-d3b87882f505f62c

The v3.0.0 five-profile curriculum killed a global color-presence rival but did
not require the matching right-side color to occur on the same row as a
wrong-position mismatch. A stricter row-local shortcut therefore fit 34/600
sampled production lessons (three bands × 200 seeds); the forced decoy profile
failed to distinguish it in 209/600 samples. Reproducer: seed 44, easy band.

Version 3.1.0 reserves two left positions on one row in `wrong_color_decoy`,
forces one to match and one to mismatch, paints both left cells with the decoy
color, and registers `row_color_presence` as an executable semantic rival. The
retained probe `workspace/probe_row_color_presence.py` reports 0/600 survivors
for both the forced profile and complete five-demo lessons after the repair.
The canonical Racket authority and `RULE_HASH` are unchanged.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `bc40405bd00bf74cd3d125f936782c709d83ee4f8d7c46577ba1ee83ab899746`.

# Decisions for 5949237e2737

## D1 — Treat the green baseline as a search for missing rivals, not a rewrite

**Observed state.** The pinned 3.0.0 source passed the full before battery 12/12.
The associated prior return
`review_response_external-local-random_3eca311785c8_x` documented why the
five-profile curriculum and right-side authority were chosen. I used that note
as a lead, then reran the current source rather than accepting the retained
claim as fresh evidence.

**Decision.** Preserve the architecture, axis ranges, canonical anchors, and
Racket authority. Search for a plausible rule that was not in the declared
semantic competitors.

**Rejected alternative.** Rebuild the distribution or add unrelated shape and
palette variation. That would add regression risk without addressing a measured
failure.

## D2 — Add the row-local color-presence rival

The existing `global_color_presence` rival asks whether a left color appears
anywhere on the right. A stronger and still simple learner can condition on the
row:

```text
keep left(r,c)=x when x occurs anywhere in right-half row r
```

This rival fit all five demonstrations in 34/600 sampled production lessons on
the baseline. The forced decoy profile itself failed in 209/600 samples. The
smallest deterministic reproducer was `difficulty=easy`, seed `44`, sample
indices `0..4`.

**Decision.** Register `row_color_presence` in `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`, and give it a named semantic
witness. This makes future standard gates aware of the exact failure rather
than relying only on an external probe.

**Failure mode considered.** Merely declaring the rival would make checks fail
without improving lessons. The distribution had to supply a deterministic
counterexample inside every five-profile schedule.

## D3 — Strengthen the existing decoy profile instead of adding a sixth slot

**Input choice.** In `wrong_color_decoy`, reserve two distinct left positions on
one row. Force one reserved position into `match_positions` and the other out of
it. Paint both left cells with the same decoy color. Their right side therefore
contains:

- one exact same-color reflected match; and
- the same color elsewhere on the same row, but not at the second cell's exact
  reflected coordinate.

**Original rationale retained.** The prior five-profile schedule was designed so
five demonstrations cover the five semantic contrasts needed by the task. Its
global decoy also deliberately cycles the palette so requested `palette_size`
is observable at the seven-cell boundary.

**Why this choice.** It repairs the missing locality distinction within the
profile already responsible for color-presence decoys. The five-example lesson
size, cyclic schedule, and canonical-anchor profiles remain unchanged.

**Rejected alternatives.** A sixth profile would no longer guarantee complete
coverage in five demonstrations. Randomly hoping two decoy cells land on the
same row caused the measured defect. Moving the same-color cell to a different
row only refutes the weaker global rival. Adding extra right-only cells would
not force coordinate-specific comparison.

## D4 — Keep palette and override semantics exact

The reserved same-row pair is selected before colors are assigned. The existing
palette-cycling logic remains responsible for exposing every requested color,
including `left_cells=7, palette_size=4`. The match/mismatch pair is passed
explicitly to `_paint_pairs`, which validates that one member is a match and the
other is not.

**Alternatives rejected.** Inferring the pair later from the first arbitrary
match and mismatch could select different rows and recreate the bug. Hardcoding
a color outside the sampled palette would violate `palette_size` observability.

**Probe.** The task-local script tests 200 seeds × 3 bands both with the decoy
profile forced and with the complete five-demo schedule. Baseline: 209/600 and
34/600 survivors. Final: 0/600 and 0/600.

## D5 — Pin authority and leave Racket unchanged

All three canonical pairs already match the selected Racket authority, and the
repair concerns lesson identifiability rather than output semantics. The
canonical `RULE_HASH` remains `08326857fca3`; the after battery's rule-smoke,
Racket-lint, and authority-sync stages are green.

**Rejected alternative.** Editing the Racket source would change correct
semantics to solve a generator-only distribution problem.

## D6 — Tests and reusable tooling

A regression test names the baseline reproducer (`easy/44`) and asserts that at
least one of its five scheduled examples refutes the row-local shortcut. The
reusable workspace probe reports both profile-level and lesson-level survivor
counts and accepts an alternate generator path, allowing before/after comparison
against the frozen baseline.

The test was written and observed failing before production code changed. The
final selected-task stage passed 44 collected cases; the repository suite passed
273 tests.

## D7 — Distribution consequences and known limits

The only new structural guarantee is local to `wrong_color_decoy`: at least two
left cells share one row and decoy color. This is intentional teaching support,
not a restriction on the authority-valid grammar. Other profiles continue to
sample arbitrary positions, and all advertised minimum/maximum overrides pass.

A finite rival set can miss another shortcut. The 300-lesson census covers all
currently declared competitors but does not rotate each example into every
query position. The strongest remaining process limitation is therefore shared
tooling: semantic gates should generate bounded locality variants of declared
rivals rather than testing only names supplied by the task author.
