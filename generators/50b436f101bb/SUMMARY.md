# 50b436f101bb

0-bg grid (size varies). The LARGEST object is a 2-wide RING of one color forming a size×size bounding box (size 7-11) with a RANDOM pattern of that color filling its (size-4)×(size-4) INTERIOR. A couple of small distractor clusters in other colors sit elsewhere. Rule: background = most frequent color; cluster non-bg cells; take the largest one-color cluster; shrink its bbox by 2; output the inner region (the color's cells stay, else bg). Output = the ring's interior pattern, dims (size-4)×(size-4).

Kind: `per_puzzle`. Imported version: `3.2.1`.
Approval is derived by the catalog from current code and retained evidence.
