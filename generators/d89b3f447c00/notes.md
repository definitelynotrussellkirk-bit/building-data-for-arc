# Current generator account: d89b3f447c00

## Parametric candidate — review-acc174ca601cc58b

`workspace/parametric/` adds episode-fixed `completion_rounds=1|2` while keeping
production 3.1.0 and exact selected canonical bytes unchanged. Two rounds mean
two synchronous applications: the second searches the actual updated grid, not
an in-place scan or unconditional full closure. Long six-to-nine-row chains,
gapped coordinates, disconnected same-color islands, minimal L clues, completed
squares and up to nine independent colors expose those distinctions. The native
contract supports 2–6 demos and 1–4 queries independently, defaulting to 3/4.

Fresh review found that the first candidate's multi-color-only demonstrations
allowed a rule that ignores single-color queries. Its two-setting counterexample
was replayed through protected Racket. Replacing the second core demonstration
with a compact one-color chain fixed both palette and small-canvas teaching gaps
without increasing demo count. The first multi-color demo retains minimal-size,
preservation, disconnected-component and all-color teaching. The regression was
observed failing before repair and passing afterwards.

The source-current audit and focused test evidence are inventoried under
`workspace/parametric/evidence/current/`; qualification, protected causal replay,
and single-query views are returned under `checks/d89b3f447c00/`. The candidate
README records exact grammar, limits and commands. This packet's native
`preview-public` helper is reused, with its existing focused rejection tests,
instead of adding a duplicate exporter. The independent rival/audit tools remain
task-local and reusable.

Next owner action is exact-source qualification and acceptance after intake.
Reviewer readiness is not owner acceptance or training admission. Finite motifs,
disjoint color regions and a finite rival bank remain explicit limits; no
universal rule uniqueness or cross-color collision coverage is claimed.

## Earlier production account (retained)

## Intended rule and authority

The selected canonical Racket program remains the only label authority. Its normalized source hash is pinned as `RULE_HASH = "1bf2bf24e722"`; this review did not change the Racket source or canonical examples. The task completes the missing fourth corner of every axis-aligned rectangle for which one foreground color occupies exactly three corners, using the original input as the one-pass source.

## Generator v3.1.0

The generator now constructs, rather than retries, `1..5` disjoint color regions on a `6..20` by `6..20` zero-background grid. Every color has exactly one induced three-corner rectangle, completion targets are distinct, and a requested rectangle count is never silently dropped. The only advertised exact controls are `grid_h`, `grid_w`, and `rect_count`; each is type/range checked and observable through `observe_overrides`. `seed` must be an exact integer and `sample_index` an exact nonnegative integer.

Four deterministic schedule profiles repeat every four sample indices:

- `canonical`: two colors, no extra markers, non-minimal rectangles, and one of the four exact canonical `(height, width)` shapes.
- `many`: four or five colors, one interior same-color distractor, and at least one minimal rectangle when feasible.
- `extra_marker`: canonical dimensions and two colors, but one color has an interior fourth point. This isolates the anti-shortcut witness from size/palette drift and raises exact canonical-profile support.
- `minimal`: three colors and a boundary-touching minimal rectangle.

The profile set supplies redundant witnesses against the declared `two_colors_only`, `three_markers_only`, and `nonminimal_only` rivals. With four examples, every cyclic choice of one query leaves three demonstrations that refute every declared rival. Exact overrides take precedence over profile decoration: on cramped requested canvases, optional distractor/minimal styling may be dropped, but dimensions and rectangle count are preserved exactly.

## Reversed baseline decisions

The baseline advertised `palette_kind`, `palette_size`, `n_distinct_colors`, and `texture` without consuming them. They were retired instead of retained as misleading no-ops. The baseline rejection loop could also underfill requested layouts; it was replaced with guillotine partitioning that either constructs the exact request or raises a clear error. A Python rule mirror, authority pin, semantic witnesses/rivals, malformed-grid validation, strict profile, and focused portable tests were added.

## Known limits

The generated domain is intentionally narrower than the full canonical law: it produces one induced rectangle per color, at most one extra same-color marker, no overlapping color regions, and no shared completion targets. The canonical Racket rule can handle broader lawful configurations, including multiple rectangles for one color; this generator does not claim coverage of that full combinatorial domain. The finite rival set establishes declared-rival identifiability, not uniqueness against every possible hypothesis.

