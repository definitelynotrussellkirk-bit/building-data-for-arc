# Current notes: ec491e97a5d5

## Intended rule

Treat each nonzero four-connected component as an independent solid monochrome rectangle. Replace that component by the one-cell perimeter of its own bounding rectangle and clear its strict interior to background `0`. The selected Racket authority remains unchanged at rule hash `56f21366dd85`.

## Repair status

The baseline sampler was replaced by a constructive curriculum. It now:

- owns all four canonical inputs and accepts them through `self_check`;
- exposes only four exact controls that are actually honored: `grid_h`, `grid_w`, `n_rects`, and `n_colors`;
- rejects unknown/coercive arguments and declares the three impossible `n_colors > n_rects` count combinations;
- preserves canonical-profile support while varying geometry by difficulty;
- alternates a `shortcut_witness` profile with a `canonical_core` profile on a period-2 schedule;
- declares and tests the strongest canonical-fitting rival, one global bounding box per foreground colour.

Final selected generator SHA-256: `f87a59961e2e3393c940120d6ce5e83b8db84a355a2088b969ddfff26697ce36`.

## Teaching policy

A lesson contains three demonstrations and one query. Every four-pair window has two repeated-colour witness pairs, so every cyclic query position leaves at least one witness in the demonstrations. The witness separates component-wise hollowing from the `by_color` rival. The exact retained counterexample is `counterexamples/by_color_shortcut.json`.

Measured final evidence:

- 12/12 after-battery stages green;
- 63/63 portable task-local tests pass;
- strict semantic support 600/600 generated inputs;
- fixed-seed schedule census: 6/6 lessons and 24/24 query rotations identifiable;
- broad census: 300/300 lessons and 1,200/1,200 query rotations identifiable against declared rivals;
- profile floor: 51/60 exact canonical-profile hits and 54/60 envelope hits;
- override matrix: 23,490 accepted draws, 270 declared incompatibility rejections, zero findings.

## Parametric extension

`workspace/parametric/` is a prototype only. It selects `border_thickness` once per episode from `{1, 2}`. Both exact Racket programs and public examples are retained; all checked pairs agree with Racket, and every demonstration distinguishes the two retained settings. It does not alter or approve the canonical thickness-1 rule.

## Known limits

The semantic evidence is finite and scoped to the declared `by_color` rival plus the battery's bounded generic rival search; it is not a proof against every possible induction rule. The parametric prototype currently assumes one solid rectangle per foreground colour and rectangle sides of at least five.
## Current reviewer considerations

Source SHA-256: `f87a59961e2e3393c940120d6ce5e83b8db84a355a2088b969ddfff26697ce36`.

# Decisions — ec491e97a5d5

## D1: Preserve the canonical rule

**Decision.** Keep the selected Racket authority unchanged at rule hash `56f21366dd85`.

**Reason.** All four canonical pairs consistently express object-wise hollowing of solid rectangular components. The baseline defects were generator ownership, distribution, controls, and lesson identifiability—not label semantics. Final rule-smoke and authority-sync stages are green.

## D2: Replace the brittle sampler instead of patching individual failures

**Prior choice.** The baseline exposed many controls that were not faithfully implemented, rejected canonical inputs, had no pinned `RULE_HASH`, and could generate lessons compatible with a minimal shortcut.

**New choice.** Construct lawful inputs directly from rectangles and expose only four observable axes:

- `grid_h`: 8–16;
- `grid_w`: 9–18;
- `n_rects`: 2–4;
- `n_colors`: 1–4.

The only impossible joint requests are the three cases where `n_colors > n_rects`; these are declared explicitly. A single `n_colors` override raises the dependent default `n_rects` as needed, while an explicitly incompatible pair still fails loudly.

**Evidence.** The final override gate exercised 264 cases × 3 bands × 30 seeds = 23,760 draws: 23,490 accepted, 270 declared incompatibility rejections, zero findings or warnings. See `checks/after-final/checks/ec491e97a5d5_after_override_results.json`.

## D3: Own the canonical domain and retain profile support

**Decision.** `self_check` accepts exactly 2–4 solid monochrome rectangular components, 1–4 foreground colours, background 0, sides at least 2, and at least one rectangle with a strict interior. Malformed grids, non-rectangular components, empty teaching cases, coercive scalar values, and unknown overrides are rejected.

