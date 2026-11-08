# Working notes: 038464cb9db1

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-db01808940396009:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `8645d0b174e895ba216f9157a7b8754744c868d3dfee82397033fc7b11938785`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/038464cb9db1/generator.py, unchanged SHA256 8645d0b174e895ba216f9157a7b8754744c868d3dfee82397033fc7b11938785. Explicit no_issue within documented four-consecutive-demonstration/fixed-query policy:53 actual reference calls31unique,24 ordered lessons cover8 start residues/3bands andall8 rivals refuted.120 rotations have0 rival ambiguities, but36hook failures (18missingtwo-row and18missingwidth1/2 boundary demo). These are unsupported control-presence failures, not rival ambiguity; no all-seed/full-battery claim. Source-bound proof: generators/038464cb9db1/evidence/bounded-ordered-policy-db01808940396009/manifest.json. Quoted basenames mean these exact target-local paths: `checks/audit/038464cb9db1/AUDIT_SECTION.md` `checks/audit/038464cb9db1/command.json` `checks/audit/038464cb9db1/probe.log` `checks/audit/038464cb9db1/probe.py` `checks/audit/038464cb9db1/report.json` `checks/audit/038464cb9db1/rotation-witness.json`

### Assessment or prior finding

## 038464cb9db1

**Verdict: No issue found in canonical output correctness or the tested ordered lesson policy.** The bounded audit found no surviving tested rival in 24 ordered lessons or 120 query-role rotations. A separate, reproduced **ordered-policy limitation (A2-ROT)** is retained below: the task's lesson hook rejects 36 of those rotations because a required demonstration control was moved into the query. These are hook-policy failures, not incorrect Racket labels or surviving query-changing rivals. The audit target was not edited, and this inspection grants no approval.

The canonical rule copies every input row intact into an output of height `h` and width `w+h-1`. Input row `r` starts at output column `h-1-r`; all padding is zero. The bottom row stays at the left edge.

### Source binding

- Generator SHA-256: `8645d0b174e895ba216f9157a7b8754744c868d3dfee82397033fc7b11938785` (the exact assigned version 2.0.0; unchanged after execution).
- Canonical normalized rule hash: `608d74db8ac9`.
- Exact canonical Racket text SHA-256: `d30c58a177ec430a2c711f32e1212d29f0f3ba2d3deb2fdbea5320138a5782e2`.
- Audit reproducer SHA-256: `fdb16acc22cd003237eee7eb385b3fee56cd1b1bfe5c4b18dc6c872e0c4aa6c6`.

`checks/audit/038464cb9db1/report.json` retains the exact program, source/rule hashes, protected Racket runtime identity, all inputs and executed outputs, per-grid results, ordered lessons, rotations, and rejection cases. Canonical labels were executed with the shared public `RacketBridge` and shared `wrap_rule`. No private runner functions or copied runtime were used.

### Checks actually run

| Scope | Result |
|---|---|
| All recorded canonical pairs | 6/6 match their recorded outputs through Racket |
| Scheduled inputs | 36 executions: seed 641, sample indices 0..11, each of easy/medium/hard |
| Explicit dimension/palette boundaries | 8 executions: seed 901, sample index 17, hard; includes 2x2, 2x15, 15x1, and 15x15 |
| Nonzero-color permutations | 3 executions: `c -> 10-c` on the first three canonical inputs; zero remains fixed; all commute with the rule |
| Total reference executions | 53/53 correct, representing **31 distinct input grids**; repeated fixed-profile inputs across difficulty bands are counted honestly |
| Ordered four-demo lessons | 24/24 accepted by the task hook; all eight tested rivals refuted |
| Query-role rotations | 84/120 accepted by the hook, **36/120 rejected**; all eight rivals refuted in all 120 |
| Invalid overrides | 11/11 rejected, including type/range/unknown-key and explicitly incompatible small-area cases |
| Malformed/out-of-domain grids | 9/9 rejected |
| Determinism, fresh returns, global RNG purity | Passed on seed 109, sample index 11, hard |

Every executed grid passed the generator's input validator, matched both its Python mirror and an independent direct row-copy construction, and produced the expected bounded output dimensions. The five declared rivals were supplemented with three independent alternatives: sort each row's colors before shearing, use palette size to control expansion, and transpose before shearing.

The 24 ordered lessons exhaust start residues 0..7 at seed 641 in each difficulty band, with four consecutive demonstrations and the fifth consecutive pair as query. The 120 rotations reuse those five-pair sets; they are overlapping diagnostic views, not 120 independent input samples.

### A2-ROT: reproduced ordered-policy limitation

There are 18 rotations lacking a two-row demonstration and 18 lacking a width-1/width-2 demonstration. In each case the only required control became the query. This is consistent with the source's documented guarantee for **four consecutive** demonstrations; it does not establish a default production-label defect.

Concrete witness: seed 641, easy, start 0, query position 1. Demonstration sample indices are 0, 2, 3, and 4, with heights 4, 6, 7, and 10. Query sample index 1 has a 2x4 input and an executed 2x5 output. The hook reports `demonstrations need a two-row boundary case`, although all five declared and three added rivals are already refuted by the remaining demonstrations. Full inputs, Racket outputs, and query rival outputs are retained in `checks/audit/038464cb9db1/rotation-witness.json`.

Keep the ordered policy explicit. Arbitrary query-role rotation support would require a policy or sampling change and its own evidence; the present audit makes no such claim.

### Exact execution and limits

Working directory: `/dev/shm/arc_review_9a465799211b/WORK`.

```bash
TMPDIR=/dev/shm/arc_review_9a465799211b/WORK/.tmp /dev/shm/arc_review_9a465799211b/WORK/.venv-review/bin/python run_with_racket.py /dev/shm/arc_review_9a465799211b/WORK/.venv-review/bin/python ../checks/audit/038464cb9db1/probe.py
```

Exit code: **0**. This command's success denotes the bounded reference/ordered checks described above; it does not erase the 36 explicitly retained rotation-hook failures. `checks/audit/038464cb9db1/command.json` records the exact argument array, environment, exit code, and log hash. `probe.log` contains the counts.

The probe did not run the target's existing test suite, a full battery, an isolated runtime snapshot, or a multi-seed census. Its conclusion is limited to the listed inputs, schedule residues, bounds, malformed cases, and eight rivals. Other conditional shortcuts remain outside this bounded audit. The read-only audit sources, programs, and input/output evidence are retained for replay.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
