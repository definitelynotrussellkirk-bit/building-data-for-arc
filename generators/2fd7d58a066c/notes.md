# Working notes: 2fd7d58a066c

## 2026-10-02 review `review-9d83cd0729c9e31b`

### Baseline observations

- The file defined `self_check` twice; the first definition was dead.
- The surviving checker rejected adjacent occupied columns, including canonical train example 2.
- Ordinary generation required monochrome columns, distinct colors by column, at least two markers per occupied column, and normally non-adjacent columns. None of those restrictions belongs to the canonical rule.
- The public override surface declared nine axes, but most were ignored, aliases, singleton constants, or incompatible with difficulty-specific draw bounds. The before override gate reported 14,915 findings over 99,540 draws.
- None of 60 before draws matched a canonical dimension/palette profile.
- The strongest canonical-fitting shortcut found was `canonical_surface_only`: fill only columns containing exactly two color-2 markers. It reproduces every canonical pair but fails on lawful mixed-color, non-2-color, singleton, and extra-marker cases.

### Selected repair

- Kept the Racket authority unchanged and pinned `RULE_HASH = 5fe179015bd4`.
- Replaced the narrow surface grammar with four semantic profiles on a five-example schedule. `canonical_pairs` appears twice to keep canonical-scale support above the repository floor; the other profiles are explicit shortcut counterexamples.
- Reduced the exact override contract to one observable `scene_profile` axis. Unknown keys and invalid profile names now fail loudly.
- Added an audit-only Python mirror, strict-canonical predicate, semantic witnesses, named rivals, schedule hook, lesson-identifiability hook, mutation fixtures, and observable profile facts.
- Added task-local regression tests and `workspace/profile_probe.py` for repeatable profile/rival coverage measurement.

### Measured local probe

`workspace/profile_probe_after.json` records 60 draws: 24 canonical, 12 adjacent/shared, 12 mixed-extreme, and 12 singleton/extra. All five canonical-fitting shortcuts are reproduced on all three canonical pairs and refuted by generated cases. The Python mirror matches all canonical outputs. This probe is not an authority check; the battery's Racket stages provide that verification.

### Limitations

- The generator intentionally uses a structured teaching grammar rather than sampling every possible nonzero-column arrangement.
- Five demonstrations are requested so every consecutive lesson window contains all four semantic profiles; this is more examples than the two canonical training demonstrations.
- `self_check` rejects identity-like already-filled inputs and lessons with fewer than two informative spanning columns even though the mathematical rule is defined on them. These exclusions are pedagogical, not claims that the Racket rule is undefined.
## Current reviewer considerations

Source SHA-256: `f5fa43530f3debc1763d2acc2c81208ad815c8333624303aa7cdaa38c34e6ed3`.

# Decisions for 2fd7d58a066c

## D1 — Keep the Racket authority unchanged

**Original state/rationale:** The existing generator description and canonical program agreed on column-wise min/max span filling. No rule-output mismatch appeared in rule smoke or authority sync. The original source did not carry a `RULE_HASH` pin.

**Decision:** Keep the canonical/base Racket program unchanged and pin its current hash, `5fe179015bd4`, in the generator.

**Alternatives considered:** Rewrite the rule to require two endpoints, same colors, or non-adjacent columns. Rejected because those are generator artifacts, not canonical semantics; the canonical program explicitly uses every nonzero cell and accepts adjacent columns.

**Probe/evidence:** Before and after rule-smoke and authority-sync logs; canonical mirror tests; `checks/after/checks/2fd7d58a066c_after_semantic_gate.json` once materialized by the full battery.

**Failure mode/limitation:** The Python mirror is audit-only and could drift in the future. `RULE_HASH`, canonical-pair tests, and Racket-backed gates are the drift defenses.

## D2 — Remove the non-adjacent-column restriction

**Original state/rationale:** A comment said separation kept fills “visually distinct.” The surviving `self_check` enforced it. That visual preference rejected canonical train example 2, whose occupied columns 6 and 7 are adjacent.

