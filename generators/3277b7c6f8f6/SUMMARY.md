# 3277b7c6f8f6

Input = three N×N PANELS (N=3..5) separated by full color-8 divider columns. Panel A is a random N×N pattern in source colors c1,c2,c3; Panel B = transform(A) + recolor (one of rot-CW/180/CCW, flip-LR/UD, transpose, anti-transpose, then c1→t1,c2→t2,c3→t3); Panel C = a different random N×N pattern in the same source palette. Rule: infer the transform and color-map from A↔B and apply both to C. Output: the N×N recolor(transform(C)) prediction.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
