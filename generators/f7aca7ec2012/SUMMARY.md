# f7aca7ec2012

0-bg grid (size varies). (a) LEGEND color at (0,0) from {1..9}. (b) ONE big BODY BLOB in the legend color (5-25 cells, LR-asymmetric so the flip is visible), away from the corner. (c) Optional smaller SAME-COLOR decoy blobs (strictly smaller, so the rule's 'largest' pick is unambiguous). (d) Several DISTRACTOR blobs in other colors. Rule: read legend L=g[0][0], clear (0,0), take the largest color-L object, crop to bbox, flip left-right; emit the flipped crop. Net: the legend color's body blob is extracted and horizontally mirrored. (Was: 3-4 cell body blob -> tiny fixed output.)

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
