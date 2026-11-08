# Working notes: 7f666a786bf3

## Current rule and authority

For each nonzero color independently, fill its tight axis-aligned bounding rectangle with that color on a 0 background. The canonical Racket authority was not changed. `RULE_HASH` remains `28a554829349`; final generator version is `4.0.0`.

## Reversed distribution decision

Version 3.0.0 required every color in a scene to have the same marker count. That choice was not part of the rule and created a teaching shortcut: a solver could fill only colors tied at the shared/minimum marker count. The shortcut matched all 4 canonical pairs and all 900 sampled ordinary baseline draws. The minimal mixed-count witness is retained in `counterexamples/mixed_marker_counts.json` and Racket evidence in `checks/repair/7f666a786bf3/mixed_marker_counts_racket.json`.

Version 4.0.0 allows each color to have 2–4 markers and adds exact `mixed_marker_counts`. `markers_per_color` is the observable minimum/floor; explicit legacy-style calls remain uniform unless they opt into mixing. `mixed_marker_counts=True` with floor 4 is declared incompatible because no larger legal count exists.

## Curriculum and semantic contract

Default samples alternate a two-slot schedule: even indices use mixed marker counts and odd indices use uniform counts. With `EXAMPLES_NEEDED=3`, every consecutive training window and every query rotation contains a mixed-count witness. Canonical linked profiles are confined to the uniform slot; their conditional prior is 0.80, preserving roughly the former 0.40 overall profile rate.

Executable rivals cover identity, first-color-only filling, and the canonical-fitting `uniform_marker_count` shortcut. `lesson_identifiable` requires all declared rivals to be contradicted by the demonstrations. The final semantic gate observed 301/600 mixed-count witnesses, verified 60/60 claimed rival disagreements, and found 0/48 ambiguous smoke-test rotations.

## Verification and limits

Final source SHA-256: `06cab5dcf73c126536c14ff1d6f6f37226861ced9c75a6b62be91cc5f925bb45`.

- Battery: 12/12 green with required rotations.
- Focused tests: 13 tests and 18 subtests passed.
- Production census: 300 lessons, 1,200 pairs, 1,200 rotations, 0 ambiguities or scoring errors.
- Exhaustive declared schedule at seed 0: 6 starts across three bands, 24 rotations, 0 ambiguities.

These checks distinguish only the declared finite rival set; they do not prove universal rule identifiability. Overlapping colored bounding rectangles remain deliberately outside the teaching domain because overwrite order would be ambiguous.
## Current reviewer considerations

Source SHA-256: `06cab5dcf73c126536c14ff1d6f6f37226861ced9c75a6b62be91cc5f925bb45`.

# Decisions

## D1 — Replace the equal-count invariant

**Prior choice:** version 3.0.0 gave every color one shared marker count and rejected unequal counts.

**Evidence against it:** `checks/baseline_equal_count_probe.json` shows 0/900 mixed ordinary inputs. A shared/minimum-count rival matched all 900 generated examples and all 4 canonical examples. The mixed-count Racket witness in `counterexamples/mixed_marker_counts.json` demonstrates that the restriction is unrelated to the authority.

**Decision:** allow each color independently to use 2–4 markers.

**Rejected alternatives:**

- Keep the validator restriction and merely document it: leaves the shortcut intact.
- Make every draw mixed: removes useful uniform/canonical-profile support and changes existing exact calls.
- Mix with an independent random coin: witness frequency would not guarantee that each complete lesson teaches the distinction.

## D2 — Add an exact relational axis

**Decision:** add `mixed_marker_counts: bool`. When false, every color has exactly `markers_per_color` markers. When true, `markers_per_color` is the minimum/floor and at least one color has a larger count. The combination `mixed_marker_counts=True, markers_per_color=4` is explicitly incompatible.

**Compatibility choice:** any explicit override call that omits the new axis remains uniform. This preserves the meaning of existing calls such as `markers_per_color=4`; callers opt into the new relational mode deliberately.

**Failure modes checked:** wrong types, unknown keys, floor boundaries, all bands, edge touching, and exact observed provenance. These are covered by focused tests and the override stage.

## D3 — Use a deterministic two-slot curriculum

**Decision:** even sample indices are mixed and odd indices are uniform; `LESSON_SCHEDULE_PERIOD=2`, `EXAMPLES_NEEDED=3`.

**Rationale:** every three-consecutive-example training set necessarily contains a mixed witness, including after any one of four materialized pairs becomes the query. This is stronger and cheaper to verify than a probabilistic mix.

**Canonical profile adjustment:** canonical linked-profile draws occur only in the uniform slot. Their conditional prior is 0.80, maintaining an approximately 0.40 overall rate rather than halving the old support.

**Limit:** the period is a deliberate curriculum correlation. It guarantees the declared distinction but is not evidence against undeclared rivals.

## D4 — Make the teaching claim executable

**Decision:** declare `identity`, `first_color_only`, and `uniform_marker_count` rivals; declare the mixed-count witness and the exact rival it refutes; require all lesson competitors to fail on demonstrations.

**Rationale:** the baseline battery's semantic stage was advisory because there was no contract. Executable rivals turn “this should teach the rule” into a source-bound check and make the larger census interpretable.

**Alternative rejected:** prose-only shortcut notes. They cannot be scored on every generated lesson or query rotation.

## D5 — Preserve the authority

The canonical Racket program already handled the mixed-count witness correctly. No rule edit was justified. `RULE_HASH` remains `28a554829349`; authority sync and rule smoke stayed green.

## D6 — Repair test portability

The selected focused test used a fixed `Path.parents[...]` depth, which failed in the portable staged runtime before behavioral assertions ran. It now uses `reviewer_support.find_root` and `canonical_pairs` and searches both supported generator layouts. This was a test-harness repair, not a relaxation of expectations.

## D7 — Build a reusable support probe

`workspace/probe_rival_support.py` loads rivals from the live `CANONICAL_SHORTCUTS` declaration, verifies canonical fit, measures generated refutation by band, and scans consecutive training windows. It can use a repaired contract against an immutable baseline sampler, making before/after comparisons possible without editing the baseline.

The probe is intentionally cheap and Python-mirror based. A pass is not a substitute for Racket-backed battery and census results; it is an authoring and regression tool.

## D8 — Known limits

- The generator intentionally rejects overlapping per-color bounding rectangles; the authority's overwrite order would otherwise introduce a separate ambiguity.
- The declared rival set is finite. Zero measured ambiguity does not prove universal induction or hidden-query correctness.
- Schedule enumeration covered all residues and query positions at one fixed seed; wider seed coverage came from the 300-lesson production census rather than exhaustive enumeration.

## Native parametric build — review-36b6144606a947ef

Built `workspace/parametric/` with episode-fixed `finish` values
`fill_only` and `highlight_largest_filled`.  The default program is the exact
selected canonical source.  The alternative fills all per-color rectangles,
measures the resulting solid components, and recolors the unique largest filled
component to 9.  Inputs are matched across settings; 2–6 demonstrations and four
privately shuffled queries are supported, including one substantive 30x30 case.

The finite authoring audit covered 18 jobs (seeds 0, 17, 97; demos 2, 3, 6;
both settings), 138 pairs, and 14 declared rivals with no wrong-rule survivor.
Native qualification passed four jobs and 40 protected-Racket evaluations.
The protected causal witness uses a wrong-intermediate perimeter selector: area
selects color 5, perimeter selects color 7, and the final grids differ on 42
cells.  Public preview verification passed 16 independent one-query views.
These are bounded reviewer results; exact-source owner acceptance and training
admission remain pending/false.
