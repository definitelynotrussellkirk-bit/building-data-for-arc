# ticket-684825f5c790f7f2 — bounded allocation-quality proposal

## Current source and pool status

The pinned generator SHA-256 is current. The catalog and assignment both name rule hash `57d7715bb63d`; canonical source equals the base archival `raw_code`, while the selected base `target_code` is not byte-identical. The assignment remains `pending`, `monitor_gate_status: unreviewed`, and `train_safety: unsafe`, with unresolved `missing_rule_hash`, `rule_source_divergence`, and historical defect-lint remeasurement items. The task has no task-local tests and no parametric evidence manifest.

The current tier-1 live-pool construction admits only `reviewed_safe` rows with positive recommended weight, a generator, and canonical Racket authority. It yields 113 equal-weight tasks and correctly excludes `22ee9e5c3a9a`. In contrast, the legacy deficit-sampler weight file gives this task weight `1.0`, it is not blacklisted, and its nominal share among positive legacy weights is about **0.344%** (`1 / 290.5`). Thus the safety-gated and legacy pools disagree materially: the former quarantines this source; the latter can sample it at ordinary weight.

## Seeded three-record comparison

Using the ticket seed, weighted sampling without replacement from the current tier-1 pool selected:

| Task | Safety/review state | 3 demos + 4 queries | Exact duplicates | Max side | Sides ≥20 |
|---|---|---:|---:|---:|---:|
| `46b45dd2aff8` | reviewed-safe, complete, monitor pass | 7/7 clean | 0 | 23 | 6/7 |
| `ebe910be6876` | reviewed-safe, complete, monitor pass | 7/7 clean | 0 | 12 | 0/7 |
| `19c5f15066d3` | reviewed-safe, complete, monitor pass | 7/7 clean | 0 | 25 | 6/7 |
| focal `22ee9e5c3a9a` | unsafe, pending, unreviewed | 7/7 mechanically clean | 0 | 13 | 0/7 |

All four probes used the canonical Racket rule, produced four distinct query inputs, changed every output, and had no `self_check` errors. This is execution and exact-dedup evidence only; it does not establish semantic identifiability or training value. The focal source accepts a validated hard override at `grid_h=18, grid_w=18, n_lines=8`; a 20×20 request is rejected because the hard draw bound is `[13,18]`. It therefore cannot directly repair the training snapshot’s 20–30-side representation gap.

The packet contains only aggregate ARC-GEN and RE-ARC token shares (16% and 11%). It includes no source-specific ARC-GEN/RE-ARC linter, rejection, repair, ambiguity, grammar, or dedup receipts, so no quality-per-cost comparison against those libraries is supportable here.

## Alternative allocation experiment

**Recommendation: retain production allocation at zero for this task.** First resolve authority metadata, run the task’s full review/monitor battery, add focused tests, and obtain `reviewed_safe` status. A clean seven-pair probe is not a substitute for those gates.

After that repair, run one offline, source-bound comparison with no mixture change:

- Materialize 32 focal episodes: 16 default and 16 hard episodes pinned to `18×18`, `n_lines=8`; each episode has three demonstrations and four queries.
- Materialize 32 equal-cost control episodes, round-robin over the three seed-selected reviewed-safe controls.
- Cost: 64 episodes, 448 Racket labels, exact-hash deduplication, and no model job.
- Record acceptance/rejection reasons, Racket crashes, `self_check`, four-query distinctness, exact pair duplicates, changed-output rate, side distribution, declared-rival/ambiguity results, and source/rule hashes.

**Stopping rule:** stop immediately on an authority mismatch, Racket crash, self-check rejection, exposed query answer, within-episode duplicate query, or semantic ambiguity. Do not consider admission unless the focal task is `reviewed_safe`, all 32 focal episodes are accepted, all 128 focal queries are distinct within their episodes, exact pair duplication is below 5%, and its semantic gate has no unresolved rival. Even on success, the estimated representation gain is modest because the family tops out at side 18 and overlaps an existing endpoint family; admission should use the standard safe-pool weight rather than an unsupported upweight.

The estimated quality per labeling cost currently favors the reviewed-safe controls: they provide the same clean four-query yield with complete review evidence, and two of three also supply ≥20-side representation. The focal task’s prospective value is family diversity, not large-grid coverage.
