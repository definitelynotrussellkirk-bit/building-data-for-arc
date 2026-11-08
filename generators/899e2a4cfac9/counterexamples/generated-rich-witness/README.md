# Exactly emitted rich witness

The frozen version 2.1.0 source emits this 6x7 input under:

```python
generate(seed=3298638998, sample_index=93, difficulty="easy")
```

There are no overrides. It has seven same-color four-connected foreground components, five total colors including zero, four border objects, and three survivors of sizes 1, 2, and 3.

Input:

```text
0330000
0066610
0000000
3002200
0000022
0001000
```

Authoritative output:

```text
0000000
0066610
0000000
0002200
0000000
0000000
```

All twelve entries in the actual final `LESSON_COMPETITORS` declaration disagree with this output. The retained provenance includes their exact outputs and differing coordinates. The surviving color-2 domino diagonally touches a border color-2 domino, so same-color eight-connectivity fails. The surviving color-6 bar is orthogonally adjacent to a border color-3 domino, so all-nonzero four-connectivity fails. Interior color 1 survives despite a disconnected bottom-border occurrence of the same color. The interior singleton beside two larger survivors defeats singleton deletion and largest-interior-only selection. Isolated top, bottom, left, and right contacts defeat each edge omission. The right-border domino has an interior cell, defeating perimeter-cell-only erasure.

`input.json` and `expected.json` retain the exact grids. `reference.json` is the direct public Racket application receipt. `provenance.json` retains seed/index/difficulty, no overrides, exact regeneration equality, `self_check=[]`, final census source, input/output hashes, rule/source hashes, and all rival outputs. The record was copied from `WORK/checks/generated-witness/witness.json` and cross-checked against `WORK/checks/generated-witness/racket.json`; expected output was not synthesized during documentation finalization.

Generator SHA256: `0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5`. Executed canonical rule hash: `50ed982b7d21`. Rule-text SHA256: `e3be5a37984b21bbb87a5d1347a612058e29f5c34c30306dbe716914a789fcc3`.

To replay reference application from the review packet's `WORK` directory:

```bash
python3 run_with_racket.py python3 -m arcpuzzles apply 899e2a4cfac9 \
  --input generators/899e2a4cfac9/counterexamples/generated-rich-witness/input.json \
  --out generators/899e2a4cfac9/counterexamples/generated-rich-witness/replayed-reference.json
```

In an installed standalone checkout, run the same payload without the packet wrapper from the repository root. Require its first result's output to equal `expected.json` and its executed rule hash to match the retained authority. This is exact positive emission and finite refutation evidence for one input, not proof against arbitrary hypotheses or approval/training admission.
