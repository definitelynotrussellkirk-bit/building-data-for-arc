# a286b2610efc — Complete straight segments

Place exactly two isolated, differently colored dominoes on a black (`0`) background: one horizontal and one vertical. The pinned rule scans every horizontal and vertical length-3 window in the **original input**. It fills the zero in `0,v,v` and `v,v,0`.

Consequences:

- A boundary-flush domino has one in-grid extension and becomes length 3.
- An interior `0,v,v,0` domino belongs to two overlapping windows, so both adjacent zeros are filled and it becomes length 4.

Generator version: `3.0.0`  
Pinned rule hash: `2e117d692607`

The default curriculum alternates `edge` and `interior` layouts by `sample_index`; every three-example lesson therefore includes both. This refutes the strongest canonical shortcut, `one_sided_triplet_completion`, which extends each domino only once. Default dimensions stay on the canonical shape envelope (`7x8` or `7x9`), while exact overrides cover heights `7|8|9`, widths `8|9|10`, and both layouts.

The generator declares a strict semantic contract, observable overrides, a Python rule mirror, the canonical shortcut, a rival-refuting witness, and an identifiable-lesson schedule. The 2026-10-02 review battery passed all 12 stages.

Kind: `per_puzzle`. Approval remains catalog-derived from current code and retained evidence.
