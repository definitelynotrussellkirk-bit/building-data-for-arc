# Review — `8eb9146172f8` proposed parametric extension

- Task/source: approved production generator `8eb9146172f8`, SHA-256 `84301bd12c17dbb0897847b4ddd15d66ee1e7fa0c74d4cafaa9f9a3480472d95`, rule hash `5592536df499`.
- Defect → repair: no retained parameter extension → separate task-local `step_size ∈ {1,2}` prototype with the canonical one-cell rule as exact default.
- Scope: production generator, canonical row, approval, catalog, dataset identity, and training admission are unchanged.
- Rule change: proposed setting `2` changes only the four signed `shift-val` constants; marker roles, traversal, clipping, and input domain are unchanged.
- Episode evidence: two fixed-setting episodes, each with 4 demonstrations and 4 distinct queries generated from the unchanged production generator.
- Authority: every label was executed by the packet's pinned Racket bridge and matched an independent Python loop (32 comparisons in the retained run).
- Teaching: demonstrations alone identify each setting against the sole declared rival; all four queries per episode also refute that rival.
- Public export: exact visible-byte IDs, no hidden settings/seeds/rules/query outputs, opaque-ID batch ordering, and private setting maps.
- Focused verification: final prototype plus unchanged production tests are recorded in `checks/parametric-final-tests.log`.
- Ticket replay: the pinned `0727bca3d518` witness reproduced exactly; its audit remains unresolved and was not cleared.
- Allocation ticket: built a seed-replayable static probe and a bounded 12-vs-12 shadow-allocation proposal; no live weights or boundaries changed.
- Remaining limit: bounded seeds and declared `{1,2}` rival family only; this return is proposed authoring evidence, not variant approval.

## Built artifacts

- `repo/generators/8eb9146172f8/workspace/parametric/prototype.py` — emits exact Racket for both settings, samples deterministic distinguishing inputs, executes Racket labels, checks a Python mirror, and writes separated public/private episodes.
- `repo/generators/8eb9146172f8/workspace/parametric/README.md` — exact commands, evidence contract, privacy boundary, and limits.
- `repo/generators/8eb9146172f8/tests/test_parametric.py` — canonical preservation, hand-derived geometry, Racket parity, deterministic episode selection, four-query identifiability, privacy/content addressing, invalid arguments, opaque-ID ordering, and exact rule-byte hashes.
- `checks/parametric-step-size/` — retained seed `2468` evidence for both settings. Public IDs are `4146adbfb5cfe09c204a2211626144f00fda1c47bdf4811d56bb863e97a7aba3` and `831088656eb446a502e0907b1b3c5806443c177ba3bceadab5b1cc0af25eb19f`.

## Supplementary tickets

### `ticket-7f261484c1c9689c` — audit replay

The exact source, review index, and audit-assets hashes matched their pins. The single allowed probe finished in 6.166 seconds and reproduced `source_sha256`, `rule_hash`, counts, canonical cases, and controls. The reproduced retained counts are 3 canonical cases / 0 canonical rival matches, 63 mirror matches, 24 default cases / 24 rival matches, and 36 override cases / 36 rival matches. This is a source-bound replay only; the existing audit remains unresolved. See `checks/tickets/ticket-7f261484c1c9689c/replay_summary.json`.

### `ticket-5f63d21523eda9b5` — allocation quality

The seeded records are `80271cb9b303`, `59a7762bc6da`, and `548c1010ce89`. The packet's 90% normal branch is uniform over 162 records and all 162 have catalog `mix_weight=1.0`, while retained review/teaching evidence differs materially. The shadow proposal preserves the 10% public-focus branch and all approval/training boundaries, then allocates the normal branch 50% to current actionable audits/exact teaching witnesses, 30% to missing review/Racket/four-query/parameter receipts, and 20% to uniform controls. Its bounded decision rule requires at least 25% more qualified deliverables per reviewer hour with no worse ambiguity/hard-failure rate. See `checks/tickets/ticket-5f63d21523eda9b5/allocation_report.json` and `proposal.md`.

## Failures and limits

- Identifiability is checked against exactly two declared settings, not arbitrary ARC programs.
- The retained prototype run covers one deterministic input set per setting within the production generator's current `9..20 × 9..22` domain.
- The allocation probe sampled only three records; missing keywords/files are treated as missing retained evidence, not proof that work never occurred.
- No production before/after battery or peer-wide battery was run because production behavior was not edited.
