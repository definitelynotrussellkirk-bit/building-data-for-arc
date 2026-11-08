## 8096ecc43d5a

**Status: Reproduced teaching ambiguity in an ordinary production lesson.** No audited source was changed. The Racket labels are correct; the demonstrations can leave a simple wrong meaning for one instruction unresolved. The production sampler still reports `passed_declared_rivals`, because that meaning is outside its twelve declared rivals.

**Source binding.** Audited `repo/generators/8096ecc43d5a/generator.py`, version `3.0.0`, SHA-256 `0a7333474bb418b62192c1c7a9ee8a8bb92a9480b109811bceb0eac71b5d85fc`. Canonical Racket source SHA-256: `04788c0240d6550baf1344b31b28de075108d0b89dcfe18faf5f1615115fd17c`; executed rule hash: `04788c0240d6`. `checks/audit/8096ecc43d5a/report.json` also binds the current notes, four test files, canonical ledger, helper, and enumeration probe. The raw `Catalog.apply` receipt retains its separate executable-wrapper hash.

### Concrete production counterexample

Run `Catalog.generate("8096ecc43d5a", count=1, seed=2, difficulty="easy", n_train=3, n_test=1, sample_index=0, overrides={}, reference="canonical", allow_unapproved=True)`. The public production API accepts sample indices `[0,1,2,3]` with **zero rejections** and uses actual Racket execution for all four labels.

The rival uses exactly the intended rule except that **code 3 means left–right reflection rather than a half-turn**. Codes 1, 2 and 4 retain their intended meanings. It matches all three demonstrations:

| Index / role | Script | Cropped motif | Racket output, also predicted by rival |
| --- | --- | --- | --- |
| 0 / rich_b | `[4,1,1,1]` | `[[9,0,0],[9,9,9],[0,9,0]]` | `[[0,9,0],[9,9,0],[0,9,9]]` |
| 1 / free | `[3]` | `[[9,9],[9,9],[9,9]]` | `[[9,9],[9,9],[9,9]]` |
| 2 / singleton | `[4]` | `[[0,6,6,6],[6,6,0,0]]` | `[[6,6,0,0],[0,6,6,6]]` |

The only demonstration containing code 3 is a solid rectangle, so its half-turn and left–right reflection coincide. The query at index 3 uses script `[3,4,1,1,1]` on an asymmetric motif. Its full input is:

```json
[
  [0,3,4,0,1,0,1,0,1],
  [0,0,0,0,0,0,0,0,0],
  [0,4,4,0,0,0,0,0,0],
  [0,0,4,4,4,0,0,0,0],
  [0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0]
]
```

- Actual Racket query output: `[[4,0],[4,4],[0,4],[0,4]]`.
- Rival query output: `[[0,4],[4,4],[4,0],[4,0]]`.
- Among all **4,096** constant D4 codebooks, **32** fit these three demonstrations and **24** disagree with the query label. Every declared rival is refuted.

Full demonstration inputs, labels, rival outputs and the recipe are retained in `checks/audit/8096ecc43d5a/production_witness.json`; the unabridged production receipt is `checks/audit/8096ecc43d5a/production_episode.json`. This rival fails two of the four canonical pairs. Those pairs are absent from the generated lesson, so excluding it because of canonical evidence does not make this lesson sufficient to distinguish it.

### Bounded checks and reproduction

The enumeration probe used seeds **0..3**, sample indices **0..3**, all three difficulty bands, and no overrides. A single `Catalog.apply` call freshly executed **52 input evaluations**: four canonical pairs and 48 generated draws. All 52 had valid outputs and passed the generator-domain check; all four canonical outputs matched their recorded labels. Because bands overlap, this is **28 unique inputs**, including **24 unique generated inputs**, not 52 independent cases.

The 12 seed/band windows represent 10 distinct ordered lessons. The expanded codebook family found query ambiguity in **10/12 ordered windows (8/10 distinct lessons)** and **38/48 query rotations (32/40 distinct rotations)**. All twelve declared rivals were refuted in every rotation. The focused production replay executed four previously counted inputs again, bringing the actual reference-execution total to **56 evaluations over 28 unique inputs**.

Both commands below exited **0**. Their actual outer working directory was `/workspace/scratch/5fe85a58d517/arc_review`; the wrapper ran payloads from its `WORK/repo` directory:

```bash
.venv/bin/python review.py run /workspace/scratch/5fe85a58d517/arc_review/.venv/bin/python ../checks/audit/8096ecc43d5a/probe_codebooks.py > WORK/checks/audit/8096ecc43d5a/probe.log 2>&1
.venv/bin/python review.py run /workspace/scratch/5fe85a58d517/arc_review/.venv/bin/python ../checks/audit/8096ecc43d5a/reproduce_production.py > WORK/checks/audit/8096ecc43d5a/production.log 2>&1
```

Reusable probes, the complete 52-input Racket receipt, per-window results, and the first enumeration witness are retained respectively in `checks/audit/8096ecc43d5a/probe_codebooks.py`, `checks/audit/8096ecc43d5a/reproduce_production.py`, `checks/audit/8096ecc43d5a/racket_apply.json`, `checks/audit/8096ecc43d5a/report.json`, and `checks/audit/8096ecc43d5a/witness.json`. The compact witness above is the separately verified production witness. `checks/audit/8096ecc43d5a/verification.json` records deduplicated counts, command receipts and evidence hashes.

**Scope and limits.** This finding extends the tested hypothesis family; it does not contradict the notes' explicitly limited twelve-rival guarantee. No full battery or task-test suite was rerun, no repair was attempted, and no solve/private-query artifact was opened. These small, overlapping seed/band counts are not a population-rate estimate or proof about arbitrary programs. A suitable follow-up is to check query agreement across all constant D4 codebooks that fit the actual generated demonstrations, without first excluding maps using canonical labels that the lesson does not show, then resample or strengthen ambiguous lessons.
