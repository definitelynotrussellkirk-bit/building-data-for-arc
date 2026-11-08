## Audit: c5905adcd2cb — ordinary lessons can omit the destination-decoder contrast

**Verdict: concrete teaching-identifiability finding; source remains unchanged.**
Audited generator SHA-256: `5d9cebc09f84a2107cc85ebac93abcdad80804818eaec6f3f0a5c501c1b67cfa`.
Pinned rule hash: `93e6c6c4b04f`; raw selected canonical program SHA-256:
`6ef97f7ff71c1a4b9c33cdb311d13f8e0b00d7957437dd06935748a7705a7f05`.

The canonical rule sends the marker's local `(row, column)` to the same macro-cell
coordinates. A simple wrong rule sends it to `(column, row)`, preserving source
selection, global clearing, copied payload, and local offsets. Three diagonal
marker codes do not distinguish these decoders. The selected sampler can emit
three such demonstrations followed by an off-diagonal query, while its current
`lesson_identifiable` checks only `drop_marker` and `preserve_distractors` and
returns no objection. The separate parametric prototype discussed in the notes
already identifies this direct/transpose distinction and requires off-diagonal
demonstrations; that protection does not apply to the production sampler.

### Exact ordinary production reproduction

`runner.run_one("c5905adcd2cb", seed=12, sample_index=0, n_train=3, n_test=1,
difficulty="easy")`, using the exact selected generator and canonical Racket
program, accepted indices 0, 1, 2, 3 in four attempts with no rejections.

| Role/index | Observed profile | Destination code | Transposed decoder agrees? |
|---|---|---|---|
| Demo 0 | light_destination | (2,2) | Yes |
| Demo 1 | marker_only | (0,0) | Yes |
| Demo 2 | public_4 | (2,2) | Yes |
| Query 3 | empty_destination | (1,2) | No |

All four inputs pass `self_check`; all four labels were produced by Racket and
match `rule_mirror`. The query copies four source cells to macro-cell `(1,2)`;
the rival copies them to `(2,1)`, producing eight differing pixels. For example,
pixel `(4,8)` is officially 3 and rival 0, while `(8,4)` is officially 0 and rival
3. The yellow marker is officially at `(5,10)` and incorrectly at `(9,6)`.
Baseline `lesson_identifiable(demos, query)` returns `[]`.

This is an omitted discriminator in generated teaching episodes, not a claim of
incorrect labels or a canonical-fitting shortcut: the transpose rival fails all
10 canonical pair occurrences (5 unique inputs), whose marker codes are all
off-diagonal. All 10 official outputs were checked through Racket and match their
retained labels.

A finite supplemental census used seeds 0–199, consecutive indices 0–3, and
difficulty `None`, easy, medium, hard: 800 four-pair lessons. It found respectively
5, 4, 5, and 3 accepted transpose-ambiguous lessons (17/800). Census labels used
the Python mirror; the complete retained counterexample and all canonical pairs
were independently executed through Racket. This is a finite measured scope,
not a probability guarantee or exhaustive search over ARC programs.

### Strict audit and environment limitations

The required public strict preset was executed with `--stage audit --phase audit`
and timeout 1800. Its first attempt passed all 118 tests plus 5 subtests; semantic
gate log reported PASS with strict 600/600, canonical 10/10, both declared
witnesses and rival claims verified, 12/12 lessons identifiable, and 0/48
diagnostic rotation ambiguities. However, the controller failed with `Errno 28`
while writing its completion checkpoint, so that first attempt is **incomplete**
and is not counted as an overall pass. Its original result is retained as
`strict-initial-result.json`. Public `--resume` was tried and explicitly rejected
because the audit preset does not support it. One serial fresh retry is recorded
under `strict-retry/`. The retry completed successfully: exit code 0, overall
`passed=true`, both requested stages completed, 118 tests plus 5 subtests passed
and semantic gate passed. Source hashes remained unchanged. The earlier
environment failure and unsupported-resume response remain retained.

The green named-rival semantic results do not cover the independently reproduced
transpose decoder. No selected generator, tests, notes, authority, contracts, or
shared tools were edited, and no approval was issued.

### Proposed owner action and evidence

Add the transpose decoder to lesson competitors and ensure demonstrations contain
an off-diagonal marker code whenever an off-diagonal query needs that contrast.
For arbitrary held-out-query rotations, retain at least two such distinguishing
pairs per four-pair lesson. Preserve valid diagonal inputs and canonical profile
support; this can be a lesson-level witness condition instead of a narrower input
validator. This audit supplies findings only and does not implement that repair.

Evidence is local to `WORK/checks/audit/c5905adcd2cb/`: `probe.py` contains the
independent rival and source-bound reproduction; `reproducer.json` retains the
complete official production episode, rival query output, pixel differences,
canonical checks and census seeds; `commands.json` retains exact command arrays,
working directories, environment settings and statuses. `strict/` and
`strict-retry/` retain the public preset results and logs.

The current `probe.py` was subsequently corrected for portability: it uses the
public `Catalog.get`, `RacketBridge`, `strip_rule_wrapper`, `GeneratorBundle`,
and `run_one` interfaces. It creates no synthetic `scripts` package and calls
no private runner functions. The canonical program is already a self-contained
lambda, so stripping its `rule!` wrapper supplies the public bundle's callable
without legacy source-conversion imports. The prior probe and JSON remain under
`history/superseded-private-runner/`, explicitly labelled superseded in
`STATUS.json`. A fresh low-memory replay completed with exit 0 using:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 review.py run python3 ../checks/audit/c5905adcd2cb/probe.py
```

That replay asserts exact agreement with the superseded evidence for the full
accepted episode, pair details, rival query output, eight differing pixels,
lesson-identifiability result, ten canonical checks, and all census seed lists.
All comparisons passed: the finding and its finite 17/800 scope are unchanged.
The updated command and evidence hashes are recorded in `commands.json` and
`evidence-hashes.json`; the strict preset was not rerun for this probe-only
portability correction.
