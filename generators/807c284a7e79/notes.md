# Working notes: 807c284a7e79

## 2026-10-04 review repair

Baseline `a911644e359ee606a85b6883e98b60aec0c63b64b28268cf4ae55a43931831ea` had a fixed connected layout, no pinned `RULE_HASH`, ten mostly dead or overlapping controls, silent unknown-key acceptance, and no executable teaching contract. All five public examples are connected, so both `paint_all_non_walls` and `paint_largest_component` reproduce every public pair.

Version `3.0.0` replaces that surface with four exact and observable axes: height, width, wall orientation, and semantic scene profile. A deterministic three-slot schedule emits connected, seed-in-smaller-split, and seed-in-larger-split scenes; seed checkerboard parity alternates. The module declares rivals, witnesses, a pure Python rule mirror, lesson identifiability checks, exact override observation, strict structural validation, and mutation fixtures.

An intermediate candidate left `difficulty` inert and was rejected by the dead-band probe. The final generator uses difficulty-aware default size draws while preserving the full exact size domain for every explicit override. A separate odd-dimension bug that could create equal split chambers was caught by tests and fixed by excluding equal-area wall positions.

Final generator SHA-256: `110242d9a417413ab18bfe8830a464a46917fa4f3ba9e436214bcbf4302f6216`. Final battery: 12/12 green. Task tests: 97/97 passed. Production lesson census: 300/300 materialized, 0 ambiguous, 0 scoring errors; every declared rival was refuted in every 100-lesson band cohort.

The archival bank entry's selected `target_code` was made byte-identical to its already-selected `raw_code`; canonical rule text, `RULE_HASH`, and behavior did not change. See packet-root `REVIEW.md`, `DECISIONS.md`, and `checks/` for exact commands and retained evidence.
## Current reviewer considerations

Source SHA-256: `110242d9a417413ab18bfe8830a464a46917fa4f3ba9e436214bcbf4302f6216`.

# Decisions — 807c284a7e79

## D1 — Replace the advertised control surface with four honest axes

**Choice.** Keep only `grid_h`, `grid_w`, `scene_profile`, and `wall_orientation`. Every value is exact, validated before generation, recorded through keyed draws, and recoverable from returned pixels by `observe_overrides`.

**Why.** The baseline declared ten controls, including singleton metadata, aliases, dead textures, and negative fixtures inside the ordinary texture domain. The override gate measured 11,944 findings over 40,050 draws / 445 cases, accepted an unknown key, and found thousands of requested-versus-observed mismatches.

**Rejected alternative.** Repair each old texture and metadata axis. That would preserve a large API with little teaching value and many mixed-override interactions. A smaller surface is easier to falsify and gives downstream dataset builders controls that mean exactly what they say.

**Probe / failure mode.** The final override gate exercises the full domain, mixed axes, provenance, malformed values, and unknown keys. The cost is less superficial variety than a many-texture API; the semantic schedule supplies more useful variation instead.

## D2 — Make reachability evidence deterministic at the lesson level

**Choice.** `sample_index mod 3` cycles `connected`, `split_seed_small`, and `split_seed_large`; `EXAMPLES_NEEDED = 3`. Any consecutive three demonstrations therefore include an unreachable chamber and a case where the seed is not in the largest chamber.

**Why.** All five canonical pairs are connected. Consequently, both `paint_all_non_walls` and `paint_largest_component` fit every public output. Randomly emitting a disconnected case at some marginal frequency would not guarantee that a specific training lesson contains the disambiguating evidence.

**Rejected alternatives.** (1) Keep only connected examples and rely on the written rule: this trains the shortcut. (2) Sample split scenes probabilistically: this permits all-connected lesson windows. (3) Always seed the smaller chamber: this refutes the largest-component rival but creates a new “always choose smaller” shortcut. Cycling both roles avoids that.

**Probe / failure mode.** `lesson_identifiable` rejects any lesson whose demonstrations leave a declared competitor fitting. The 300-lesson production census covered all six combined profile/orientation start residues and found 0 ambiguous lessons. This remains finite declared-rival evidence, not universal induction.

## D3 — Alternate wall orientation and seed parity independently

**Choice.** `sample_index mod 2` alternates vertical and horizontal walls, and the seed is selected from a target-chamber cell with alternating absolute checkerboard parity.

**Why.** Orientation prevents a vertical-layout shortcut. Alternating seed parity refutes a checkerboard anchored to absolute grid origin rather than to distance from the seed.

