# Working notes: cd818a9d92d1

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current proposed parameter extension

`workspace/parametric/` now supplies episode-fixed `bend_direction=left|right`,
with `right` equal to the selected canonical Racket bytes. The production
generator and rule are unchanged. Both directions use identical seed-controlled
inputs, so their comparison isolates the transformation.

The prototype strengthens the common input domain: interior marker columns,
guide-row-only red markers, and no gray cells in either active bend destination.
This excludes lawful right-only edge/overlap cases rather than mislabeling them
under a leftward rule. The 5×6 compact profile has four distinct inputs; requests
above finite support fail explicitly. Demo/query counts are independent (1..8).

Labels and demo-only finite-rival certificates execute in Racket. The exporter
uses exact visible-byte content IDs, rejects duplicates and existing
destinations, and keeps private metadata separate. An independently reproduced
forged-provenance acceptance gap was repaired: certification now checks the
exact program digest and current loaded generator/prototype source mapping.
The retained regression rehashes modified private data and still must be rejected.

Evidence: `WORK/checks/parametric/run-01/` has two seeds × two directions,
each with two demonstrations and four distinct queries; fresh export replay
checks all 24 labels. The adapter and bounded promotion contract are proposals.
Next useful owner action: review the parameter semantics, bind the current
prototype inventory, then run protected qualification and explicit acceptance.
Neither this prototype nor its evidence admits data to training.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/cd818a9d92d1/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
