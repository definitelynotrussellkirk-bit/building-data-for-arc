## df5e596e5e96

**Finding — generated lessons omit the rotation-before-reflection priority needed for symmetric supports.** This is a teaching-coverage finding against selected generator SHA-256 `7eaedfe24e1c2faba9192e342314ad541f643291b3f17397db4754c9effb2ae3`, version `3.0.0`. No audited target source or authority was edited. The current notes and the earlier `review-ecb9eab7828409d2:v0001` repair were used as leads; the current audit index contains no unresolved earlier audit. That repair successfully addresses count/color shortcuts, but its declared rivals do not cover this precedence case.

The concrete rival keeps the cyan diagonal and exact-match priority, then tests reflected rotations before ordinary rotations. For asymmetric objects, the two orbits are disjoint and this rival agrees with the reference. For a symmetric object, a distinct rotation can also be a reflected rotation; the reference must return `2`, while the rival returns `3`. The generator constructs transformed related objects from fully asymmetric motif A. Motif B appears as an unrelated object or an exact duplicate, without a distinct rotated symmetric B partner. This construction does not teach the missing priority.

**Observed evidence.** The separate Python-mirror census checked 1,536 generated inputs: seeds `0..15`, sample indices `0..7`, difficulty `None/easy/medium/hard`, and `n_panels=3/4/5`. All passed `self_check`; the rival matched the selected Python mirror on 1,536/1,536. These counts are not claimed as 1,536 Racket executions. A single supported `arcpuzzles apply` batch independently executed 54 inputs: 48 generated anchors spanning all four difficulty values, all three panel counts and all four schedule slots; all five canonical pairs; and one minimized lawful witness. All 54 authoritative outputs matched the expected labels, with no per-input errors. The rival matched 48/48 generated anchors and 4/5 canonical pairs.

The failing canonical pair is **variant 0, train index 3**. Its eight off-diagonal rotation entries should be `2`; the rival returns `3`. This is therefore an omission of an existing canonical lesson, not a shortcut that fits every canonical example. Its full input, authoritative output and rival output are retained in `checks/audit/df5e596e5e96/canonical-lesson-witness.json`, with the independent reference receipt at `checks/audit/df5e596e5e96/racket.json`.

The minimized witness is a **5×17** input containing three lawful four-cell panels: a T tetromino, its distinct quarter-turn, and an unrelated L tetromino. It satisfies both `self_check` and `strict_canonical_like`. The authoritative matrix is `[[8,2,0],[2,8,0],[0,0,8]]`; the rival predicts `[[8,3,0],[3,8,0],[0,0,8]]`. Complete grids and outputs are in `checks/audit/df5e596e5e96/lesson-witness.json` and `checks/audit/df5e596e5e96/assessment.json`.

Three ordinary generated demonstrations—seed `1700`, sample indices `0,1,2`, difficulty `None`, exact `n_panels=5`—all fit the rival. After those demonstrations, the selected `lesson_identifiable` hook returns `[]` for **both** the minimized witness and the unaltered canonical train-index-3 input used as a query. Both query outputs were obtained from the supported Racket batch. This is a concrete missing-rival/teaching-support case; it is not a sampled mislabel or a claim of universal hypothesis identification.

**Authority binding.** Catalog and executed normalized rule identifiers both equal `dd7b7aac9913`, and `rule_hash_matches_catalog=true`. The exact canonical program SHA-256 is `dd7b7aac9913cfda3671bc02b7b8af33716140dd90702a08af92f45f4f8383e4`; the reference runner's wrapped executable-text SHA-256 is `219cd4d43be4ba0a5c299f021748ac0b60a0d7f32368beaa7159c3afb5d3fdff`. These are different hash representations, not an authority mismatch. The ledger, probe and generator hashes are retained in `checks/audit/df5e596e5e96/assessment.json`.

**Suggested repair.** Add ordinary lesson support for a rotated symmetric motif pair, alongside the existing asymmetric and same-count-unrelated witnesses, and declare this reflection-before-rotation rival. Preserve exact-match precedence and the pinned canonical Racket rule. This audit makes no repair or approval claim.

**Reproduction and scope.** Retain the complete `checks/audit/df5e596e5e96/` folder. `probe.py prepare` materializes the exact 54 inputs and the bounded mirror census; `probe.py summarize` checks the reference receipt and produces the assessments and complete lessons. Actual commands, outer/effective working directories, exit codes and logs are recorded in `checks/audit/df5e596e5e96/commands.json`; all final audit commands exited `0`. The reference invocation was:

```sh
WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles apply \
  df5e596e5e96 --input ../checks/audit/df5e596e5e96/inputs.json \
  --reference canonical --timeout 180 \
  --out ../checks/audit/df5e596e5e96/racket.json
```

It ran from the outer extracted packet directory, with payload cwd `WORK/repo`. Use a fresh receipt path when replaying. The census is finite; the broader 1,536-input count is mirror-based, and only the identified 54 inputs received this audit's new Racket execution. No blanket battery was run for this findings-only audit.
