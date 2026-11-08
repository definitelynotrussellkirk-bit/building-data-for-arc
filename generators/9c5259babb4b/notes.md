# Working notes: 9c5259babb4b

## 2026-10-24 review-d6519a124d84a876

### Finding

The rule and validator use same-color 8-connectivity, but `_random_shape("a")` grew asymmetric objects only by orthogonal moves. Generalized lessons therefore never required diagonal connectivity; a 4-connected-object shortcut survived even though the canonical rule is broader.

### Repair

Version `3.1.0` adds a validated asymmetric six-cell bridge shape whose two lobes meet only diagonally. The first asymmetric object in `class_balanced`, `dense_mixed`, and `precedence_both` is sampled from its reflection variants. Each variant is asserted asymmetric, 8-connected, and not 4-connected before placement. Existing class counts, public-family generation, observer behavior, and canonical Racket source are unchanged.

The task tests were also made source-layout independent through `reviewer_support`. Base-solution Racket copies are compared after whitespace normalization because their 851-byte compact form is semantically identical to the 1,990-byte formatted canonical source.

### Verification

- Focused task suite: **66 passed**.
- Protected-Racket probe: **24/24** generated generalized scenes matched the Python mirror and contained an 8-connected/not-4-connected asymmetric witness.
- Canonical authority: **10/10** labeled pair appearances matched both the Python mirror and protected Racket.
- Evidence: `WORK/checks/peer-9c5259babb4b/probe.json` and `command.json`.
- Canonical normalized program SHA-256 remains `6a2cfe9a66b0e74c933fcf480718306c900866d6ac481f0c4c8d5d1818c4a866`.

### Remaining bounded gap

A short default lesson can still omit an object symmetric on both axes, so a left-right-first precedence rival may survive some three-example draws. That schedule-level teaching gap was not folded into this 15% connectivity repair.

## 2026-10-24 review-fab3aaae25f414f0

### Decision

Close the remaining precedence-identifiability gap with a task-local native parametric family rather than changing the already-correct canonical generator. The episode-fixed parameter is `precedence`: canonical `top_bottom_first` versus nearby `left_right_first`, with matched inputs and exact Racket programs differing only in the order of the two symmetry branches.

### Construction

The first two demonstrations are constructive teaching examples. Each contains two top-bottom-only objects, two left-right-only objects, one asymmetric 8-connected/not-4-connected object, one object symmetric on both axes, and singleton distractors. This makes the two-demo minimum identify the setting while retaining all source branches. Episodes support 2–6 demonstrations, always four distinct sequentially revealed queries, border contact, varied 18–30 dimensions, and a substantive exact 30×30 query.

### Evidence and limits

- Focused parametric suite: 42/42 passed; complete task suite: 108/108 passed.
- Finite teaching audit: 72 episodes across both settings, seeds 0–11, and 2/3/6 demonstrations; the declared alternate and seven additional shortcuts did not both fit the demonstrations and disagree on a query.
- Public projection audit: 16 one-query files, exact visible-byte IDs, no private setting/program/answer or future-query leakage.
- Protected-Racket native qualification passed at 2, 3, and 6 demonstrations (32, 40, and 64 evaluations respectively), including exact 30×30 labels.
- The protected-Racket wrong-order witness changes 13 final cells on a both-axis object (left-right-first color 3 versus top-bottom-first color 1).

This is reviewer-ready only. The next action is owner integration followed by fresh native qualification and acceptance on the exact live bytes. No training admission is claimed. Optional peers `9b5d72b45563` and `8e9c04b8fdfb` were not reviewed in this return.
