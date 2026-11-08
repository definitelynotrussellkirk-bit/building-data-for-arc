# Bounded allocation-quality assessment

Ticket `ticket-863b7283c68abcae`; seeded sample `9e204e7ff3a2`, `4ebdc8d865ce`, and `a16e387b682a`.

## Scope and identity

The primary source is still exactly the ticket-pinned `generators/9e204e7ff3a2/generator.py` SHA-256 `b9bef337d0036693ea5759767287b4555de82435260990cdab10e84c0aba219e`; the packet pins canonical rule hash `892d64eecd2e`. The two comparison records were selected deterministically from the current `allocation_quality` candidates with the ticket seed; `selection.json` records the algorithm and identities. This assessment does not run a model, alter weights, approve a source, or claim a globally optimal mixture.

## What the current pool is allocating

`allocation-context.json` shows a uniform packet draw pool of 500 IDs: all 500 packet IDs are main IDs, including 293 packet-approved and 207 packet-unapproved records. The derived catalog has 498 rows and broad lint debt (`477 warn`, `9 err`, `12 pass`). The separate catalog-weight file is nearly flat (`465` at `1.0`, `20` at `0.3`, `11` at `1.5`, `2` at `0.0`). Each sampled source has weight `1.0`, so equal weight does not encode the current source-bound review state.

The dated training context reports a different level of allocation: r6 materialized tokens were ARCpuzzles 37%, NVARC 36%, ARC-GEN 16%, and RE-ARC 11%. Those are frozen October 23 measurements, not a current optimum and not directly comparable to the packet's uniform 500-ID authoring pool.

## Seeded source comparison

| Source | Current evidence | Teachability / four-query support | Review and dedup cost | Bounded disposition |
| --- | --- | --- | --- | --- |
| `9e204e7ff3a2` | Packet-unapproved; queue pending/unverified; missing declared `RULE_HASH`; no task tests or `observe_overrides`; current source-bound audit reproduces invalid advertised exact overrides, accepted unknown key, and 79,740 explicit rejections in 135,720 audit draws. | The exact replay in `postprocess.json` produced seven distinct visible-effect inputs, mixed both UD transfer directions across three demos, four distinct queries, and eliminated five cheap rivals on demonstrations alone. This is useful positive evidence for one default episode, not the override contract. | High. Contract repair, source pin, tests, and an authoritative retained episode are prerequisites. The sole bounded Racket call reached `rule_hash_matches_catalog=true`, but the reviewer probe then asserted a nonexistent generic `rule_hash` field instead of the documented `executed_rule_hash`; therefore it retained no labels. That is a probe-script failure, not a source/Racket mismatch. | Do not spend accepted-episode volume yet. Spend repair/verification effort first. |
| `4ebdc8d865ce` | Packet-approved and reviewed-safe; current source/rule pin; declared `RULE_HASH`; task tests, `self_check`, `observe_overrides`, and a Python mirror. Current retained evidence includes a valid/invalid API boundary check and a source-bound adversarial witness confirmed by Racket. | Strong semantic evidence, but `EXAMPLES_NEEDED=5`, so each episode costs more demonstration tokens. The current ticket did not run a fresh four-query episode for this source. | Moderate. Existing source-bound receipts lower review risk; five demos increase token/rendering cost. | Candidate for the bounded accepted-episode comparison. |
| `a16e387b682a` | Packet-approved and reviewed-safe; current source/rule pin; declared `RULE_HASH`; focused tests and exact override recovery. Version 3 repaired the previous Euclidean/top-left proxy and enforces unique canonical Manhattan scores. | Consecutive indices cycle target reading-order rank `0/1/2`, directly rebuffing a fixed-position shortcut in a three-demo window. The ticket has no fresh authoritative four-query receipt for this source. | Low-to-moderate. Three demonstrations should be cheaper than the five-demo source, but source-bound Racket evidence still belongs in the proposed test. | Candidate for the bounded accepted-episode comparison. |

## ARC-GEN and RE-ARC coverage limit

The seeded records are ARCpuzzles generators only. The packet does expose source-specific integration contracts:

- RE-ARC's integration tool requires `verifier(input) == output`, removes empty/identity cases, deduplicates exact pairs, bounds sampling attempts, and fingerprints generator/verifier source.
- ARC-GEN's native builder requires a usable rule source, validates dimensions and colors, retains generator version provenance, and supports grouping up to four query pairs.

No current ARC-GEN or RE-ARC episode, rejection-rate receipt, ambiguity assessment, repair record, or source hash was selected here. The tools show useful gates but do not establish current quality per token. This ticket therefore makes no source-ranking or volume recommendation across ARCpuzzles, ARC-GEN, and RE-ARC. The dated r6 shares remain context only.

## Alternative allocation to test

**Estimated, sampled-family proposal—not a production weight change:** temporarily gate accepted episode production on current source-bound readiness. For a 10-episode comparison batch drawn only from these three sampled families, allocate `0` to `9e204e7ff3a2` until its known contract defect is repaired, `4` to `4ebdc8d865ce`, and `6` to `a16e387b682a`. The `4/6` split tests whether the three-demo schedule yields more authoritative distinct queries per rendered token without abandoning the stronger current semantic receipt on the five-demo source.

In parallel, allocate review effort—not training volume—to `9e204e7ff3a2`: add the exact canonical `RULE_HASH`, make the advertised exact overrides legal across their declared ranges or narrow the declaration, reject unknown keys, add focused tests, and retain one source/rule-bound four-query Racket episode. Only then may it enter the same comparison.

## Bounded experiment and stopping rule

For `4ebdc8d865ce` and `a16e387b682a`, attempt at most eight deterministic episodes per source and retain at most four. Use each source's intended demonstration count (`5` for `4ebdc8d865ce`; a complete `0/1/2` target-rank cycle for `a16e387b682a`) plus four distinct queries. Require current source and rule hashes, `self_check`, no exact duplicate inputs or episodes, real canonical Racket outputs, and demonstration-only checks against the named cheap rivals relevant to each rule. Record rendered tokens/cells, Racket seconds, attempted/accepted episodes, and authoritative query labels.

Stop a source immediately on any source/rule drift, Python/Racket disagreement, malformed grid, or query-label use in rival elimination. Suspend rather than upweight if fewer than two episodes survive eight attempts, if the same rejection reason occurs twice, or if a new canonical-fitting rival survives every retained demonstration set. Compare sources by accepted authoritative query labels per rendered token and per Racket second, with acceptance rate reported separately. Do not run a model; the experiment measures source quality and authoring cost only.

For `9e204e7ff3a2`, the first stopping gate is the repair itself: no volume experiment until the exact-override/unknown-key audit passes and the source declares/pins the canonical rule hash. After that, use the same maximum-eight-attempt protocol.

## Bottom line

The sampled default episode for `9e204e7ff3a2` looks teachable, but equal weight currently hides a larger readiness difference: a known unresolved source contract sits beside two reviewed-safe sources at weight `1.0`. The bounded alternative is to gate unreviewed sources before volume allocation, then compare accepted authoritative queries per cost among source-bound, four-query episodes. External ARC-GEN/RE-ARC quality remains an explicit coverage gap rather than an inferred ranking.
