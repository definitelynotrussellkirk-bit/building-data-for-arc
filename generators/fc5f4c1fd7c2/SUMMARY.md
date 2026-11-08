# fc5f4c1fd7c2

0-bg grid (size varies). Several ISOLATED connected motifs (bbox >=2x2). 1..6 of them are color 4 (the TARGETS); 0..5 are DISTRACTORS in other colors from {2,3,5,6,7,8,9}. Motifs are separated by a 1-cell halo so each is its own 4-conn component. Rule: take every color-4 component and paint its FOUR bounding-box corners ((r1,c1),(r1,c2),(r2,c1),(r2,c2)) with color 1; leave the rest of each motif as-is. Objects of any other color are left COMPLETELY unchanged. Net: only color-4 motifs get their bbox corners flagged in blue. (Was a tiny 6-8x8-10 grid with 1-2 motifs, color 4 only, no distractors.)

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
