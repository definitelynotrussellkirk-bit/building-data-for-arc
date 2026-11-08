# 1e7a6ba0bb90

Row 0 gives a transform key (1=clockwise, 2=left/right reflection,
3=up/down reflection) and an operation key (4=union, 5=intersection, 6=XOR).
Transform the left motif, align the two local origins, combine their occupancy
masks, and crop the result painted in color 8. Empty results are `[[0]]`.
Body motifs may use any two distinct colors 1..9, including the canonical 2/3.

Kind: `per_puzzle`. Selected repair version: `2.0.0`.
Default lessons use nine demonstrations with a seed-shifted nine-profile key
schedule. Exact controls cover dimensions, both keys, palette roles and the
relation between the transformed operands. See `notes.md` for the bounded
domain and source-bound teaching evidence.
Approval is derived by the catalog from current code and retained evidence.