Final generator SHA-256: `a94e1ae857063d08e63cf6acb23f54bd3d171207af7c3369f9e580100f06423e`.
## Current reviewer considerations

Source SHA-256: `a94e1ae857063d08e63cf6acb23f54bd3d171207af7c3369f9e580100f06423e`.

# Decisions and rationale

## D1 — Preserve canonical authority; repair the sampler

The four canonical pairs and selected Racket source consistently express same-color missing-corner completion. The baseline failures were generator-contract and curriculum defects, not evidence that the reference law was wrong. I pinned `RULE_HASH = 1bf2bf24e722`, added an exact Python mirror for tests, and left the Racket authority unchanged. Rejected alternative: edit the rule to match the sampler's narrower behavior; that would make labels less general and sever canonical authority.

## D2 — Retire fake axes instead of fabricating semantics

The baseline declared `palette_kind`, `palette_size`, `n_distinct_colors`, and `texture` but did not consume them. Keeping them would let data jobs believe they exercised controls that had no effect. The repaired API advertises only `grid_h`, `grid_w`, and `rect_count`, and rejects unknown/retired keys. Probe: every min/max combination of those three axes round-trips through `observe_overrides` in every difficulty band. Rejected alternative: implement unrelated palette/texture knobs solely to preserve a misleading interface.

## D3 — Replace rejection sampling with constructive packing

The old loop could fail to place all requested rectangles and silently return fewer clues. The new guillotine partitioner proves capacity recursively and creates exactly the requested count; impossible requests fail loudly. This improves exact overrides and avoids seed-dependent underfill. Rejected alternative: raise the retry count, which reduces but does not eliminate the failure mode.

## D4 — Use a four-profile, rotation-safe teaching schedule

`canonical`, `many`, `extra_marker`, and `minimal` repeat every four indices. The three noncanonical witnesses separately challenge color-count, point-count, and rectangle-size shortcuts; each witness appears at least twice across a four-example lesson, so any one held-out query still leaves a refuting demonstration. `lesson_identifiable` evaluates the actual demo labels against declared rivals. Rejected alternative: rely on aggregate witness frequency, which does not guarantee that each complete lesson or query rotation is identifiable.

## D5 — Put one adversarial profile on canonical morphology

The first repair made `extra_marker` larger than every canonical example. The final profile-floor battery measured only 13/60 (21.7%) canonical-envelope draws. I moved `extra_marker` to exact canonical dimensions and two colors while retaining its interior distractor. This isolates the semantic change from scale/palette cues and raises exact/envelope support to 24/60 across all bands. Rejected alternative: game the pinned seed residue or increase the nominal canonical schedule frequency without improving the conceptual contrast.

## D6 — Exact controls outrank optional profile decoration

A caller may request a 6×6 grid with five rectangles, where a 3×3 distractor profile cannot fit. The generator preserves requested dimensions/count and degrades only extra-marker or nonminimal styling when infeasible. Rejected alternative: reject jointly feasible exact controls because a non-axis teaching flourish cannot fit.

## D7 — Enforce call-scalar determinism

The final defect lint showed that boolean/string/float seeds and boolean/negative sample indices were accepted through Python coercions. The API now requires an exact integer seed and exact nonnegative integer sample index before any RNG context is created. Regression tests retain every detected invalid scalar.

## D8 — Scope and self-review

The source deliberately generates one induced rectangle per color, no overlapping regions, and at most one extra point. That is narrower than the canonical law and is documented rather than hidden. I specifically rechecked that moving `extra_marker` onto canonical dimensions did not create a new size-based shortcut: its only distinction from canonical morphology is the extra same-color interior point, while the `many` and `minimal` profiles independently retain color-count and minimal-size witnesses.

## D9 — Solve records remain source-bound

The first post-repair solve was bound to generator hash `4f00d8d…`. After the v3.1.0 call-contract/profile fix, I moved it to `checks/prior-solve/v3.0.0-hash-4f00d8d17472/` and prepared a fresh visible-only episode. The final solve is bound to `a94e1ae…`, passes 4/4 visible examples, declares earlier exposure `yes`, and reports no reference consultation during the solve.
