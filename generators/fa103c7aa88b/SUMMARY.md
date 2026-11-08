# fa103c7aa88b

0-bg grid (size varies). Cell (0,0) holds the OP KEY: 1=union, 2=intersection, 3=symmetric-difference. Elsewhere are TWO LARGE partially-overlapping component shapes (when each is cropped to its bbox top-left they share some cells and each has private cells) plus 0-2 SMALLER distractor components. Every component is a distinct color != the key. Rule: read the key at (0,0); zero out all key-valued cells; find the TWO LARGEST remaining components; crop each to its bbox; apply the set op of their cell sets (union / intersection / symmetric difference); CROP to the result bbox and paint it color 8. Smaller distractors are ignored. (Was two tiny 3-5 cell shapes with no guaranteed overlap.)

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
