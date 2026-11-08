# 1a4459f1a38f

On background 0, find the same-color **4-connected** components. Select the unique component with the greatest **cell count**; generated lessons forbid ties. Return the rectangular crop of the original input at that component's bounding box, preserving its color, holes, and indentations. Distractors stay outside the selected bounding box.

Version `4.1.1` uses a four-slot curriculum: canonical hollow frame, larger-bbox/smaller-cell decoy, repeated-target-color decoy, and an irregular target. The repeated-color and irregular slots place a same-color distractor in diagonal contact so 4- and 8-connectivity predict different crops. The irregular slot also repeats the modal-color and bbox-area counterexamples, which makes every three-demo sliding lesson reject the named shortcuts instead of only schedule-aligned lessons. A separate bbox-decoy anchor preserves the canonical `10x10` / four-color profile rate.

Kind: `per_puzzle`. Rule hash: `f1a4398aee4e`. The canonical Racket authority was not changed. Approval is derived by the catalog from current code and retained evidence.
