# Working notes: c181f41a09f0

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-0774c3878e6860bf — parametric travel extent

### D1 — Preserve the production authority exactly

The production generator (`fdaef0b9eb49b55dd60c29589e8f5fca51519fe52b3357ab2f146234fdd7eba0`) and canonical rule hash (`bd986c826aae`) were not changed. The default `travel_extent=opposite_end` materializes the canonical Racket program byte-for-byte (`bb50b7fdceb2f705a80eddc57c020feb2f4bbfcd6d398fc5cd891ae7364d6f69`).

### D2 — Parameterize only travel distance

The prototype adds `travel_extent ∈ {opposite_end, one_block}`. Both settings infer the same marked source strip, source-side direction, unmarked-strip fallback, and stationary marker decoys. `one_block` changes only the destination from the far end to one recovered block inward; its program hash is `92288a6482e44438052f59c433b2e5a5373b9fddf47d446326a84d1b0b2ed7cb`.

### D3 — Keep sampling setting-neutral and stress the lawful grammar

The adapter supports 2–6 demonstrations and 1–8 queries independently. The reviewed four-query schedule is 8×12, 14×14, 24×28, and 30×30; it covers horizontal/vertical strips, both source sides, marked and unmarked strips, and stationary decoys. The 30×30 query has four strips, three marked strips, and six marker decoys.

### D4 — Separate public and private evidence exactly

Public files contain demonstration input/output pairs and query inputs only. Private records retain settings, programs, query labels, and protected-Racket provenance. A bounded adversarial check found that pretty-printed JSON broke the full-SHA filename contract; `_write_public` now writes exact `public_challenge_bytes`, and a regression pins that serialization boundary. Mutated labels, leaked query outputs, and unsupported counts fail closed.

### D5 — Retain as a proposal, not an approval

Focused Racket-backed tests passed 16/16 and the staged task suite passed 21/21. The current source/evidence inventory is `workspace/parametric/evidence/source-inventory.json` (SHA-256 `5d310ebd1e3a628da6ef4b09bb54491bec466d1be31fa6c3286a73a7b5870bc6`). Finite evidence distinguishes the two declared extents only. The next useful action is owner qualification with at least two fresh seeds per setting; no production integration or training admission is implied.

## Review review-f7fbe6446c0ee181 — marker-count sequential travel

### D6 — Replace the scalar alternate with a causal two-stage rule

The prior `one_block` alternate changed only a constant destination. It was replaced by `marker_count_steps`: Step A recovers each source-end 3×3 block and counts its marker-colored cells; the intermediate is that per-strip count; Step B moves the recovered block by that many 3-cell steps, clipped by strip capacity. The exact canonical `opposite_end` program remains byte-for-byte unchanged. A protected-Racket constant-one counterfactual changes the final output, so Step B cannot be computed correctly after skipping or corrupting Step A.

### D7 — Repair the smallest lesson instead of raising its cost

The first two-demo design admitted constant-step and strip-rank shortcuts on 118 of 256 sampled lessons. A second attack found a marker-span shortcut on 26 of 64 seeds and side/rank lookup rivals on all 64. The repaired two-demo lesson holds dimensions, orientation, source side, and marked strip ranks fixed while permuting marker counts `(1,2,3)` and `(3,1,2)`; a noncontiguous two-cell cap breaks span and position proxies. The minimum remains two demonstrations. The retained 64-seed audit now reports zero failures across 1,152 shortcut fits, 48 boundary cases, crossed controls, and eight protected-Racket parity cases. This is bounded evidence, not universal rule uniqueness.

### D8 — Keep the episode and export contracts strict

The adapter supports independent 2–6 demonstration and 1–4 query counts. Four query inputs are distinct, privately shuffled, prefix-stable, and projected one at a time without future-query or total-count hints. The verifier rejects duplicate inputs, boolean/non-integer cells, mutated labels, stale program hashes, forged survivor certificates, and private-field leakage. Minimum, axis-swapped, boundary-source, and substantive 30×30 scenes are exercised.

### D9 — Preserve the owner gate

This review prepares source-bound manifest, authoring preflight, protected-Racket causal witness, and public/first-turn export receipts. It does not edit approval state, grant native acceptance, or admit training data. The next useful action is owner review of the exact source followed by fresh native qualification and acceptance.
