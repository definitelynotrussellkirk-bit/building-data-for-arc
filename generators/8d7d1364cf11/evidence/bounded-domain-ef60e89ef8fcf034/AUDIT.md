## 8d7d1364cf11

**Domain question / coverage restriction — duplicate-anchor tie breaking is not
taught.** The 61 portable task tests pass, and I found no failure on the
advertised unique-anchor grammar. However, the canonical Racket program flattens
all source cells and takes the first color match when multiple source cells share
a dot's color. Production explicitly rejects that case, so a solver trained only
on generated lessons need not learn the canonical first-match behavior.

`checks/audit/8d7d1364cf11/duplicate-anchor-witness.json` contains an exact
10×12 input with two 2×2 source templates that both use accent color 5, one
color-5 dot, and one absent-color decoy. The selected Racket authority matches a
row-major first-match mirror and differs from a last-match rival at three cells:
`(5,4)`, `(5,5)`, and `(6,4)` (authority color 2 versus rival color 3). The
current `self_check` rejects the input with the expected “multiple source-cell
anchors” diagnostic.

This is not a reproduced runtime defect; it is a deliberate subdomain boundary
already acknowledged in the task notes. A future maintainer should decide
whether canonical tie-break coverage matters enough to add a controlled
duplicate-anchor lesson branch. No audited source was edited.
