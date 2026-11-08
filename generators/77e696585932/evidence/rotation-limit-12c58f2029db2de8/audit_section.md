## 77e696585932

**Reproduced rotation limitation: holding out the only cross removes the evidence for row-wins-ties. The existing lesson guard correctly rejects that rotation.** This is an order-dependent curriculum limitation, not a wrong generated label or a falsely accepting guard. The ordinary three-demo production orientation passed this bounded probe.

Audited selected generator version `2.0.0`, SHA-256 `be2ae4aed1cf23cb1fa18aa1223202c215df7a8e865277e308ec16b4a6dbc1b9`. The selected and actually executed canonical rule hash was `315cb8671701`; executed rule-text SHA-256 was `02ad883b4aaacb79f3490a03ed99e49a11afe49851e7197cf64fcf4256e29ac3`. The canonical record SHA-256 was `3720fdac2a08a3025525491fb1fa4a3f8f8ca00c76fddebd8552eb9ca1d4f143`. Before/after source hashes matched.

With seed **0**, difficulty **medium**, no overrides, and sample indices **0, 1, 2, 3**, the four inputs have profiles **rows, columns, cross, rows**. Canonical Racket supplied all four outputs. The original demonstrations at indices 0, 1, 2 and query at 3 produce no `lesson_identifiable` reasons; each of the five declared competitors is refuted by the demonstrations.

The allowed query rotation holding out sample **2**, with demonstrations **0, 1, 3**, leaves profiles **rows, columns, rows**. The independently implemented `tie_to_column` rival fits all three demonstration outputs and disagrees with the cross query. It also fits all **four canonical labeled pairs**, independently checked against Racket. In the 18x19 cross query, color-7 source **(8,14)** is distance 5 from full row **13** and full column **9**. Racket paints **(12,14)**; the rival paints **(8,10)**. Those are the two differing output cells. All coordinates are zero-based. All four generated inputs pass both `self_check` and `strict_canonical_like`.

The rotated lesson's own guard returns exactly:

- `demonstrations omit profiles ['cross']`
- `demonstrations omit the tie_row nearest-line branch`
- `query profile was not demonstrated`

Therefore this evidence must not be presented as an undetected production ambiguity. The source advertises an ordered three-example schedule and preserves that schedule in its normal orientation. If use requires every held-out-pair rotation to remain identifiable, this schedule does not meet that requirement; an additional cross demonstration or a richer per-input teaching design would be needed. Under the documented diagnostic-only rotation policy, this remains an explicit scope limit.

The current source-matching `evidence/review_index.json` already carries a separate unresolved nearest-versus-first parallel-line shortcut audit. That existing finding was read for context; this probe neither re-executed its hand input nor resolved it. Its text also mentions an earlier guarded rotation exploration, so the present result is independent corroboration rather than a claim of a novel defect.

Primary evidence: `checks/audit/77e696585932/evidence.json`. It retains exact generated and canonical grids, Racket outputs and authority receipt, rival predictions, every held-out-pair rotation, hook diagnostics, replay parameters, and source hashes. Runnable probe: `checks/audit/77e696585932/rotation_probe.py`. Recorder: `checks/audit/77e696585932/run_probe.py`. Exact subprocess command, working directory, source/script/stream/evidence hashes and exit code are in `checks/audit/77e696585932/command_receipt.json`; streams are `stdout.log` and `stderr.log` in the same directory.

Executed from `WORK/repo`:

```bash
/workspace/scratch/81253eacf5c6/packet/WORK/.venv/bin/python -B /workspace/scratch/81253eacf5c6/packet/WORK/checks/audit/77e696585932/run_probe.py
```

The recorder launches the packet's `run_with_racket.py` with the same runtime Python and the probe's explicit evidence destination. Both recorder and payload exited **0**, meaning the audit assertions and evidence recording completed. Scope: **four generated draws, four canonical labeled pairs, eight real Racket applications, and all four query positions of one materialized four-pair lesson**. No battery, broad override scan, target edit, shared-tool edit, or repair was performed.
