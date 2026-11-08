# b6592c220670

Read the nonzero codes in row 0 from left to right.  Crop the motif below the all-zero separator row to its bounding box, then apply every code to the previous state (1=identity, 2=rotate-CW, 3=flip-LR, 4=rotate-180).  Pack all intermediate states left-to-right with one zero column between them.  Motif colours are preserved; they may overlap the script colours.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.

Review distribution: every four consecutive ordinary draws contain a repeated instruction, which must execute again and emit another panel. General first-code-1 teaching slots end in code 2 to distinguish instruction order. Exact one-code overrides are exempt from repetition coverage. Compact connected motif masks remain a deliberate domain restriction.