**Rejected alternative.** Let both be purely random. Randomness improves marginal variety but cannot guarantee each short lesson witnesses both parities or both orientations. The combined schedule has period six, which is cheap to cover exhaustively.

**Probe / failure mode.** `absolute_origin_checkerboard` is a declared rival and was refuted in every census lesson. Because only two wall orientations are generated, this does not test curved or multi-wall layouts.

## D4 — Use unequal split chambers and explicitly schedule the seed side

**Choice.** A split wall spans the full interior and is chosen only from positions that create unequal chamber sizes. `split_seed_small` and `split_seed_large` then select the appropriate component before placing the seed.

**Why.** “Smaller” and “larger” must be observable and unambiguous. An early implementation allowed an odd-size split to produce equal chambers; the regression test failed first, then the wall-position domain was narrowed to exclude equality.

**Rejected alternative.** Break ties arbitrarily. A hidden tie-break would make the semantic axis unrecoverable from pixels and encourage position-specific shortcuts.

**Probe / failure mode.** Tests cover every legal size/orientation/profile combination and assert exact observation. Smaller chambers must contain at least six cells, preventing trivial one-cell witnesses.

## D5 — Preserve canonical-size support while giving difficulty an honest effect

**Choice.** Heights are 8–12 and widths 10–14. The first five slots of each ten-sample cycle pin the five canonical shape signatures; other slots draw within the full envelope. `draw_int_diff` changes the default size distribution by difficulty but validates explicit overrides against the same complete domain in every band.

**Why.** Canonical support should be deliberate, not an accidental low-probability event. Difficulty must produce observable data differences without making a size legal in one band and illegal in another.

**Rejected alternatives.** Band-specific exact domains caused the baseline’s override contradictions. Ignoring difficulty passed the first implementation tests but was caught by the dead-band detector.

**Probe / failure mode.** The intermediate failure is retained at `checks/intermediate/dead-bands.json`; the final profile-floor, defect-lint, distribution, and override stages are green. Canonical anchoring introduces repeated shapes, but seed location and wall placement remain stochastic and exact inputs remained highly diverse (952 unique across 1,200 overlapping pairs).

## D6 — Validate the task grammar rather than a single constructor template

**Choice.** `self_check` analyzes colors, border, seed count/location, interior walls, one or two four-connected passable components, reachable component size, and unequal lawful split chambers. `strict_canonical_like` delegates to that broad grammar, so all public inputs remain valid.

**Why.** A validator that merely recognizes the generator’s own exact layout cannot catch semantic errors and may reject lawful canonical inputs. The analyzer is also reused by `observe_overrides`, semantic observables, rivals, and the rule mirror, avoiding conflicting interpretations.

**Rejected alternative.** Validate only dimensions and colors. That would accept missing seeds, broken frames, isolated seeds, mixed unsupported colors, and semantically undefined splits.

**Probe / failure mode.** Mutation fixtures cover missing seed, broken border, unknown color, missing interior wall, and isolated seed. The grammar intentionally permits a wider lawful set than the constructor generates, but still only one or two components.

## D7 — Keep Racket authoritative and make Python independently auditable

**Choice.** Pin `RULE_HASH = 229d8e0a7e30`, retain the canonical Racket program as label authority, and provide a pure Python BFS mirror plus `workspace/reference_probe.py` for independent structural, shortcut, determinism, and optional Racket parity checks.

**Why.** The Python mirror makes tests and curriculum diagnostics fast, while selected Racket execution prevents a shared Python bug from silently defining labels.

**Authority text decision.** The selected archival bank carried two behavior-equivalent source texts that differed only in comments/formatting. I set `target_code` equal to the existing `raw_code`; canonical source, rule hash, and execution behavior were not changed.

**Probe / failure mode.** Ninety-seven task tests include Racket parity, and the battery’s authority-sync stage reports one exact source group with execution parity PASS. A future canonical rule edit requires a new hash and complete re-review.

## D8 — Stop after the smallest source-bound repair that passes production-shaped checks

**Choice.** Do not add arbitrary maze generation, additional colors, multiple seeds, or new task semantics. Update the stale task summary/notes, add focused tests and a reusable probe, and leave unrelated audit targets untouched.

**Why.** Those extensions would change the generator domain and multiply rival hypotheses without evidence they improve this task’s training value. The current repair directly addresses measured failures and public-data ambiguity.

**Remaining limitation.** A learner can still exploit the single-straight-wall distribution. Expanding to multi-turn walls should be a separate reviewed version with observable controls and guaranteed lesson witnesses, not an untested “more diversity” edit.
