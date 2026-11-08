# Working notes: 7bd583886bad

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/7bd583886bad/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-24 parametric label-policy proposal

Built `workspace/parametric/` around `label_mode=shape_type|area`. The default is
the byte-exact canonical exact-cover program. The alternate keeps the same legal
piece set and unique-cover search, changing only final cell labels from piece
IDs 1–4 to piece areas (4 for the square, 3 for each L tromino). A constructive
sampler produces connected masks with exactly one cover, independent demo/query
streams, 2–6 demos, and 1–8 queries. Its fourth ordinary query is a connected
30x30 mask with a unique cover, at least 70 occupied cells, and a bounding box
spanning at least 25 rows and columns. Demonstrations exclude the one degenerate
all-type-3 case so the two settings are identifiable without query answers.

Focused tests and retained protected-Racket evidence cover both settings,
matched inputs, count boundaries, four-query export, query-prefix stability,
private/public separation, malformed labels/masks, and the 30x30 case. The
bounded adversarial pass generated 32 episodes across four count corners, four
seeds, and both settings, rechecking connectivity and unique cover. Native
qualification was attempted but correctly refused before execution because the
production generator is not approved on its current source/rule. The concrete
next step is owner approval of that unchanged production source followed by the
existing `parametric qualify` command; no approval bypass was made. The prototype
is proposal-only and is not accepted or admitted to training.
