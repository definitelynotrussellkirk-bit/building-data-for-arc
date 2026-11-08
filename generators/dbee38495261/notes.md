# Working notes: dbee38495261

## Current rule and authority

Final generator version: 3.0.0. Generator SHA-256: `b7a091c114eece1357ceac46e64a6d915564d3f618699aaae7be999862c8907d`. Canonical `RULE_HASH`: `f1fa88aeec11`; no Racket authority changed.

Input is a color-1 wall maze with traversable color-0 cells, one start 2, one end 3, and one to four distinct mids from 4..7. Visit present mids in ascending numeric order. For each consecutive leg, use deterministic four-neighbor BFS (up, down, left, right), block color 1, paint only interior color-0 path cells 8, and preserve walls/markers.

## Reversed decision

Prior v2.2.0 used open all-zero boards and several pseudo-axes. That choice made wall avoidance unobservable and rejected all four canonical inputs. It was replaced with constructive wall mazes after the before self-check and red focused tests reproduced the mismatch. Palette/texture/density aliases were removed rather than claimed as controls.

## Distribution decisions

- Exact axes: `grid_h` 7..14, `grid_w` 9..16, `n_mids` 1..4; invalid/unknown controls fail.
- Four-scene schedule: midpoint counts 1,2,3,4; one canonical-size profile per lesson.
- Random DFS maze plus bounded connector/placement search.
- Every scene defeats wall-ignoring and direct-2→3 rivals; scenes with ≥2 mids also defeat reverse-numeric and row-major order.
- Four deterministic 7×9 semantic fallbacks guarantee completion and embed into larger exact canvases.
- `rule_mirror`, validators, witnesses, rivals, and query-aware lesson hook are executable.

## Evidence

- Before aggregate was interrupted after retained lint/self-check failures and a green rule smoke: `checks/before/`.
- TDD red: 21 failed / 8 passed; final focused suite: 30 passed.
- Final battery: 12/12 green with required rotations.
- Override gate: 13,590/13,590 accepted, zero findings.
- Census: 300 lessons, four demos + one query, 1,500 unique inputs, 0 production ambiguity and 0/1,500 rotated-query ambiguity against four unique named competitors (eight registry-qualified entries).
- Source-bound counterexample: `counterexamples/review-a21b77ad9dc3e664-v0001/`.

## Known limits / open findings

Maze topology has border walls and an odd-cell DFS lattice; undeclared parity or morphology shortcuts remain possible. Finite rival checks do not prove universal identifiability. Rare bounded-search fallback use can reduce structural variety while preserving the tested semantics. Catalog approval is still a maintainer decision.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b7a091c114eece1357ceac46e64a6d915564d3f618699aaae7be999862c8907d`.

# Decisions for `dbee38495261`

## D1 — Replace the open-grid domain with the canonical wall-maze domain

**Prior choice:** v2.2.0 sampled only color-0 backgrounds with isolated markers. The original rationale is not retained; its summary described shortest paths “through background cells” and apparently treated obstacles as unnecessary.

**New choice:** every lawful generated input contains color-1 walls and traversable color-0 corridors, with the same start/end/waypoint palette as canonical inputs.

**Reason and evidence:** the selected Racket authority blocks color 1, all four canonical inputs contain walls, and the prior `self_check` rejected all four. Open grids make the wall-aware law observationally identical to a wall-ignoring shortcut. The retained red tests and before self-check reproduce this mismatch.

**Rejected alternatives:**
- Merely loosen the old validator: labels would run but wall behavior would still be unteachable.
- Sprinkle independent random walls: this frequently disconnects legs or creates scenes where the shortcut still agrees.
- Change the Racket rule to match open grids: the canonical labels and authority were already coherent; the generator was wrong.

## D2 — Construct mazes, then search placements against executable competitors

A randomized DFS maze with a few connectors guarantees connectivity structure. Marker placement is accepted only when each intended leg exists, avoids unrelated markers, paints at least one zero, leaves at least one zero, and defeats the wall-ignoring and direct-2→3 rivals. With two or more mids it must also defeat reverse-numeric and row-major ordering.

Bounded search is followed by four verified 7×9 fallback scenes, one for each midpoint count. Larger exact dimensions embed the fallback in wall padding. This is preferable to unbounded resampling and gives deterministic completion, but it can narrow morphology on rare fallback use.

## D3 — Keep only observable exact controls

The old palette, texture, `position_bias`, `density`, `n_distinct_colors`, and `palette_size` declarations were aliases, degenerates, or unrelated to the actual canonical law. They were removed rather than reported as axes.

The retained controls are:
- `grid_h`: exact integer 7..14;
- `grid_w`: exact integer 9..16;
- `n_mids`: exact integer 1..4.

Overrides are honored over all difficulty bands; unknown keys and invalid types/ranges fail. The final gate exercised 151 cases × 3 bands × 30 seeds = 13,590 draws with no findings.

## D4 — Use a four-scene curriculum tied to semantic coverage

A lesson has four ordered demonstrations and one query. `sample_index % 4` supplies 1,2,3,4 mids, while profile zero supplies a canonical-size anchor. The ordering is intentional but the lesson contract is also query-aware and supports every hold-one-out rotation.

Measured policy and verdict:
- demonstrations: 4; query: 1;
- production assembly: consecutive sampler indices;
- production verdict: 0 ambiguous among 300 materialized lessons against four unique named competitors (eight registry-qualified entries);
- rotation policy: required; every one of 1,500 labeled pairs held out once;
- rotation verdict: 0/1,500 ambiguous; 0 hook warnings or scoring errors;
- unique inputs: 1,500.

This finite rival census does not prove universal identifiability or enumerate all schedule starts.

## D5 — Make the rule contract independently executable

The Python `rule_mirror` duplicates the selected Racket behavior only for audit/testing: four-neighbor BFS, neighbor order up/down/left/right, color 1 blocked, and only interior color-0 path cells recolored 8. Racket remains authority.

Named competitors are wall-ignoring, direct start-to-end, reverse numeric waypoint order, and row-major waypoint order. Witness functions and `lesson_identifiable` use actual outputs rather than metadata names. The hook rejects only a competitor that fits every demo **and changes the labeled query**, avoiding the false-positive pattern found in audit target `40dea3d45f2a`.

## D6 — Pin, do not modify, the canonical authority

`RULE_HASH` is pinned to `f1fa88aeec11`. Rule smoke, Racket lint, and authority synchronization/execution parity passed. No canonical or archival Racket row changed.

## D7 — Retain exact counterexamples and test them

The task-local fixture `counterexamples/review-a21b77ad9dc3e664-v0001/` records a final-source generated input, call parameters, Python mirror output, selected Racket receipt, and all rival outputs. The focused suite reloads it and verifies the source hash and all mismatches. This is more useful to future reviewers than a prose-only warning.

## Known limits

Generated mazes intentionally use border walls and a room/corridor lattice. The current declared rivals do not test every potential shortcut based on parity, border structure, path-tie statistics, or fallback morphology. Search and census results are empirical and source-bound. Catalog approval remains a maintainer action.
