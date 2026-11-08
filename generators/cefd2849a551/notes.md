# Working notes: `cefd2849a551`

## Current rule and authority

A lawful input has one monochrome, hole-free, 4-connected object on background 0. The object retains a one-cell background margin and contains at least one cell whose four cardinal neighbours are also object cells. The output keeps exactly the object's 4-neighbour boundary in the original color and erases its interior. The canonical Racket behavior was not changed; `RULE_HASH` is pinned to `4681778f7a43`.

## 2026-10-19 review repair

**Prior choice.** Version 1.3.1 advertised nine axes, including singleton/dead controls and a `texture` axis containing blank, hollow, and singleton negatives. `self_check` accepted important semantic impostors, authority was unpinned, canonical profile support was weak, and shortcut comments were not executable.

**New choice.** Version 2.0.0 exposes only four total, observable axes: `grid_h`, `grid_w`, `shape_kind`, and `palette_kind`. It constructs one validated object from a rectangle/step/L/T grammar, rejects malformed calls and grids, and cycles the four shapes by sample index. Two schedule positions use exact canonical dimensions; two retain broad difficulty-banded dimensions. Palette groups are disjoint so exact palette overrides are observable while each scene remains monochrome.

Each complete lesson has three demonstrations and one query from a four-profile period. The declared rivals are identity, 8-neighbour boundary, and bounding-box perimeter. `lesson_identifiable` requires the demonstrations to refute every rival that would answer the query differently. The compact witness `counterexamples/semantic-rivals.json` is replayed by the focused suite.

## Final evidence

- Generator SHA-256: `471045dad2d3628f045b00a438a3c9d507871b84c8d3fc56003c12a80a7e4ae8`.
- Full after battery: 12 green, 0 advisory, 0 failed.
- Portable focused suite: 109 passed, 0 failed.
- Profile floor: 26/60 exact and 27/60 envelope; every band has exact support.
- Override audit: 32,760/32,760 accepted draws, 0 findings, 0 warnings.
- Lesson census: 300/300 production lessons and 1,200/1,200 query rotations with no ambiguity against the three declared rivals; 765 unique inputs.

## Known limits and open questions

The generator intentionally covers four hole-free shape families, not every object accepted by the Racket program. The schedule is deterministic and therefore not a natural shape-frequency model; it is a teaching guarantee. Identifiability results are finite and rival-bounded, not a proof against all hypotheses. Any downstream assembler that changes the three-demonstration requirement or breaks consecutive four-profile windows must rerun the rotation/lesson gates.
## Current reviewer considerations

Source SHA-256: `471045dad2d3628f045b00a438a3c9d507871b84c8d3fc56003c12a80a7e4ae8`.

# Decisions for `cefd2849a551`

## D1 — Preserve the Racket output law and pin it

**Prior choice.** Version 1.3.1 described the correct “cardinal outline only” rule but did not declare `RULE_HASH`, leaving source-to-authority binding implicit.

**Decision.** Keep the canonical Racket behavior unchanged and pin `RULE_HASH = "4681778f7a43"`.

**Alternatives considered.** Rewriting the authority to match a narrower Python grammar was rejected: no output-law defect was reproduced, and generator restrictions should not redefine the canonical task.

**Probe/evidence.** Rule smoke, Racket lint, authority sync, canonical-pair oracle checks, and the real-Racket task test are green. The main residual risk is only untested authority behavior outside the sampled lawful manifold.

## D2 — Replace the advertised axis surface with four total controls

**Prior choice.** The baseline advertised `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` in addition to dimensions/shape/palette. Several were fixed, aliases, dead, or allowed unlawful negative fixtures; unknown controls were not rejected reliably.

**Decision.** Expose only `grid_h=6..16`, `grid_w=7..18`, `shape_kind=rect|step|L|T`, and `palette_kind=default|warm|cool|varied`. Reject unknown keys, wrong types (including booleans), out-of-range values, invalid difficulty, and negative sample indices.

**Alternatives considered.** Keeping compatibility aliases was rejected because metadata is an executable contract, not documentation trivia. Declaring incompatibility combinations was unnecessary because the constructor supports the full cross-product.

**Probe/evidence.** The override gate accepted 32,760/32,760 draws across 364 cases with no finding/warning; task tests exercise all 64 shape/palette/band combinations plus dimension endpoints. A future expansion should add a real pixel-observable control rather than reviving a dead axis.

## D3 — Use one truthful object manifold

**Prior choice.** Degenerate textures could emit a blank grid, hollow ring, or singleton, while `self_check` could accept them despite the stated requirement for a solid object with interior.

**Decision.** Generate exactly one monochrome, 4-connected, hole-free object, separated from the canvas edge by background and containing at least one cardinal interior cell.

**Alternatives considered.** Multiple objects, holes, edge-touching objects, and arbitrary polyominoes are mathematically compatible with variants of outline extraction but are not needed to teach this canonical task. Keeping them as “hard” cases would enlarge the hypothesis class and complicate validation without canonical evidence.

**Probe/evidence.** The validator independently checks connectivity, margin, interior, and background reachability. Mutation fixtures reject blank, singleton, hollow, disconnected, ragged, noninteger, and multicolor cases. Defect lint and all focused tests pass.

**Limitation.** This is a curriculum boundary, not a claim about the full Racket domain.

