# Working notes: 9a94379ed070

## Current decision

Retain the selected production generator and canonical Racket authority unchanged.
A task-local **proposed, unapproved** prototype exposes one episode-fixed
parameter, `rank_offset ∈ {0,1}`. Offset `0` returns the canonical program
byte-for-byte; offset `1` moves each cyan macro/micro correspondence to the next
active motif rank cyclically. Motif recovery, macro and micro row-major ranking,
self-product construction, colors, and input grammar remain invariant.

The retained lesson uses two demonstrations and four distinct queries per
setting on shared lawful inputs. Both demonstrations reject the other setting,
and all four queries differ under that rival. Every label is executed through
the exact matching Racket program and checked against an independent Python
mirror. Public challenges omit settings, seeds, programs, and query answers and
are named only from visible bytes. Private episodes, the report, and the manifest
bind the exact prototype source path and SHA-256; replay rejects stale identity,
modified bytes, symlinked/out-of-inventory paths, seed or source drift, and
split-brain `train`/`test` copies.

Evidence: `checks/parametric/9a94379ed070-rank-offset-v1/report.json`,
`checks/parametric/9a94379ed070-rank-offset-run-v4/verify.log`, and
`checks/parametric/9a94379ed070-rank-offset-adversarial-v1/result.json`.
Focused tests pass 10/10 and staged selected-task tests pass 26/26. The staged
baseline also required repairing the existing portable test harness to resolve
canonical data through `reviewer_support` instead of a test-relative path.

## Limits and next action

Evidence covers only offsets 0 and 1, seed 31, the selected generator grammar,
and the other offset as the declared rival. It does not establish uniqueness
against arbitrary programs, exhaustive seed coverage, production approval, or
training admission. If the owner wants promotion, the next useful action is a
separate source-acceptance review and thin adapter/promotion contract using these
exact program bytes and retained verifier; do not replace the canonical rule.
