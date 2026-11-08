# Current design — public_eval_5961cc34

General reference: a yellow emitter's adjacent straight red tail determines the
launch vector. A beam stops at the first blue/green object. Every reached object
becomes red and emits one parallel ray per green port cell along the port's
outward normal. Unreached objects disappear. Activated objects do not re-emit on
re-entry, so loops terminate. Original 4 demonstrations and 1 gold query were all
executed successfully by protected Racket; no stored-example lookup is used.

The fixed episode parameter is finish=trace_only|highlight_deepest. The alternate
computes the minimum relay-hop depth of each reached object and highlights the
entire maximum-depth class with 9. This requires the traced activation graph,
not object size or reading order. The protected wrong-intermediate program uses
largest reached object size instead of depth. The default is byte-identical to
reference.rkt and the task-local canonical.rkt copy.

Sampler: constructive six-route bank, 3..7 active relays, one or more unreachable
large decoys, one/two-cell green ports, clipped/solid variable-size bodies, all D4
orientations, and a closed loop. Grid controls describe the FINAL dimensions;
an inherited design mistake where quarter-turns swapped them was caught by a
failing regression and fixed. The first demo intentionally separates reading
order and depth. Every episode contains a full-content 30x30 query; all four
queries are shuffled privately by a separately supplied presentation seed.
2..6 demos; exactly four private queries; no retry/fallback path.

Bounded self-review: seven executable wrong rules, exact controls under all eight
transforms, cycle termination, count-stable input streams, matched settings,
boolean/numeric rejection, hidden-field invariance and corrupt-export rejection.
No universal uniqueness claim. Generated support is 24..30 canvases and structured
route templates, not every possible routing network in the broader reference
rule. Original source colors are semantic constants, not palette-permuted roles.

Current receipts: WORK/checks/public_eval_5961cc34/preflight-current/ and
WORK/checks/public_eval_5961cc34/audit-current/. Preflight is UNAPPROVED authoring
execution, not native qualification. Owner registration, native qualification and
exact-source acceptance remain required. training_admitted=false.
Final review is author self-review, not an independent review.

## Current repeated-parent reconciliation

Preserve exact trace_only/highlight_deepest programs. Adopt cycle-plus-fanout demonstrations defeating terminal-only and single-deepest shortcuts; query episodes alternate original and enriched banks. Support 1..4 independently shuffled query prefixes. Replace the declared-sidecar ordinary wrapper with a reproducibly built generator-file-only standalone implementation and explicit fanout control; changed ordinary inputs are retained in exact replay. Current evidence resides in evidence/repeat-third-union. Private native acceptance and root publication are separate.
