# Working notes: b3750af4dac1

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

# Native parametric review — 2026-10-25

## Preserved authority and selected family

The production generator remains byte-exact at
`c53fc9358c39c9c48fc9a67c7672251919bf7856e7dcc6fc2442189c73a7b92b`.
The `finish=match_only` setting is the exact selected canonical program,
SHA-256 `674e022a164ba23953f076335f26ee58ff9832627f0d1aa9200c516446709d92`.
The alternative `finish=mark_match_neighbors` first computes the canonical
one-hot complete-signature match strip, then uses its color-8 position to recover
the selected room and marks candidate rooms connected to it by color-7 doorways
with color 4.

The bounded sampler guarantees that the first same-area candidate is a different
room with a different graph neighborhood. It also rejects scenes where the true
neighbors equal adjacent strip positions or the query room's neighbors. The
fourth query is an exact 30x30, 25-room scene with at least 400 nonzero cells.

## Repairs and retained evidence

The inherited canonical test used a checkout-relative data path and failed in the
staged runtime. It now resolves canonical pairs through `reviewer_support`.
The structural-shortcut regression was written first, observed failing on a
case where `[selected-1, selected+1]` exactly matched the graph neighbors, and
then made green by strengthening sampler eligibility.

- Complete staged task suite: 38 passed, 43 subtests passed; one pre-existing
  `_drawn` deprecation warning remains.
- Bounded self-audit: 12 jobs, 160 protected-Racket evaluations, 16 isolated
  one-query public turns, and no harmful survivor among the declared finite rivals.
- Native qualification: both settings, seeds 0 and 17, 3 demonstrations and 4
  queries, 40 protected-Racket labels.
- The source-bound counterfactual substitutes the first same-area match for the
  exact-signature intermediate and changes the final output on the retained 30x30 witness.

The finite rival set and sampled seeds do not prove universal identifiability or
training benefit. Owner exact-source integration, fresh acceptance, and any
training admission remain pending.
