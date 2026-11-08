## 7017b91a367d

**A2-7017-1 — Reproduced teaching ambiguity in one generated production lesson.**
Audited generator SHA-256: `8f48fb04488be1f42a863fb60eb4587aaa433a5c4c560345cedd251ec3c700dc`.
Selected rule hash: `aa994ed25e88`; canonical program SHA-256:
`aa994ed25e886084192847f7a0e2c5dab413df7cb804c24a227b0e3873ce880a`.
The public apply receipt additionally identifies the converted executable Racket
callable as `8bf53e0b393f1210979931c4aeb58a9885945125a795f583f83a3e4a3ea29bb1`.
Exact source snapshots and hash meanings are retained under
`checks/audit/7017b91a367d/` in `source.json`, `audited_generator.py`, and
`audited_rule.rkt`.

The public `arcpuzzles generate` command produced a hard lesson at **seed 4,
requested sample index 0**, with three demonstrations and one query. Its actual
accepted indices are **[0, 1, 2, 3]**, with no rejections and four distinct inputs.
The independent public `arcpuzzles apply --check-generator-domain` command
recomputed all four outputs through the selected Racket authority: **4/4 valid
outputs, 4/4 inputs accepted by the current validator**, and exact agreement with
the retained production episode. Each input is 5 rows × 17 columns; each output
is 5 rows × 5 columns.

The input-only rival `ignore_left_singletons` performs the count map except that
it erases cells occupied only by the leftmost panel. None of the three
demonstrations contains that occupancy case. The rival therefore matches **3/3
demonstration outputs**, but differs from the query at the zero-based local
coordinate **(row 3, column 3): Racket outputs 2; the rival outputs 0**. This is a
production-order ambiguity on the exact materialized lesson. A separate
query-rotation census was not run; its verdict is **unknown**. The current
`lesson_identifiable` hook returns `[]`. Its existing `central_3x3_only` rival is
refuted by two of these demonstrations, so the existing border repair does not
address this positional-role alternative.

**Evidence and replay.** `checks/audit/7017b91a367d/finding.json` records the exact
comparison, all four input/output hashes, source binding, and current declared
rival results. `production.jsonl` retains the complete production episode and
accepted-index metadata; `input.json`, `racket.json`, and `rival.json` retain the
independent authority check and rival predictions. `probe.py prepare` recreates
the inputs, and `probe.py verify` compares the materializer, Racket receipt, and
rival. Exact wrapper argument arrays, working directories, exit statuses, and
evidence paths are in `commands.json` in the same directory.

**Root cause and proposed follow-up.** The three-position schedule guarantees
border occupancy and all total count levels, but does not guarantee that the
demonstrations teach singleton occupancy for each individual panel. Consider
declaring the three panel-specific singleton-erasure rivals as lesson competitors
and ensuring a refuting demonstration when one changes a query. This rival is
**not** a canonical shortcut: the probe matches only **3/5** original canonical
pairs. The finding concerns the teaching support of this particular generated
lesson; it does not contradict the earlier finite checks of the declared
central-only rival.

**Scope and disposition.** Findings-only; the target generator, its notes, and
all shared sources remain unchanged. The discovery probe examined hard seeds
0–4 with four draws each; this small selected search is not a population failure
rate. One production episode and four Racket applications were retained; no full
battery or staged task-test suite was run. Two initial audit-verifier failures
were harness schema mistakes (the generation hash is under `provenance`, and
the apply hash covers the converted callable). Their script snapshots and logs
are retained, followed by a successful corrected verification; neither failure
is attributed to the generator. The older audit entry on different source bytes
is not resolved or reopened by this finding.
