# Working notes: 7860069b4149

## 2026-10-24 review `review-7944861aa83ee6b1`

Repaired the fixed generator/validator against the exact canonical contract in
version `2.0.0`. It now accepts all three labeled canonical inputs, connected
monochrome polyominoes (including holes and concavities), bbox-side anchors that
need not touch an occupied component cell, all four directions, and exactly one
available sweep step. Typed axes cover 5×5 through 30×30, shape kind, foreground
color, anchor side, and sweep length. Unknown or misspelled overrides fail
closed. A wide-U one-step case separates whole-shape translation from the old
canonical-fitting scanline-envelope shortcut.

Built a separate proposed `trail_mode=continuous|terminal_only` episode family.
`continuous` returns the canonical Racket source byte-for-byte; `terminal_only`
preserves the same object, direction, and stopping reasoning while painting only
the farthest valid translated copy. Inputs are matched across settings; 2–6
demonstrations and 1–8 queries are independent, with four queries by default and
a substantive 30×30 fourth query. The controller-facing projection emits one
visible query per turn, includes neither future inputs nor a total-count hint,
and has byte-equivalent first-turn content to single-query use. Every retained
label is executed through protected Racket.

Public IDs hash only visible bytes. The source-bound evidence verifier rebuilds
public projections and rejects stale generator hashes, altered programs,
missing settings, count mismatches, unlisted files, path escapes, and rehashed
answer tampering. The native inventory remains `reviewer_reported`; the variant
is proposed and unapproved, with no training admission.

Focused evidence: 13 fixed-generator tests plus 16 parametric tests (29 total),
a 23-case protected Racket replay across all assigned tasks, and a bounded
1,172-case sampler/domain probe with zero observed failures (132 on this task).
These finite checks cover the declared settings and profiles; they do not prove
all seeds, arbitrary alternative programs, owner qualification, acceptance, or
training suitability.
