# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Replay retained reference receipts

`replay_reference_receipts.py` checks the current task's mirror and validators
against saved public `arcpuzzles apply` outputs. It uses `reviewer_support` to
locate its own library/runtime, validates receipt/grid hashes and success flags,
and binds old receipts to a fresh anchor by both the selected rule hash and full
executed rule text hash. The anchor must name the current generator bytes; older
receipt generator hashes remain separate provenance. No Racket process is run
and no new labels are claimed.

From `WORK/repo`, replay the 408 retained mode-calibration grids:

```bash
../.venv-review/bin/python generators/d3575d4206d7/workspace/replay_reference_receipts.py \
  --anchor ../checks/code-review/followup_racket.json \
  --receipts ../checks/semantic-probe/mode-calibration/racket-*.json \
             ../checks/semantic-probe/mode-calibration/reverse-racket.json \
  --expect-count 408 --out ../checks/final-replay/replay-new.json
```

Supply explicit receipt paths to replay another bounded collection. The output
path must be new. Exit `0` means every mirror comparison and validator passed;
exit `1` reports mirror/validator failures; exit `2` rejects invalid evidence,
including stale anchors, mixed rules, corrupt grid hashes and failed reference
outputs. The report records current source hash, receipt hashes, accepted/rejected
counts, mismatches and the original input-source identities separately.

The current mirror's fallback tie behavior is calibrated for at most three
distinct noncyan uniform-row colors on pinned Racket 8.10. A wider tied palette
requires the Racket authority. Receipt replay does not expand that domain.

The review's two targeted negative checks are retained in
`checks/final-replay/negative_checks.py`: one corrupted grid hash and one stale
anchor source hash. They operate on marked copies and preserve prior receipts.
