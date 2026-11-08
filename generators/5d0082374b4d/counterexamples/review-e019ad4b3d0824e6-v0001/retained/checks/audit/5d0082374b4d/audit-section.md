## 5d0082374b4d

**Verdict: substantive teaching ambiguity independently reproduced; target unchanged.**

Audited generator version `2.0.0`, SHA-256
`f24326c752e2a0e3d1d38282d5f9da862a7c6e6889a600dcb7ce71f8bc289314`.
The public canonical Racket execution used rule hash `80261197592b`.
Canonical `rule!` source SHA-256 is
`7683ced9e9e5fa50e3640c92cf91bf771a8f0a8f641bebe8eead90cb05e5e64d`;
the public apply receipt separately identifies the lowered callable it executed
as `131d8217f4b5cfb221cfdcbd440cee3eb8adb656cde137c19d5570ad8c0a0b35`.

### A-5d0082374b4d-001 — a default lesson can leave marker overwriting unidentified

The intended rule fills every interior cell with alternating vertical stripes.
When an interior has odd width, the right input marker must be overwritten by
the left marker's color. A plausible competing rule fills only the zero interior
cells and preserves both colored input markers. These rules agree on every
even-width frame and differ at the right marker of an odd-width frame.

An independently rerun production episode demonstrates the ambiguity:

| Setting | Observed result |
|---|---|
| CLI seed / difficulty | `136` / `easy` |
| Demonstration policy | Omitted `--train`; production resolved three demonstrations |
| Accepted sample indices | `0, 1, 2, 3`, with zero rejections |
| Demo 0 frame interior widths | `4, 4` |
| Demo 1 frame interior widths | `4, 4` |
| Demo 2 frame interior widths | `6, 4` |
| Query frame interior widths | `3, 3` |
| Marker-preserving rival on demos | Fits all three Racket-labeled outputs exactly |
| Rival on query | Disagrees at two cells |
| Production lesson check | `status: not_declared`, `contract: none` |

The query disagreements use zero-based coordinates: `(1,11)` must become `2`
but the rival preserves `3`; `(4,3)` must become `9` but the rival preserves `5`.
The query answer was used only for evaluating that query, never as a
demonstration. The actual emitted episode is retained in
`checks/audit/5d0082374b4d/production.jsonl`; its four inputs and outputs match
the separate public `arcpuzzles apply` execution exactly.

**Cause and prior context.** Frame widths are sampled independently inside
`_layout_frames` (`generator.py`, beginning at line 408) and `generate`
(beginning at line 498). There is no executable lesson competitor or
identifiability hook. The existing focused test
`test_semantic_branches_and_shortcut_rebuttals_appear` checks that odd and even
widths occur across a pooled 240-draw population; it does not require the
distinction to appear in each lesson's demonstrations. Inherited associated
note `GNOTE-001240` recognizes that the right marker is an instruction, and
asks to retain odd/even coverage. This audit newly reproduces the concrete
seed-136 lesson failure; it does not claim the inherited result was rerun.
No `evidence/review_index.json` was present for this target.

**Minimal reduction.** `checks/audit/5d0082374b4d/minimal-witness.json` retains a
4×5 frame with top interior `[2,0,3]`. The canonical Racket output changes that
row to `[2,3,2]`; the competing rule produces `[2,3,3]`. The target's
`self_check` accepts the grid. It is the smallest single-frame reduction admitted
by the validator that exposes this branch. Normal generation uses larger
canvases and two or three frames; the separate production episode establishes
that the same ambiguity occurs in normal generated data.

**Suggested repair, not applied.** Add an executable marker-preserving
competitor and score each query against the actual demonstrations. Ensure a
demonstration contains an odd-width frame whenever the intended query behavior
requires overwriting a right marker. This can be implemented as a teaching
anchor or a lesson-level coverage condition without changing the canonical rule.
Retain the seed-136 episode as a regression case. Population-level parity
coverage alone does not discharge this obligation.

### Verification and limits

The public Racket apply command checked ten inputs: all four generated episode
inputs, the 4×5 reduction, and all five canonical pairs. All ten passed the
target's domain checker. Racket matched the independent stripe implementation
and the target's Python mirror on all ten; the five canonical outputs matched
their recorded labels. Therefore this finding concerns demonstration
identifiability, with no observed label-correctness failure.

The bounded search stopped at the first witness, seed 136, among the configured
range `0..1999`; it actually examined seeds `0..136`. This is one reproducible
lesson, not an estimate of ambiguity prevalence. The rival is introduced by
this audit, not declared by the target. Existing task tests were inspected;
the full battery and the existing test suite were not rerun.

All executed commands, working directories, timings, and exit codes are in
`checks/audit/5d0082374b4d/commands.json`. One initial audit-script verification
failed because it compared canonical source text with the public apply tool's
lowered-callable hash. The script was corrected to compare matching source
representations and retain both hashes; final verification passes. This was an
audit-script assertion error and involved no target modification.

Runnable reproduction (from the packet's outer root; public output files must
have new names when repeating generation/application):

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  ../checks/audit/5d0082374b4d/repro.py prepare
WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles \
  apply 5d0082374b4d --check-generator-domain \
  --input ../checks/audit/5d0082374b4d/inputs.json \
  --out ../checks/audit/5d0082374b4d/authority.json
WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles \
  generate 5d0082374b4d --count 1 --seed 136 --difficulty easy --test 1 \
  --out ../checks/audit/5d0082374b4d/production.jsonl
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  ../checks/audit/5d0082374b4d/repro.py verify
```

Evidence: `finding.json` contains the structured finding and exact query/rival
outputs; `minimal-witness.json` contains the reduction; `authority.json` is the
public Racket receipt; `verify-final.log` records the successful independent
comparison. All are under `checks/audit/5d0082374b4d/`.