**Decision:** Adjacent columns are ordinary lawful inputs. The `adjacent_shared` profile guarantees at least one adjacent pair.

**Alternatives considered:** Keep non-adjacency for generation but relax only `self_check`; add a rare adjacent texture. Rejected because a checker-only repair would still teach the shortcut, and a rare texture would not guarantee lesson-level coverage.

**Probe/evidence:** Canonical acceptance test, `adjacent_active_columns` witness, named `nonadjacent_columns_only` rival, semantic gate.

**Failure mode/limitation:** Adjacent markers can form horizontal visual components. The intended rule remains column-local, and the profile deliberately teaches that component appearance is irrelevant.

## D3 — Make marker color semantically irrelevant in the distribution

**Original state/rationale:** The old generator chose one distinct color per active column and required each column to be monochrome. The stated rationale was not recorded; it appears to have been a visual-separation heuristic.

**Decision:** Generate repeated colors across columns, arbitrary nonzero colors including `1` and `8`, and mixed colors within a column. The `mixed_extremes` profile guarantees top and bottom colors differ in at least one column.

**Alternatives considered:** Continue monochrome columns while merely expanding the palette; recolor only interior markers. Rejected because same-colored extremes and color-2-only remain canonical-fitting shortcuts unless extremes themselves vary.

**Probe/evidence:** `mixed_extreme_colors`, `noncanonical_marker_colors`, and `repeated_column_colors` witnesses; `same_color_extremes_only`, `color_2_only`, `canonical_surface_only`, and `one_column_per_marker_color` rivals; retained first counterexamples in `workspace/profile_probe_after.json`.

**Failure mode/limitation:** Some input markers can already be cyan (`8`), making those individual cells look unchanged. Every ordinary lesson still contains visible blank gaps filled by the output.

## D4 — Include singleton columns and extra-marker columns

**Original state/rationale:** The old generator required at least two markers per occupied column and treated a single endpoint as a degenerate. That conflicts with the canonical program, where min row equals max row and therefore a singleton is a one-cell span.

**Decision:** `singleton_and_extra` contains one lawful singleton plus at least two informative spanning columns, one with an extra interior marker. This separates the real extreme rule from “ignore singletons” and “exactly two markers” shortcuts.

**Alternatives considered:** Make singleton-only lessons; accept arbitrary one-marker grids. Rejected because a singleton by itself does not demonstrate expansion. The profile keeps two visible span completions so the lesson remains identifiable.

**Probe/evidence:** `singleton_column` and `extra_marker_column` witnesses; `ignore_singleton_columns` and `exactly_two_markers_only` rivals; profile-probe refutation counts.

**Failure mode/limitation:** `self_check` still rejects a grid containing only singleton columns. That is a pedagogical distribution boundary, not a claim that the mathematical rule is undefined.

## D5 — Replace nine misleading axes with one exact macro-axis

**Original state/rationale:** The old `AXES` advertised dimensions, palette kind/size, active-column count, position bias, distinct-color count, density, and texture. Difficulty narrowed dimension and count ranges; several values were ignored or aliases; unknown keys were silently swallowed. The before override stage reported 14,915 concrete findings and 51,450 legacy multi-axis rejections.

**Decision:** Expose only `scene_profile`, whose four values are all accepted, semantically live, and recovered from the returned grid by `observe_overrides`. Geometry, colors, and counts still vary internally through keyed RNG draws.

**Alternatives considered:** Preserve every old axis and enumerate incompatibility declarations; mark most axes diagnostic; clamp impossible combinations. Rejected because this would retain a large API with little useful control, or make requested values silently inexact. One honest macro-axis is easier for training consumers and review tooling to reason about.

**Probe/evidence:** Exact override round-trip tests, unknown-key tests, after override stage pass.