## D4 — Choose four shape profiles that expose the rule

**Prior choice.** Shape selection was random and the generated shape could be convex, leaving 4-neighbour boundary, 8-neighbour boundary, and bounding-box perimeter extensionally equal on a sample.

**Decision.** Cycle deterministically through a rectangle, one-cell corner step, larger corner-notch L, and thick T. Every shape has interior; three are concave.

**Alternatives considered.** Pure random sampling was rejected because witness frequency does not guarantee a complete lesson. Making every grid maximally concave was rejected because it would remove the ordinary rectangular case and create another artificial shortcut.

**Probe/evidence.** `LESSON_SCHEDULE_PERIOD = 4`; task tests exhaust cyclic starts and all four query positions in easy/medium/hard. The retained sample at seed 711/sample 1 disagrees with identity, 8-neighbour, and bounding-box rivals and is stored in `counterexamples/semantic-rivals.json`.

**Failure mode.** A consumer that assembles fewer than three demonstrations, skips schedule slots, or samples nonconsecutive indices can lose the guarantee. The generator declares `EXAMPLES_NEEDED = 3`; downstream assembly must honor it.

## D5 — Anchor canonical profiles while retaining broad dimensions

**Prior choice.** Baseline defaults rarely reproduced the two canonical `(height,width,color-count)` profiles, making the profile-floor result advisory.

**Decision.** Schedule profiles 0 and 1 at exact canonical dimensions 6×9 and 6×7; profiles 2 and 3 sample broader difficulty-banded dimensions. Overrides retain full 6..16 by 7..18 support.

**Alternatives considered.** Copying all canonical coordinates was rejected as overfitting. A purely broad uniform draw was rejected because it does not provide robust exact support in each band.

**Probe/evidence.** In 60 final profile draws: exact 26, envelope 27; per-band exact support is easy 9, medium 10, hard 7. All three canonical inputs pass strict validation.

**Limitation.** Exact-profile frequency is intentionally higher than a natural uniform distribution; dimensions alone should not be treated as the semantic teaching signal.

## D6 — Make palette controls observable without changing color semantics

**Prior choice.** `palette_kind`/`texture` behavior was ambiguous and entangled with dead `palette_size`/`n_distinct_colors` controls.

**Decision.** Use four disjoint color sets: default `{4}`, warm `{2,3}`, cool `{1,8}`, varied `{6,7,9}`. Each grid still has exactly one foreground color, and the palette kind can be recovered from pixels.

**Alternatives considered.** Overlapping palettes were rejected because exact override observation would be ambiguous. Multiple foreground colors were rejected because the canonical task is a single monochrome object.

**Probe/evidence.** Every joint palette/shape/band override is generated, validated, and recovered by `observe_overrides`.

**Limitation.** Disjoint groups make palette-kind classification easy, but color does not predict output structure because every group appears across every shape.

## D7 — Fail closed in validation

**Prior choice.** Baseline `self_check` mainly checked rectangularity, ARC range, and at most one nonzero color; it returned no error for the declared `no_object` negative and did not enforce the core geometry.

**Decision.** Validate literal integer cells, dimensions, one nonzero color, one component, margin, interior, background, and no enclosed holes. Constructor failures raise instead of silently falling back or resampling.

**Alternatives considered.** Provenance-based validation (checking hidden profile labels/coordinates) was rejected because canonical and external lawful inputs must be accepted based on pixels alone.

**Probe/evidence.** Canonical acceptance, mutation tests, defect lint, selfcheck, and strict semantic census are green; strict rate is 600/600.

## D8 — Add an executable semantic contract

**Prior choice.** The baseline comments named possible shortcuts but exposed no executable rivals, witnesses, or lesson-level hook.

**Decision.** Declare three rivals: identity, 8-neighbour boundary, and bounding-box perimeter. Bind them to witnesses for erased interior, cardinal-vs-diagonal boundary, and object-vs-bounding-box outline. `lesson_identifiable` validates labels and rejects any lesson whose demonstrations leave a declared rival alive when it changes the query.

**Alternatives considered.** Prose-only documentation and isolated witness-frequency checks were rejected because neither establishes that the assembled training lesson teaches the intended rule.

**Probe/evidence.** Semantic smoke: 12/12 production lessons identifiable and 0/48 ambiguous rotations. Large census: 300/300 lessons, 0/1,200 ambiguous rotations, 765 unique inputs. The evidence is finite and restricted to declared/generic tested rivals.

## D9 — Build portable independent tooling

**Decision.** Add `workspace/reference_probe.py` with an independent cardinal-boundary oracle, canonical loader, observable-axis helper, and supported Racket bridge. Add focused tests under the task directory using portable paths and `GENERATOR_UNDER_TEST`.

**Why.** Future agents can replay authority parity, canonical acceptance, overrides, mutations, schedule windows, and exact counterexamples without trusting generator internals.

**Probe/evidence.** The suite was observed red before implementation and now has 109 passing tests in the isolated task-test runtime. The exact counterexample file is itself replayed and source-hash-bound.

## D10 — Keep genuine failures and separate interrupted evidence

The before battery and red test logs are retained. An early combined profile-floor command was interrupted by an outer timeout and is not represented as a pass; the clean rerun is under `checks/iter2-profile-floor`. All final positive claims use completed reports from unchanged generator bytes.
