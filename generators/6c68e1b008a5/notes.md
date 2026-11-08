# Working notes: 6c68e1b008a5

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-09-11 — isolated baseline, known limitations

The copied generator ran the full 12-stage baseline in ARCpuzzles v0.5 with
predecessor reads denied. Seven stages green, two advisory, three failed. Active
rule texts differ (sampled behavior agrees); palette range 4–6 misses canonical
7, canonical-profile/envelope support is 0/60, and no semantic contract is declared.
No source, rule or approval label changed. Resolve these findings deliberately in
a future review; migration execution is not a quality endorsement. Evidence:
[full battery](../../docs/migration/battery-evidence/receipt.json).
