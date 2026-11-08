# Bounded allocation-quality proposal

Ticket `ticket-5f63d21523eda9b5`; seed `0f5b1a79e7b735e5f7ba3e089f9c6aad4dc6b331c36b68619c8bc321d6d6a802`.
Seeded sample: `80271cb9b303`, `59a7762bc6da`, `548c1010ce89`.

## Observed allocation

The packet has 300 records, 164 main IDs, and 162 uniformly selected normal IDs. The public-evaluation focus remains 1/10; only 1 of 120 anchors has related generators in this packet, covering 2 IDs. The other focused anchors retain the normal task and act as inspired-extension prompts.

Normal-pool catalog mix weights are `{'1.0': 162}`. They are dataset sampling weights, not authoring-review priorities.

## Sample

| task | provenance | review state | key gap/finding | estimated gain/cost |
|---|---|---|---|---:|
| `80271cb9b303` | training | finite no-issue audit, needs triage | no task-local retained Racket receipt in this packet | 1.250 |
| `59a7762bc6da` | training | no review index | no current review index | 1.250 |
| `548c1010ce89` | augmented, training | current actionable audit | current-source actionable audit is unresolved | 3.000 |

The estimate is a transparent triage heuristic for marginal review leverage. It is not an approval score, source ranking, or measured model-data value.

## Alternative and stopping rule

Run a shadow allocator only: 50% current-source actionable audits/exact teaching witnesses, 30% missing review/Racket/four-query/parameter receipts, and 20% uniform controls. Keep the production 10% public focus, all approvals, catalog weights, and training boundaries unchanged.

shadow-select 12 normal-branch records with the current uniform allocator and 12 with the stratified allocator; cap each record at 20 reviewer minutes and one batched Racket-label receipt.

Primary metric: qualified deliverables per reviewer hour.

Stopping rule: stop the shadow arm after 6 records per arm if it has two hard integrity failures (source/authority mismatch, answer leakage, or duplicate-query padding) or uses >1.5x reviewer time with no additional qualified deliverable.

Decision rule: after 12 per arm, expand only if the stratified arm yields at least 25% more qualified deliverables per reviewer hour with no higher ambiguity or hard-failure rate; otherwise retain the current allocator.

## Coverage limits

- only three seeded records were inspected
- no sampled catalog row identifies ARC-GEN or RE-ARC provenance, so source-specific linter/rejection/grammar quality for those sources remains unknown
- the heuristic estimates marginal review leverage, not model accuracy or universal task quality
- task-local keyword absence may reflect missing retained receipts rather than missing historical work
