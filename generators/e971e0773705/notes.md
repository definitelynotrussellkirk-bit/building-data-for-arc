# Working notes: e971e0773705

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric decision

The separate `workspace/parametric/` family exposes episode-fixed
`count_mode=raw|cancel_opposites`. `raw` returns the exact canonical Racket
program bytes; the alternative counts the same four-connected red T components,
cancels opposite orientations one for one, then caps each residual count at four
and fills the existing blue/green emblem positions. Production `generator.py`
and the canonical rule are unchanged. The source version remains `3.0.1`, SHA-256
`1bb0029217dfe3bc4d19aeed64933a5d41db97231c4596a74253544ff650e5b9`, rule
`2855526e979d`.

The count after cancellation is the input-dependent intermediate consumed by
the cap and tally. For example, counts `(8,3)` leave five unmatched top-bar Ts,
which produce four blue marks. Capping first leaves `(4,3)` and then one blue
mark. This is a count-state dependency; no spatial pairing or iterative motion
is claimed.

Both settings share the entire input bank for a seed, including queries.
Complete banks are constructed before slicing, so independent demonstration and
query requests preserve prefixes. The proposed exact-T grammar extends the
production size/count sampler through 30x30. Its dense query contains 54 distinct
Ts, 216 red cells, and content reaching all four edges. Seed zero also exercises
the literal 2x3 minimum; other seeds vary small-query geometry and counts.

## Teaching repair and retained counterexamples

Five demonstrations are the supported minimum and default, with a maximum of
six. They teach a saturated winner in each color, a nonsaturated winner in each
color, and equal-count cancellation. Counts below five are rejected. Keeping the
queries varied exposed two concrete problems in earlier teaching banks:

- The earlier supported four-demo seed17 cancellation lesson allowed a
  green-only cap-three rival to fit every demonstration, then disagree with
  emitted query1. The exact Racket programs, grids, labels and source hashes are
  retained in `checks/e971e0773705/audit-asymmetric-before/private/asymmetric-cap-before.json`
  in the reviewer delta. The old Python sampler bytes were not separately saved;
  this evidence replays the semantic failure, not the old seed-to-grid generator.
- After both saturated winners were taught, a four-demo seed17 lesson still
  allowed a blue-only always-four rival to fit all demonstrations. Emitted query2
  has counts `(10,8)` and needs two blue marks; the rival returns four. Twenty
  protected Racket evaluations reproduced it. The old source snapshot and
  reproduction are retained under `checks/e971e0773705/asymmetric-majority-before*`.
  Teaching both nonsaturated winners closes this demonstrated gap.

`audit_native.py` is the reusable bounded check: independent Python and Racket
meanings, twenty explicit extra rivals, fits frozen using demonstrations, then
query disagreements checked only for surviving hypotheses. Execution errors
fail closed. A deliberately weak five-demo lesson separately demonstrates the
cap-before-cancel failure and its teaching repair. Finite rivals and seeds do
not establish universal identifiability or a model-performance improvement.

## Export and admission boundary

`make_examples.py` obtains labels through the protected native worker and calls
the strict task-local exporter. Controller records contain four novel queries;
each actor payload contains the demonstrations and exactly one current masked
query, without future inputs, total-count hints, settings or private answers.
Content IDs bind exact visible bytes. Invalid counts, duplicate inputs or public
payloads, invalid private grids and non-JSON metadata fail before publication.
The manifest is written last. The exporter does not itself authenticate labels.

The reviewer delta supplies the native source inventory, qualification and two
causal counterfactual replays. Exact-source owner qualification and acceptance
remain required after integration; `training_admitted` remains false. Runnable
commands, request limits and evidence scope are in `workspace/parametric/README.md`.

## Earlier production findings remain open

This prototype does not repair or silently clear inherited observations about
the unchanged production lesson sampler: the cap-three ambiguity in retained
`repair-review-6dd9f121c37f0225-v0001` was a direct-draw lesson; the C8 ambiguity
in `repair-review-72e374634768ca1f-v0001` was an actual native lesson at seed1,
three demonstrations and four queries. That C8 rival fits the demonstrations and
differs at query1/sample4. Those receipts were read, not freshly replayed here.
Their next action is a separate production teaching repair and focused replay;
new-prototype checks and generic approval do not resolve them.
