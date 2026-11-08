# Working notes: a0076c1c960c

## Current rule and domain

For each row, find its nonzero marker cells. The reviewed generated domain has exactly two markers on each of 2–4 active rows. The authority closes the horizontal span, removes all original marker positions, and paints only previously zero interior cells with fixed output color 8. Output shape equals input shape.

The generator is pinned to canonical rule hash `2205cb4e988b` and uses only the three canonical input profiles: `8x10`, `8x11`, and `9x9`. Every generated grid has at most one adjacent marker pair and at least one nonempty bridge. Non-adjacent pairs have one exact endpoint distance, controlled by `span=2..6`.

## Decision reversals in review-003bdcc2dc991b98

The imported v2 generator treated same-color endpoints as semantic and painted bridge cells with each endpoint color. That was reversed because all canonical outputs use fixed color 8, while the selected authority treats every nonzero marker as a marker regardless of its color. The exact mixed-color witness is retained at `counterexamples/same_color_pairs_only.json`; supported Racket evidence is `checks/counterexample-racket.json` in the review return.

The imported sampler used noncanonical dimensions, distinct row colors, and a minimum endpoint distance of 3. It therefore omitted canonical adjacent and one-cell-gap boundary cases. The reviewed sampler instead uses canonical shapes, explicit adjacent presence/absence, and spans 2–6.

The imported eight-axis surface included dead or unobservable controls. It was replaced with five pixel-observable controls: `shape`, `active_rows`, `span`, `adjacent_mode`, and `palette_mode`. Unknown, mistyped, and out-of-range overrides reject loudly.

## Teaching schedule

A lesson uses four demonstrations plus one query. The six-step default palette schedule is `mixed, canonical, mixed, same, mixed, canonical`; every four consecutive inputs contain at least two mixed-color witnesses, so any one held-out pair leaves a witness in the demonstrations. The declared rival `same_color_pairs_only` fits all three canonical pairs but is falsified by mixed-color endpoints.

Final source SHA-256: `1efc88aae34a48ddfcf0786db335f69cf652f1d103c249e8dc77e14f9c2e586e`. The final 300-lesson census materialized 1,500 pairs and all 1,500 query rotations with zero declared-rival ambiguities or scoring errors; this is finite evidence, not a proof against undeclared rules.

## Known limits

The generator intentionally stays within the canonical two-markers-per-row grammar; it does not teach rows with three or more markers. Marker color 8 is reserved for output and never generated as input. Palettes cover canonical, same-color, and two-color mixed endpoints, but not every possible multi-color arrangement. The semantic checks cover the strongest identified canonical shortcut, not all conceivable hypotheses.
## Current reviewer considerations

Source SHA-256: `1efc88aae34a48ddfcf0786db335f69cf652f1d103c249e8dc77e14f9c2e586e`.

# Decisions for a0076c1c960c

## D1 — Bind behavior to the selected authority

**Prior choice:** The imported generator described same-color endpoint pairs and painted the interior with the endpoint color. Its original rationale is unknown.

**New choice:** Treat every nonzero cell as a marker, remove original marker positions, and paint bridge-only cells with fixed color 8. Pin `RULE_HASH = "2205cb4e988b"`.

**Why:** Every canonical output uses only 0 and 8, and the selected Racket program closes each row's nonzero span before subtracting original cells. Independent Python oracle tests agree on every canonical pair; rule-smoke and authority-sync pass.

**Rejected alternative:** Keep the old per-row color output and change the Racket rule. That would contradict the canonical outputs and had no evidence.

## D2 — Use canonical shape support, not a broad guessed envelope

**Prior choice:** Heights 6–8 and widths 7–10, which omitted canonical `8x11` and `9x9` inputs.

**New choice:** Exact `shape` values `8x10`, `8x11`, and `9x9`.

**Why:** All three are source-supported and directly observable. The strict profile and profile-floor gates pass in every difficulty band.

**Limitation:** No extrapolation to larger shapes is claimed.

## D3 — Separate adjacent rows from nonempty bridge span

**Prior choice:** Endpoint distance at least 3, excluding adjacent pairs and one-cell interiors.

**New choice:** `span=2..6` for non-adjacent rows plus `adjacent_mode=absent|present`, with at most one adjacent row and at least one nonempty bridge per grid.

**Why:** Canonical examples include adjacent pairs (empty output contribution) and distance-2 pairs. A separate adjacent control makes the empty-bridge boundary exact and observable without allowing all-empty impostors.

**Rejected alternative:** Fold distance 1 into the `span` axis. That would make a single grid unable to expose one exact non-adjacent span when adjacent and non-adjacent rows coexist.

## D4 — Two to four active rows, exactly two markers per row

**Choice:** Generate 2–4 active rows, each with exactly two nonzero markers.

**Why:** This covers canonical structure while avoiding trivial one-row lessons and generic solid-block impostors. The validator accepts every canonical input and rejects blank, third-marker, vertical-pair, reserved-color, too-many-row, and solid-2x2 near misses.

**Limitation:** The authority can be read more broadly as closing any row with nonzero cells; rows with three or more markers are intentionally outside this reviewed generator grammar.

## D5 — Palette modes encode semantic counterfactuals

**Choice:** `canonical` uses color 2; `same_color` uses one noncanonical marker color; `mixed_color` uses two distinct colors with reversed order on alternating rows. Input color 8 is reserved.

**Why:** Canonical demonstrations alone support the strong shortcut “only bridge equal-color endpoints.” Mixed endpoints are legal under the authority and directly refute it. Same-color non-2 cases also show that color 2 is not the trigger.

**Probe:** `counterexamples/same_color_pairs_only.json` is generated by the public API, passes `self_check`, and has a supported Racket output differing from the rival.

**Rejected alternative:** Random unrestricted colors. A deliberate three-mode curriculum gives stronger lesson-level guarantees and remains easy to audit.

## D6 — Keep only exact, pixel-observable controls

**Choice:** Public axes are exactly `shape`, `active_rows`, `span`, `adjacent_mode`, and `palette_mode`.

**Why:** The imported texture/palette-size/distinct-color/position controls were dead, singleton, or not recoverable from output pixels. Every retained override is checked by `observe_overrides`; invalid types, ranges, enums, and unknown names reject loudly.

**Failure mode considered:** `bool` is an `int` subclass in Python. Validation uses exact types so `True` cannot silently stand for an integer axis.

## D7 — Four demonstrations, one query, deliberate six-step schedule

**Choice:** `EXAMPLES_NEEDED=4`; palette schedule `mixed, canonical, mixed, same, mixed, canonical` and a parallel adjacent schedule.

**Why:** Any four consecutive pairs contain at least two mixed-color witnesses. Holding out any one pair from a five-pair lesson therefore leaves at least one mixed witness among the four demonstrations. Focused tests enumerate 18 consecutive starts, and the 300-lesson production/rotation census reports zero declared-rival ambiguities.

**Ordering/query policy:** Production order is deterministic by sample index, but arbitrary single-pair query rotations are supported and required; the census held out every materialized pair once.

**Limitation:** The finite census and one declared rival do not prove universal identifiability.

## D8 — Retain failures and distinguish infrastructure from semantics

The baseline battery, TDD-red test, first census handshake error, and successful retries are retained. The failed census requested zero lessons and is not interpreted as a semantic result. Its isolated retry used identical source hash and completed 300/300 lessons.