**Failure mode/limitation:** Callers can no longer request an exact height, width, or active-column count. Those were not reliably honored before. A future need should add a new exact axis only with cross-profile compatibility and observer tests.

## D6 — Use a five-example schedule with two canonical anchors

**Original state/rationale:** The first four-profile implementation gave one canonical profile per four residues, but the repository’s pinned random sample indices hit it only 10/60 times (16.7%), below the 25% canonical-envelope policy.

**Decision:** Use `canonical_pairs, canonical_pairs, adjacent_shared, mixed_extremes, singleton_and_extra`. Any five consecutive indices contain all four semantic profiles; the pinned profile-floor census now exceeds 25%, and the local sequential probe measures 24/60 (40%) exact canonical signatures.

**Alternatives considered:** Exploit the coarse profile metric by giving noncanonical profiles canonical dimensions and palette cardinality; weaken the profile-floor threshold; remove broad profiles. Rejected because those options optimize the metric without increasing literal canonical support or reduce semantic breadth.

**Probe/evidence:** Test `test_pinned_profile_floor_has_at_least_twenty_five_percent_exact_anchors`; retained failed after iteration at `checks/after` was replaced by the final exact run, while the intermediate failure is described in notes; `checks/profile-retest` records the targeted passing rerun.

**Failure mode/limitation:** Generated lessons use five demonstrations rather than the canonical two. This is deliberate to guarantee rival elimination under every schedule offset.

## D7 — Narrow `self_check` to informative grammar, not canonical surface

**Original state/rationale:** Two definitions existed. The surviving one mixed semantic requirements with unjustified surface constraints and accepted the `already_filled` identity texture.

**Decision:** Keep exactly one checker. It validates ARC shape/cells, requires at least two spanning columns with spans of at least three cells, and requires at least one visible blank inside a span. It allows adjacency, mixed/repeated colors, extra markers, and singleton control columns.

**Alternatives considered:** Make `self_check` accept every grid on which the Racket rule is defined. Rejected because all-background, already-filled, or singleton-only inputs are lawful but poor teaching examples and make the checker non-probative.

**Probe/evidence:** Canonical acceptance tests, mutation fixtures, before/after self-check and defect-lint stages.

**Failure mode/limitation:** The checker encodes training usefulness, not the complete mathematical domain. Reports and docstrings state this distinction explicitly.

## D8 — Declare semantic rivals and make the lesson falsifiable

**Original state/rationale:** The old generator had only prose claims about generic rivals and no executable semantic contract. The before semantic gate was advisory `NO_CONTRACT`.

**Decision:** Add strict-canonical, witness, rival, schedule, and lesson-identifiability hooks. Five shortcuts are marked canonical-fitting; two additional rivals target adjacency and repeated colors. Every witness names a rival that the Racket-backed semantic gate can verify on the same grid.

**Alternatives considered:** Rely on marginal diversity/profile gates; add prose-only examples. Rejected because marginal morphology can be diverse while every lesson still supports the wrong rule.

**Probe/evidence:** Task-local rival tests, `workspace/profile_probe.py`, after semantic gate pass.

**Failure mode/limitation:** The rival set is not exhaustive. It targets the strongest surface shortcuts exposed by the canonical examples and former generator grammar; future audits can add newly discovered rivals.

## D9 — Add reusable regression tooling

**Original state/rationale:** The workspace contained only a placeholder README.

**Decision:** Add nine task-local tests and `workspace/profile_probe.py`. The probe reports profile counts, canonical profile rate, witness hits, canonical-shortcut fit, first exact counterexamples, and lesson-identifiability status.

**Alternatives considered:** Keep only battery logs. Rejected because the full Racket battery is slower and less convenient for iterating on distribution design.

**Probe/evidence:** `workspace/profile_probe_after.json`; direct pytest command recorded in `RESULTS.json`.

**Failure mode/limitation:** The probe uses the Python audit mirror and is therefore diagnostic only. It prints that limitation and points users to the Racket-backed battery.
