# fb7c915894d6

0-bg grid (size varies) with: (a) K (2-5) COPIES of a FREQUENT random polyomino SHAPE (4-7 cells); (b) 1-4 DISTRACTOR shapes, each a random polyomino with a DIFFERENT normalized shape (and distinct from each other), each appearing exactly ONCE. Every blob is painted a DISTINCT non-0 color drawn without replacement from {1..9} (the rule is COLOR-BLIND). Blobs are placed with 4-adjacent buffer separation. Rule (FIND THE MOST-FREQUENT NORMALIZED SHAPE, COUNT ITS FREQUENCY K, OUTPUT THAT SHAPE SCALED K× IN COLOR 8): GROUP all blobs by NORMALIZED SHAPE (color-blind, exact orientation). FIND the most-frequent class (tie-break top-most, left-most). Let K = its frequency. UPSCALE that shape by K (each cell -> K×K block) and PAINT every block color 8 on a bg-0 canvas of size (sh*K, sw*K). Input colors are DROPPED. Net: the dominant shape's mass × frequency yields a cyan-8 scaled output. (Was a fixed 9-shape bank; now shapes are generated randomly.)

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
