# Public-evaluation reasoning probe: `16de56c4`

This is a **separate source-bound proposal**, retained because the assigned public
focus is structurally unrelated to the selected `74a14031dc79` occupancy family.
It does not modify the production generator, claim verified lineage, or reveal
private evaluation labels.

Parent challenge:

- task: `16de56c4`
- split: public ARC evaluation
- canonical challenge SHA-256:
  `04f2c3b7aed8c16f787c41eb38d771d28bed8c54f4c649596974d8457a24edfd`

## Inferred rule

1. In both orientations, count `(line, color)` groups containing at least two
   same-color anchors. Select the orientation with the larger group count.
2. For each selected group, use the gcd of anchor gaps as its arithmetic-lattice
   step.
3. With no different-color point on that lattice beyond the anchors, extend the
   anchor color along the lattice to both grid edges.
4. A unique external different-color point on the same lattice is a terminal
   marker: use its color and fill only the lattice segment joining marker and
   anchors. Off-lattice distractors remain unchanged.

`solver.py` reproduces all 3 public training outputs exactly. The matching
proposed Racket implementation is retained in `rule.rkt` (SHA-256
`dc53ff9b90a291d3e35f56ca4cda17e1dcc66810787e2db2a15480ef67635593`) and is
executed over all demonstrations and queries. The implementation rejects tied
orientation evidence, internal on-lattice markers, and multiple terminal markers
instead of silently inventing behavior not identified by the demonstrations.

## Generate retained query predictions

From the outer packet directory:

```sh
python3 review.py run python3 \
  generators/74a14031dc79/workspace/public_focus_16de56c4/solver.py \
  --out ../checks/public-focus-16de56c4/prediction.json
```

The retained evidence forms one 3-demonstration/4-query proposed episode: the two
actual public evaluation queries plus two distinct support queries that exercise
horizontal terminal recoloring and vertical lattice extension. All seven outputs
are executed by the matching Racket source and checked against the Python probe.
The two actual public query predictions have SHA-256 values:

- `ad2b4472a20a70b73ac1df9bb0bf7884ab3148282568252a440b1268ad5de53a`
- `4d277732077141c6ca67662d6714f4c6bf93bb6866aed9d420610c875ad0c75a`

Those two predictions remain unverified because public evaluation query labels
are not available in this packet. The additional two outputs are labels only
under the proposed Racket rule; they are not hidden evaluation examples. The
focused tests pin both Python and Racket source identity, all training pairs,
four-query distinctness/parity, terminal/off-lattice behavior, ambiguity
rejection, and both public predictions.