Dimensions are drawn from the full declared domains but strongly weighted toward the four canonical height/width profiles. Difficulty changes rectangle geometry only; it does not remove any advertised override value.

**Evidence.** All four canonical inputs pass. The final profile floor has 51/60 exact hits and 54/60 envelope hits, with exact support in every band: easy 18/20, medium 18/20, hard 15/20. See `checks/after-final/checks/ec491e97a5d5_after_profile_floor.json`.

## D4: Teach against the strongest canonical-fitting shortcut

**Shortcut.** Hollow one global bounding box per foreground colour. It fits all four canonical pairs because no canonical colour is split across objects.

**Decision.** Alternate two profiles on `LESSON_SCHEDULE_PERIOD = 2`:

1. `shortcut_witness`: three separated rectangles using two colours, forcing one repeated colour;
2. `canonical_core`: two differently coloured rectangles touching along an edge, preserving a canonical structural relation.

A lesson uses three demonstrations plus one query. Every four-pair window therefore contains two witness pairs; after holding out any one query, at least one witness remains in the demonstrations. The author hook and declared rival independently check this property.

**Evidence.** The battery smoke check found 12/12 identifiable lessons and 48/48 identifiable query rotations. The fixed-seed period census exhausts 6/6 band/start lessons and 24/24 query rotations. The broad production census found 300/300 lessons and 1,200/1,200 rotations identifiable, with 1,062 unique inputs and no materialization, hook, or scoring errors. See `checks/final-schedule-period-s0.json` and `checks/lesson-census-final.summary.json`.

**Limitation.** These are finite checks against declared and bounded searched rivals, not proof of unique induction against every conceivable rule.

## D5: Retain an exact counterexample as executable documentation

**Decision.** Store `repo/generators/ec491e97a5d5/counterexamples/by_color_shortcut.json`, containing an exact input, selected Racket output, rival output, source/rule hashes, and validator result. A task-local test loads the file and checks all fields against the live generator.

**Evidence.** `checks/counterexamples/ec491e97a5d5/by_color_racket.json` is the supported `arcpuzzles apply` receipt. The regression was written red-first (`checks/red-counterexample-test.log`) and then passes (`checks/green-counterexample-test.log`).

## D6: Add a bounded parametric prototype, not a canonical rule change

**Parameter.** `border_thickness ∈ {1, 2}`, chosen once per episode by seed parity. Canonical/default remains 1.

**Why suitable.** It changes the executed transformation, admits compact exact Racket programs, and can be distinguished by demonstrations when rectangle sides are at least five.

**Scope.** The prototype is isolated under `workspace/parametric/`. It assumes one solid rectangle per foreground colour and does not generalize the production repeated-colour component semantics. It is proposed evidence only; it neither changes the selected generator's Racket path nor refreshes approval metadata.

**Evidence.** Seed 17 materializes both settings. Every checked pair matches its exact Racket program and every demonstration refutes the alternative thickness. Racket SHA-256 values are `40f23fe4e7eb3f9bf29f330e7a12bc4b4b72d83ecdb710650f66250849e0556a` for thickness 1 and `f2c7e41add404599daaf274e085870d6dd63ad4bddd1d80ad1fc67377c19791c` for thickness 2. See `checks/parametric/border-thickness-seed17.json`.

## D7: Rejected alternatives

- **Keep one colour per rectangle.** Rejected because it leaves the strongest canonical-fitting `by_color` shortcut untested.
- **Use only separated rectangles.** Rejected because it would lose the canonical touching relation and narrow structural support.
- **Advertise texture, palette, or position controls without exact observability.** Rejected; only controls exercised by the override gate remain.
- **Make difficulty alter axis availability.** Rejected after a regression showed byte-identical bands; difficulty now changes geometry while every exact control remains reachable in every band.
- **Fold thickness 2 into production immediately.** Rejected because it is a new rule family requiring separate approval and broader component semantics.

## D8: Solve records

The blind pre-repair task `cc8c719680e6` was solved in one substantive attempt with no earlier exposure or reference consultation, passing 4/4 visible examples. The post-repair task `ec491e97a5d5` was also solved in one attempt, passing 3/3 visible examples; earlier rule exposure was declared `yes`, and no reference was consulted during that solve. Both finished records are preserved under `solve-blind/` and `solve/`.
