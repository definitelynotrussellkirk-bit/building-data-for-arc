# Working notes: d6607fc42bcc

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review 2026-10-24 — review-6449ae9dfaea35be

Production generator version 3.0.0, SHA-256 `01bd9fe9646fea8b34ef2604e9bf8b162051b6c8ffd3ac89577fa96d55013402`, and canonical rule hash `30de93f65182` remain unchanged. This review adds a separate native parametric candidate under `workspace/parametric/` plus focused tests; it does not alter the accepted generator or canonical authority.

The family exposes one episode-level parameter, `projection_depth`: canonical/default `one` and alternate `dot_offset`. Both settings receive identical inputs for a fixed seed and count request. Step A detects each color-1 notched rectangular frame, locates its single interior non-frame dot, and records the vertical dot-to-notch distance. Step B fills the interior/notch with the dot color and projects a full frame-width bar outward by either one row or the recorded distance. The alternate therefore uses an input-derived intermediate rather than a cosmetic branch.

The adapter supports 2–6 demonstrations and 1–4 queries. Constructive demonstrations make every prefix of length 2–6 distinguish the two settings and reject six explicit finite shortcuts: fixed depth two, no exterior bar, bar only, opposite-edge distance, interior height, and nearest-edge distance. The fourth query is a distinct 30×30 two-frame case. Public one-query turns retain only demonstrations and the current query input.

Native qualification passed for both settings at seeds 0 and 17 with three demonstrations and four queries. The protected-Racket causal witness selects a `dot_offset` query whose Step-A distance is 3; replacing that intermediate with the canonical constant 1 changes the final grid on the same input. Evidence is in `checks/d6607fc42bcc/qualification/` and `checks/d6607fc42bcc/causal/built/`.

The focused suite passed 23 tests. The isolated task suite passed 31 tests and 11 subtests after replacing an inherited fixed-parent canonical-data path in the test with `reviewer_support.find_root`/`canonical_pairs`; the production generator was not changed. The bounded audit executed 32 sampler requests, 102 protected-Racket evaluations, all six executable shortcuts, and four actual 30×30 labels.

Limits: shortcut coverage is finite, the causal interpretation is reviewer-authored metadata backed by one protected-Racket counterfactual, and `ready` is not owner acceptance. The next owner action is to integrate the exact source bytes, rerun native qualification and witness replay on the live tree, then perform fresh native acceptance. No training data is admitted by this review.

