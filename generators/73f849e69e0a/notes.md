# Working notes: 73f849e69e0a

Review `review-b79217513dc660a0` kept the existing base generator unchanged and added a native two-setting parametric family.

- Base review: original protected labels and ordinary `None`/`medium` draws pass; no base-source repair was needed.
- Parametric family: `orientation = identity | rotate_cw`; sampling is setting-independent. A locates the first full color-5 separator and extracts the logical stride-2 3×3 icon; B stamps the identity or clockwise-rotated icon at every red marker below the discovered separator.
- Teaching construction uses separator rows 6, 7, and 8, asymmetric multicolor icons, red as payload, distributed/corner markers, distinct inputs, and a corner-spanning 30×30 output query.
- The canonical identity rule is byte-identical to ledger SHA-256 `07d5df073b976e08aaca5c377718a2554bbddca567207d05496b491986a33e2d`; the rotate rule is `cc218abe4419de33bb70f78dba69241c28f1fcc997d56bee8a95520d1c901a22`.
- Retained evidence: 17 final tests; four protected-worker jobs / 40 Racket labels; sole declared-setting survivor at seeds 0 and 17; protected fixed-wrong-separator causal replay; bounded rotation/fixed-separator shortcut audit; verified 16-view sequential public projection and first-turn privacy checks.
- Current status: reviewer-ready only. Owner source review, native qualification, and fresh acceptance remain mandatory; no training admission is claimed. The unchanged legacy base test emits one non-failing staged-namespace warning.
