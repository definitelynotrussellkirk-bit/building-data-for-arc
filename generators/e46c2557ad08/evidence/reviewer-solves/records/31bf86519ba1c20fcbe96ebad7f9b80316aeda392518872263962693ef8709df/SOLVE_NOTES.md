# Visible-only blind solve

No generator, reference rule, canonical data, task notes or audit evidence was opened. Earlier rule exposure: no.

The three visible examples preserve background 0, vertical grey dominoes, and larger grey objects. Every isolated horizontal two-cell grey component changes to 8. The 2x2 square in example 1 stays 5, which rejects recoloring any horizontal adjacent pair inside larger components. The length-three and length-four horizontal objects also stay 5.

Hypothesis: flood-fill four-connected grey components; recolor exactly the two-cell horizontal components to 8. Implemented this directly as the first genuine solve attempt, with no invented failed revision. The queries were inspected only as unlabeled inputs; no query correctness has been measured.
