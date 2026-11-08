# 07ab476607b3

Normalize the red (`2`) shape A and yellow (`4`) shape B independently to their top-left origins, subtract normalized B from normalized A, and stamp the residue in magenta (`6`) at the maroon (`9`) anchor on a fresh black canvas. Out-of-bounds residue cells are clipped.

The default curriculum guarantees three rival-refuting lessons in every difficulty band: partial normalized overlap (`plain`), normalized disjointness (`disjoint_b`), and partial clipping (`clip`). `empty_diff` is an exact lawful boundary override where A equals B after normalization. `no_anchor` is retained only as a rejected negative fixture.

Kind: `per_puzzle`. Imported version: `4.0.0`. Rule hash: `11cea0a09738`.
Approval is derived by the catalog from current code and retained evidence.
