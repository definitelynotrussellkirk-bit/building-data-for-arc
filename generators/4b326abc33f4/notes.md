# Working notes: 4b326abc33f4

## Current decision

The repaired base remains the canonical puzzle: detect one or two hollow color-5
frames and fill each interior from its unique midpoint side seed. Version 2.0.0
removes unused/degenerate axes, rejects unknown or malformed overrides, supports
its declared 8–14 by 12–20 domain constructively, and mirrors the exact canonical
Racket program (`b18855f77d40`).

The native parameter is `assignment_mode = local | cyclic_next`. `local` is the
exact canonical program. `cyclic_next` orders frames by bbox, extracts the ordered
seed-color sequence, rotates it left, and fills each frame with its successor's
color. Inputs are matched across settings; the adapter supports 2–6 demos and
1–4 queries, with four qualification queries including a substantive 30x30 scene.

## Adversarial findings and repairs

- Seed 82 exposed a two-demo shortcut where numeric color sorting matched the
  intended rotation. Teaching colors are now constructed to reject that collapse;
  the retained counterexample is `workspace/parametric/evidence/teaching-regression-rank-sort.json`.
- Broader probes found center-row/area ordering, color-rank cycling, and
  side-conditional partial-cycle shortcuts. The minimum lesson now deliberately
  varies geometry, seed sides, and nonmonotone colors so all 13 named rivals are
  refuted in the bounded audit.
- Saved-export attacks with Boolean cells, duplicate inputs/payloads/JSON keys,
  leaked settings, and leaked query answers were rejected. Stale source hashes,
  forged program maps, tampered episode programs, and forged execution hashes
  were also rejected by the receipt reader.

## Final evidence and limits

- 15/15 staged focused tests passed.
- 256-seed audit: 512 minimum lessons, 6,656 rival checks, 512 crossed controls,
  3,904 labeled pairs, 400 ordinary base draws, zero findings.
- Protected authoring preflight: 4 episodes, 40 Racket evaluations, original-label
  and ordinary-generation checks passed.
- Protected causal replay proves `[3,2,6] -> [2,6,3]`; the unrotated local
  counterfactual changes the final output.
- Public projection: 16 one-query views; 24 private-field invariance checks passed.

Finite tests do not prove universal lesson uniqueness. Owner source review, fresh
native qualification/acceptance, and training admission remain pending. The next
useful action is owner replay on the integrated source patch.
