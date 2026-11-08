# Public family 71e489b6: implementation and verification plan

Intent: preserve the supplied binary-defect cleanup/outline task, author a general Racket reference and a source-bound native adapter. No lookup of supplied examples is permitted. Source lives only in this assigned home.

Design: identify monochrome 4-connected components with a solid 2x2 core; coreless blue components and one-neighbor blue tips are stray cells. Black coreless components and blue-surrounded black tips are defects. Detect on the original input; erase stray blue then draw an 8-neighbor orange rim, never painting defect cells. The alternative selects the largest 4-connected orange rim after construction, with row-major ties; merged small-defect rims can beat the largest individual defect. Preserve the default exact source in canonical.rkt. Bounded grammar and uncertainty are documented in notes.md.

Approaches: pixel-majority filtering incorrectly erases long black channels; closing also fills them. Component/core classification plus local tips matches all supplied labels without a numeric defect-size cutoff. Chosen by the implementer under the user's build-first request.

Tasks: (1) tests RED, reference/model and deterministic grammar, GREEN; (2) finite rival audit, strict API and one-query private/public projection, negative tests; (3) protected-Racket original labels, authoring preflight and causal counterfactual; (4) review, source patch and replay.

Review focus: black/blue detection order; diagonal versus cardinal connectivity; structural black channels; clipping and rim ties; private metadata and query-prefix independence. No acceptance or training admission is claimed.
