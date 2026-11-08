# 95d9a7d908ea

0-bg grid (h ∈ 9-13, w ∈ 11-16) with: n ∈ 2-5 SCATTERED MULTI-CELL CONNECTED MOTIFS, each a 3-5 cell motif (built via _build_motif random adjacent-step walk), each in a DISTINCT non-bg color drawn from {2..9}, placed at random non-overlapping positions via _free check (1-cell padding). Per-task semantics aim at tile-the-component-with-most-holes: motif with the largest enclosed-area is the target. Rule (FIND THE COMPONENT WITH THE MOST HOLES — IE, MOST ENCLOSED BG-CELLS WITHIN ITS BBOX OR CONVEX HULL — TILE IT OR EMIT IT AS THE ANSWER PER DEMOS): For EACH motif: COMPUTE the number of HOLES (interior bg cells trapped within the motif's bbox/region). SELECT the motif with the MOST holes. CROP it to its bbox. TILE / EXPAND / EMIT per the rule's canonical output for this task. Net: most-holed motif is extracted and emphasized as the answer.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
