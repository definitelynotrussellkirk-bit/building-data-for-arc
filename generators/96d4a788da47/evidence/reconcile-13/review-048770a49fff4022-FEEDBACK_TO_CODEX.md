# General feedback

## F1: Canonical evidence paths should be enforced before expensive execution

**Symptom:** qualification and witness helpers accept arbitrary output directories, while the return contract later requires `checks/<task>/qualification/...` and `checks/<task>/causal/...`. Valid source-bound evidence can therefore be produced in a version-suffixed location that the final result schema cannot cite directly.

**Evidence:** this packet initially produced qualification and causal receipts under version-suffixed top-level directories and had to replay both targets into the canonical per-task layout before packaging.

**Suggested change:** have `review.py duties` emit the canonical final evidence paths as machine-readable data, and make qualification/witness commands warn or refuse noncanonical paths when an active packet contract is present.
