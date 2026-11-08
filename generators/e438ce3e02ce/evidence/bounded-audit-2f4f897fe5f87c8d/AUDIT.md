## e438ce3e02ce

**Conclusion: Domain question / order-sensitive shortcut, not a reproduced production defect.** Source SHA-256: `60a2cee1c491a112a7d37e67336131257da46cdb417cc03b92fc6c176a068c7f`.

The documented fixed lesson order works: all 12 sampled four-demonstration/one-query lessons are identifiable against the declared Euclidean rivals. However, arbitrary query reassignment does not. The semantic audit checked 60 held-out positions and found 27 ambiguous rotations, each with a hook warning and no execution/scoring error. Only 33/60 rotations remain identifiable.

The first exact witness is retained under `checks/audit/e438ce3e02ce/`:

- recipe: difficulty `easy`, seed `120682136684435`, sample index `0`;
- held-out flattened pair/query index: `1`;
- demonstrations retained: indices `[0, 2, 3, 4]`;
- surviving rival: `euclidean_only_for_four_seeds`;
- `input.json`: the held-out lawful query input;
- `expected-from-census.json`: authoritative output recorded by the semantic census;
- `rival.json`: the surviving rival's different output;
- `racket.json`: independent supported `arcpuzzles apply` replay;
- `counterexample.json`: source/rule hashes, recipe, validation, counts, and command.

The query passes the target validator and belongs to the documented generator domain. Independent Racket application matches `expected-from-census.json` and disagrees with `rival.json`. The ambiguity arises because the held-out pair is the only four-seed Manhattan-versus-Euclidean discriminator in that lesson; the remaining demonstrations do not refute a rival that switches to Euclidean distance only for four seeds.

Measured context:

- 11/11 portable tests passed.
- 308/600 generated draws passed the strict-canonical profile, above the declared `0.45` floor; no crashes or hook errors were observed.
- 12/12 ordered lessons were identifiable.
- 27/60 diagnostic rotations were ambiguous; zero rotation scoring errors.
- The additional deterministic sweep covered 5,760 draws and 5,737 unique normalized inputs with no exception, nondeterminism, or `self_check` failure.

**Recommendation.** Keep the current fixed order if that is the real export contract. Before a downstream data pipeline shuffles demonstrations or rotates which pair is the query, either require rotation identifiability or construct each lesson with redundant 3-, 4-, and 5-seed Manhattan-versus-Euclidean discriminators. Unconditionally calling this a generator defect would be a false positive under the fixed-order contract, so I made no audit-target edit.
