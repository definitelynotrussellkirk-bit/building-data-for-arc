# Working notes: ff76baf6c2d9

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/ff76baf6c2d9/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current decision — review-6669ae4d2df7bdfa

Built a native two-setting family around the existing template-copy rule.  The
canonical default (`mirror_when=anchor_is_2`) is byte-identical to the selected
canonical Racket program; the alternative mirrors non-2 anchors instead.  Inputs
are setting-neutral, support 2–6 demonstrations and 1–4 queries, and include a
substantive 30×30 fourth query.

Each pair contains both anchor classes and two asymmetric sources.  The minimum
two demonstrations also alternate which row-major source owns color 2 after all
whole-grid transforms, blocking always-preserve, always-mirror, identity, and
left/right-source orientation shortcuts.  Protected-Racket qualification covered
2 settings × 2 seeds with 28 labels; the finite adversarial audit performed 58
additional evaluations with zero surviving named rivals.

The inherited task test now locates canonical data through `reviewer_support` and
records the archived raw/target Racket sources as intentionally distinct from the
current canonical authority instead of asserting false byte equality.  The native
artifact is reviewer-ready only.  Next action is owner integration followed by
fresh exact-source qualification and acceptance replay; no training admission is
claimed.  Optional peers `2a6aac780e6d` and `3206770a2bd8` were left unmodified.
