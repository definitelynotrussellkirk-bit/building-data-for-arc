# Visible-only solve work log

## Scope and exposure

This solver read only `README.md`, `challenge.json`, and its own Python work in
`WORK/solve`. It has not read generator source, Racket rules, canonical data,
reference solutions, private labels, earlier solve explanations, or hidden review
state. The coordinator had source exposure before this isolated solver was
assigned. Consequently, the overall episode must record earlier exposure as
**yes**, while reference consultation by this solver is **no**.

These notes are a concise record of hypotheses and experiments, not a token-level
reasoning trace. No prior failed attempt has been invented.

## Initial observations and hypothesis

Input and output dimensions are independent. The visible training shapes are:
7 by 10 -> 3 by 3; 7 by 11 -> 4 by 4; and 8 by 9 -> 4 by 3.
The two public query inputs are 7 by 11 and 8 by 9; their true output shapes and
contents are withheld.

Each training output keeps the color and bounding box of the largest component
connected through shared edges. In example 1, the other color has more cells in
total but is split into two components, so selecting the most frequent color
would be inappropriate.

The proposed transformation is a simultaneous removal of component cells whose
four orthogonal neighbors all belong to the same component. This predicts the
central hole in example 0 and the two central holes in example 2. In example 1,
the pre-existing hole prevents removal of its immediate neighbors; only the
opposite interior cell is newly removed. This distinguishes the hypothesis from
blanking the entire bounding-box interior or requiring all eight neighbors.

Next probe: measure shared-edge component sizes, compare those three removal
rules against the visible outputs, and implement the rule if the evidence holds.

## Probe 1 and implementation 1

Command: `python3 WORK/solve/probe_components.py` from the packet root.
Exit status: 0.

The four-neighbor rule matched all three visible examples. The eight-neighbor
and full-interior alternatives each matched examples 0 and 2 but failed example
1, as expected from its pre-existing hole. The observed component sizes were
9/1/3, 9/15/8, and 12/4/4 respectively. The selected component had no size tie
in any visible training example.

Implemented `solve(grid)` using same-color shared-edge components, choosing the
largest by cell count, computing removals simultaneously from that component,
and returning its original bounding box. Non-component cells in the crop are
background zero. Ties, which the visible examples do not specify, are resolved
by first occurrence in row-major order. No solution revision has yet been needed.

Next check: submit this implementation to the public visible-example checker.

## Public check 1 and stopping decision

Command:

```sh
python3 review.py solve check --intent solve --note 'Largest same-color component with shared-edge connectivity; simultaneously clear cells having four component neighbors. This matched all three visible examples in a local probe and distinguished the existing-hole case from eight-neighbor and full-interior alternatives.'
```

Exit status: 0. The checker recorded revision 1, execution status `completed`,
and **3 / 3 visible examples passed**. It reported label `unknown` and
`training_admitted: false`. No hidden correctness result was provided or inferred.

Stopped with the first submitted implementation: the visible examples agree
with the proposed rule and the public check found no execution problem. There
was one component probe and one public solve check; no failed submitted attempt
or implementation revision occurred. The alternatives rejected in the local
probe remain recorded above. Private-query correctness remains unverified.

Finish declaration: earlier exposure **yes** for the overall episode because
the coordinator had source exposure; reference consulted **no** for this
isolated visible-only solver. This distinction does not establish a clean
holdout result for the overall review.
