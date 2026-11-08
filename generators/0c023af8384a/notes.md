# Working notes: 0c023af8384a

## Current decision — 2026-10-26

Repaired the retained exact-control and observability findings in generator
`2.2.0`. Explicit size and mark pins take precedence over difficulty ranges;
`dense` respects an exact mark count; exact even-height `on_axis` requests keep
their height; one-mark `on_axis` requests remain effective; unpinned
`on_axis` draws an odd height directly; unknown overrides are rejected; and
`observe_overrides` reports the realized dimensions and mark count. A final
axis-only repair preserves exact dimensions/counts while preventing accidental
identity lessons on short odd grids. The task-local override-contract sweep
accepts all 3,492 draws across 388 cases and three difficulty bands.

Added the proposed native family `completion={vertical,
vertical_then_selected_horizontal}`. The default program is the exact catalog
source. The alternate performs canonical vertical completion (A), then chooses
the most frequent nonzero color in that intermediate and horizontally completes
only that color (B). Inputs are setting-independent, support 3–6 demonstrations
and 1–4 queries, and include a distributed 30×30 fourth query. Focused pytest,
a protected-Racket four-job study, authoring preflight, a protected skip-A
witness, and public projection checks are retained as source-bound reviewer
evidence. Owner source review, native qualification/acceptance, and any training
admission remain separate.

## Second reviewer pass — 2026-10-26

Removed a residual fixed-side teaching shortcut. The selected color now
alternates between left and right source regions inside every three-example
episode while preserving setting-independent inputs and the exact A→B rule.
A new regression test proves that fixed-left and fixed-right selectors each
fail, and the protected-Racket probe now embeds a 200-seed / 600-demonstration
shortcut audit in its source-bound report. The focused suite now has 20 tests;
the protected study still passes 40 Racket evaluations.

## Third reviewer pass — 2026-10-26

Removed a second residual teaching cue: the selected color had always been the
second-most frequent nonzero color in the raw input. Odd-index demonstrations
now include two axis-only competitors, so the true selector alternates between
raw-frequency ranks two and three while remaining the unique winner only after
vertical completion. A new regression test rejects fixed rank-two and
rank-three rules. The permanent probe now checks side and frequency-rank
variation over 200 seeds / 600 demonstrations in addition to 40 protected-Racket
evaluations. The focused suite now has 21 tests.
