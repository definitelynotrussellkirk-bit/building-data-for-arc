# d75d93612b90

Variable-size 0-bg grid with: (a) one ORANGE(7) rectangular block (rh∈3-4 × rw∈3-5) at a random interior position; (b) one GRAY(5) strip of THICKNESS t spanning exactly one side of the block (top/bottom/left/right) so the rule's push = t ∈ {1,2,3}; (c) one isolated 2×2 orange block in the top-left corner (no gray contact). Rule: first recolor every gray(5) cell → yellow(4) and every orange(7) cell → gray(5) into a base result. Then for each orange block in the input, find total gray contact size and contact direction. Push = floor(gray_size / perpendicular_dim) cells from the contacted side. Re-paint that side's slice of the orange block back to orange(7); the remaining slice stays gray(5). Isolated orange blocks (no gray contact) revert entirely to orange(7) — staying unchanged from input.

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.
