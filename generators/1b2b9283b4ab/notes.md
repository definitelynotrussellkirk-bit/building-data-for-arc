# Working notes: 1b2b9283b4ab

## Version 4.0.0 review decisions

The imported `3.0.2` sampler made every ordinary shared wall a doorway and used distinct single-cell seed colors. It therefore hid important graph and color distinctions. Its normal texture controls were ineffective, sampled dimensions could be clipped, and the same-color special case put doorway cells inside rooms. The repair builds explicit room graphs, puts doors on separating walls, chooses feasible dimensions before drawing, and validates actual component geometry for every texture. Detailed rationale and source-bound receipts are in [DECISIONS.md](../../../DECISIONS.md).

The selected Racket authority is unchanged: rule ID `3e13418e96c9`, program SHA-256 `3e13418e96c93147e7c87ec55070352d783b241e00f140ef2509279bf340e71c`. Effective seed color means the minimum color in a seeded room. Distance counts doorway edges. Equal nearest distinct colors produce `8`; repeated nearest seeds of one color do not. Unreachable rooms follow the authority's distance-`999` competition among all global effective seed colors.

Default lessons use three demonstrations and one query, with period four: `[witness, canonical, witness, explore]`. The two compound witnesses preserve visible evidence under every single-pair query holdout. Each witness distinguishes `seed_room_tie`, `largest_seed_in_room`, `ignore_doors`, `minimum_color_tie`, and `unreachable_zero`. The canonical profile anchor and exploratory slot provide other sizes and graph families. Explicit controls select authoring distributions and do not inherit the lesson guarantee.

The [final probe](../../../checks/room-graph/final/report.json) retains all three canonical checks, eight cell-observed witness orientations, 44 joint-control checks, and the emitted 4-by-10 same-color counterexample. Both `seed_room_tie` and `largest_seed_in_room` fit all three canonical pairs. [QUESTION_ANSWER.md](../../../QUESTION_ANSWER.md) gives the exact tie counterexample and actual Racket/rival outputs.

On generator SHA-256 `b7e78b1eaebfb919f8344017390dfda73beba17146c1cb20e1b170390dcb97ce`, the [final battery](../../../checks/after-final/result.json) has all 12 stages green. The [larger census](../../../checks/lesson-census-final.json) materializes 300 lessons and checks 1,200 rotations without ambiguity against five unique declared rivals. The [fixed-seed period census](../../../checks/schedule-census-final.json) covers 12 lessons and 48 rotations at seed `0` across all four starts and three bands.

Remaining scope: rectangular room lattices, seed inputs `2..6`, no input `8`, and a compound witness topology in half the scheduled draws. Eight symmetries and varied colors/sizes do not eliminate template learning. The finite-rival results are not universal identifiability or downstream learning evidence. Catalog approval remains derived separately.

The [tie-marker prototype](workspace/parametric/README.md) is **proposed**, separate from the repair: one episode-scoped parameter, default `8` or alternative `6`, with seed colors restricted to `2..5`. Its independent chain fixtures and materialized Racket programs have [separate execution evidence](../../../checks/parametric/final/report.json). No production parameter interface or canonical rule change is included.

Imported associated notes retain their original evidence and timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b7e78b1eaebfb919f8344017390dfda73beba17146c1cb20e1b170390dcb97ce`.

# Design decisions: 1b2b9283b4ab

The repair changes the input sampler, its controls, and its diagnostics. The selected canonical Racket program remains the label authority. The default lesson has **three demonstrations and one query**, drawn from the repeating profile schedule **`[witness, canonical, witness, explore]`**. Every query position is supported within the tested four-pair lessons; the evidence and the finite scope of that claim are recorded below.

## Source and authority binding

| Subject | Version / SHA-256 |
| --- | --- |
| Imported generator | `3.0.2` / `43a5059c196fa285764dfcf94f8bfc678f026fa08f0d069b990a806af89b7b29` |
| Repaired [generator.py](repo/generators/1b2b9283b4ab/generator.py) | `4.0.0` / `b7e78b1eaebfb919f8344017390dfda73beba17146c1cb20e1b170390dcb97ce` |
| Unchanged canonical Racket program | `3e13418e96c93147e7c87ec55070352d783b241e00f140ef2509279bf340e71c` |
| Declared rule ID | `3e13418e96c9` |

These identities are retained together in the [final room-graph probe](checks/room-graph/final/report.json). The [final battery](checks/after-final/result.json) also binds its result to the repaired generator hash and passes authority synchronization. Passing checks do not themselves change catalog approval or training admission.

## What changed, and why

| Imported behavior | Decision in version 4.0.0 | Reason |
| --- | --- | --- |
| Normal draws opened every shared room wall. Declared `chain` and `grid` controls did not produce different normal graphs. | Render actual chain, full grid, random spanning tree, sparse, and disconnected graphs. | A complete lattice makes room-graph distance indistinguishable from lattice Manhattan distance. Detours must change the answer to teach the role of doors. |
| Normal draws used one colored cell in each seeded room and distinct colors across those rooms. | Repeated effective seed colors and a larger extra color inside a seeded room occur in the default compound witness. Explicit repeated-color controls are supported. | Distinct colors hide the difference between counting nearest seed rooms and counting nearest colors. A single color per room hides the rule's minimum-color choice. |
| Dimensions and seed count were adjusted after their draws. Degenerate constructors could ignore other controls. | Draw only jointly feasible dimensions, honor accepted exact controls, and reject incompatible requests. | A recorded request must describe the emitted cells. Silent clipping prevents trustworthy probing and replay. |
| The old same-color special case placed its `7` cells inside room interiors. | Place each `7` on the shared separating wall of the two selected rooms. | The advertised three-room chain must exist in the parsed grid. The retained 4-by-10 counterexample checks this directly. |
| The validator performed shallow checks and returned success early for named degenerate textures. | Parse the grid's rooms and doorway incidences; apply the same geometry checks to every texture. | A texture name in metadata cannot establish validity. Lawful single-room, no-door, and repeated-color cases still remain available. |

The unchanged rule treats `1`, `7`, and `9` as walls when finding non-wall four-connected components. Each seeded room contributes its **smallest** nonzero non-wall color. Shortest-path distance counts doorway edges. Equally nearest seed rooms of one color produce that color; equally nearest **distinct colors** produce `8`. Walls and doors are preserved. The [actual canonical checks and counterexamples](checks/room-graph/final/report.json) exercise these distinctions.

Disconnected rooms require particular care. The authoritative program represents an unreachable distance as `999`; all global seed entries at that distance still compete. Thus an unreachable room takes the sole global effective seed color, or `8` if multiple global effective colors compete. Replacing that result with blank `0` would change the authority. The compound witness deliberately exposes this behavior.

## Sampling space and exact controls

The generator builds a rectangular lattice of rectangular rooms with a closed `1`/`9` border. Its sampled seed palette is `2..6`; input `8` is reserved as an output marker. Those are deliberate sampler and validator restrictions, not a claim to cover every input accepted by the Racket program.

| Control | Supported meaning |
| --- | --- |
| `n_room_rows`, `n_room_cols` | `1..3` room rows and `1..6` room columns |
| `room_h`, `room_w` | Uniform room interior dimensions, each `2..6` |
| `n_seeds` | `1..5` **seeded rooms**, not distinct colors or colored-cell count |
| `seed_colors` | One integer from `2..6` per seeded room; repeated values allowed; length must agree with an explicit `n_seeds` |
| `texture` | `chain`, `grid`, `tree`, `sparse`, `witness`, `canonical`, `explore`, `single_room`, `no_doors`, or `two_seeds_same_color` |
| `door_positions`, `seed_positions` | Only `random`; the deterministic context supplies the random stream |

Feasibility is checked jointly before drawing: `1 + n_room_rows * (room_h + 1) <= 30`, `1 + n_room_cols * (room_w + 1) <= 30`, and `n_seeds <= n_room_rows * n_room_cols`. Difficulty changes weights among feasible choices before the draw. It never resizes an already selected room. Unknown controls, scalar coercions such as booleans, invalid difficulty values, negative sample indices, and inconsistent or impossible requests fail explicitly. Dynamic incompatibility exceptions retain the requested axis names.

Fixed profiles also constrain controls. `witness` requires a 3-by-3 room lattice and three seeded rooms; it chooses its own repeated colors and larger in-room extra. `canonical` fixes two room rows, three columns, 3-by-3 interiors, three distinct seeded colors, and wall color `1`. It samples a grid, chain, or tree graph. It is a **canonical profile anchor**, not a replay of stored example grids. `single_room` requires one room and one seeded room; `two_seeds_same_color` requires two seeded rooms with the same color. Conflicting exact controls raise an error.

Any active explicit control without a texture selects the exploratory distribution. Explicitly selected textures likewise select their own authoring distributions. These calls remain useful for controlled examples, but they do not inherit the default lesson schedule. The [44 final joint-control checks](checks/room-graph/final/report.json) cover 36 valid combinations across all three difficulty bands and eight explicit incompatibility rejections. `observe_overrides` measures dimensions and seeded-room count from the returned grid, so those checks do not rely solely on draw metadata.

The validator checks rectangular nonempty integer grids within 30-by-30, excludes boolean colors and input `8`, requires a closed wall border and at least one seeded room, verifies that each non-wall component fills its bounding rectangle, and requires every `7` to touch exactly two distinct rooms. It does not demand that every sample teach every semantic distinction. That is the lesson sampler's job.

## The compound witness

The base witness uses nine rooms arranged in a 3-by-3 lattice. With row-major room IDs, doorway edges form the path `0, 1, 2, 5, 4, 3, 6, 7`; room `8` is isolated. Three seed rooms lie at path positions `0`, `2`, and `6`, with effective colors `a, a, b`. A second, larger color is added inside the first seed room, so its effective color remains `a`. The colors `a`, the extra color, and `b` are distinct. Random room sizes, palette choices, door positions, seed positions, and all eight dihedral orientations vary the cells while preserving these comparisons.

| Rival | Answer-changing cue in the witness |
| --- | --- |
| `seed_room_tie` | The room between the first two seeds is tied between two rooms of color `a`; its correct fill is `a`, not `8`. |
| `largest_seed_in_room` | The first seed room contains `a` and a larger color; the effective seed must be the minimum. |
| `ignore_doors` | The bent path creates distances different from those on a fully connected room lattice. |
| `minimum_color_tie` | A tie between distinct effective colors must produce `8`, not the smaller seed color. |
| `unreachable_zero` | The isolated room must follow the authority's global distance-`999` competition, producing `8` here. |

The [final probe](checks/room-graph/final/report.json) found eight distinct orientations by reading emitted cells, using seeds `0, 1, 2, 3, 4, 5, 10, 21`, sample index `0`, medium difficulty, and explicit `witness` / 2-by-2 interior controls. All five witness predicates were true in each case; all five rival predictions differed from actual pinned Racket output. The ordinary diagnostic prediction matched Racket in every case. This is executed evidence for the constructed witnesses, distinct from default-frequency evidence.

## Four-draw lessons and query positions

| Sample-index residue modulo 4 | Profile | Purpose |
| --- | --- | --- |
| 0 | `witness` | Expose all five declared semantic mistakes |
| 1 | `canonical` | Retain the canonical size, palette-role, and room-count profile |
| 2 | `witness` | Keep a visible witness when another pair becomes the query |
| 3 | `explore` | Vary geometry and topology beyond the compound witness |

Every four consecutive sample indices contain two compound witnesses. A lesson uses the first three accepted pairs as demonstrations and the fourth as its query. Holding out any one of the four pairs leaves at least one complete witness in the demonstrations. The rotation check holds out each labelled pair once and preserves the order of the other three. This derivation assumes the four accepted indices form that scheduled window; retained runner indices and materialization evidence are therefore necessary, rather than assuming rejected draws cannot affect assembly.

The [fixed-seed schedule census](checks/schedule-census-final.json) materialized all four starting residues at seed `0` in each of easy, medium, and hard: **12 production lessons, 48 query rotations, and 17 unique input grids**, with no ambiguity, materialization errors, or scoring errors. It enumerates the declared period `4`. The report's separate residue-reporting modulus `6` is not a different generator schedule. This census exhausts the declared starts at that seed and those bands; it does not exhaust every seed or possible rejection schedule.

The [larger final census](checks/lesson-census-final.json) materialized **300 production lessons**—100 per difficulty band—and checked **1,200 query rotations** over **1,198 unique input grids**, with no ambiguity or materialization/scoring errors. Its seeds follow the report's deterministic task/band/index hash recipe. Rotations reuse the materialized bundles rather than generating new draws. There are **five unique declared rivals**, exposed through 12 declaration bindings; the aliases are not 12 independent hypotheses. The two `CANONICAL_SHORTCUTS`, `seed_room_tie` and `largest_seed_in_room`, each fit all three labelled canonical pairs. Other declared rivals are useful competitors without claiming they fit all canonical pairs.

## Measured repair checks

| Retained evidence | Observed result on the repaired source |
| --- | --- |
| [Battery result](checks/after-final/result.json) | Exit `0`; all 12 stages green, including authority synchronization |
| [Canonical profile floor](checks/after-final/checks/1b2b9283b4ab_after_profile_floor.json) | 15/60 exact profile hits: easy 6, medium 5, hard 4; 31/60 within the canonical envelope; no canonical inputs rejected |
| [Semantic gate](checks/after-final/checks/1b2b9283b4ab_after_semantic_gate.json) | 600/600 strict-valid draws; 12/12 production lessons and 48/48 required query rotations without ambiguity |
| [Portable task tests](checks/task-tests/result.json) | JUnit total 248 passed, zero failures/errors/skips; this includes subtest entries and prototype tests |
| [Room-graph probe and run receipt](checks/room-graph/final-run.json) | Exit `0`; all three canonical pairs, eight observed witness orientations, 44 joint controls, and the exact same-color counterexample retained |

These are bounded checks of semantics, controls, and lesson assembly. They do not measure solver learning, downstream model accuracy, or generalization to every lawful room graph.

## Alternatives rejected and remaining restriction

- **Only add more random draws.** The original construction excluded important counterexamples by construction. More samples of distinct single-color seeds on a complete lattice would leave those rival rules viable.
- **Add one witness per four pairs.** That witness could become the held-out query. Two compound witnesses preserve visible evidence under each tested query position.
- **Force distinct seed colors everywhere.** This would avoid the counterexample while removing the exact semantic distinction the generator needs to teach.
- **Use the compound witness for every draw.** The canonical anchor and exploratory slot retain useful variation. Nevertheless, the adopted schedule still puts one compound topology in half the default draws. Palette, size, position, and symmetry variation do not remove that template restriction. Broader independently constructed witnesses would be a useful future extension; present results do not establish resistance to template memorization.
- **Silently clip controls or excuse degenerate textures in validation.** Both hide discrepancies between requested and emitted structure. Explicit infeasibility errors and cell-based validation make the contract inspectable.
- **Change unreachable-room behavior or use the Python model as the authority.** Both would obscure whether the repair matches the selected Racket rule. Actual Racket execution supplies labels; Python predictions remain diagnostic.

The exploratory sampler covers several graph families, but rectangular lattices, the bounded palette, uniform room interiors, and the finite rival set remain restrictions. The declared-rival census establishes separation from those named predictions on those lessons. It is not a proof of universal identifiability.

## Proposed parametric prototype: tie marker

**Assessment: suitable as a small proposed prototype, separate from canonical repair.** A bounded `tie_marker` parameter changes only the output color used for an equal-distance tie between distinct seed colors. The original/default setting is `8`; the alternative is `6`. The [task-local prototype and README](repo/generators/1b2b9283b4ab/workspace/parametric/README.md) leave the selected generator and canonical authority unchanged and introduce no production parametric API.

The parameter is chosen once per complete episode: even seeds select `8`, odd seeds select `6`. Inputs use only seed colors `2, 3, 4, 5`, so either marker remains distinct from seeded colors. The independent prototype sampler builds connected chains with two distinct-colored endpoint seeds; its four examples have 3, 5, 4, and 7 rooms. Three demonstrations and one query share the same materialized program. Three odd-length chains provide tie witnesses, so holding out any pair leaves at least two visible examples that distinguish the settings.

| Setting | Exact materialized program SHA-256 |
| --- | --- |
| Default `8` | `3e13418e96c93147e7c87ec55070352d783b241e00f140ef2509279bf340e71c` |
| Alternative `6` | `a03b3d18cfce3403ea1ea852de1aeb4acf918aee44e3c0847d161040b7dfe9c7` |

The default program is byte-identical to the canonical program. A pinned, guarded replacement materializes the alternative tie-fill expression. The exact programs are retained as [tie_marker_8.rkt](checks/parametric/final/tie_marker_8.rkt) and [tie_marker_6.rkt](checks/parametric/final/tie_marker_6.rkt). Labels come from their actual execution through the public Racket bridge. A task-local public-wrapper adapter handles this already valid Racket program; the README records why the generic helper's missing legacy import cannot be used in the authoring layout.

The [final prototype report](checks/parametric/final/report.json), [canonical checks](checks/parametric/final/canonical_default_checks.json), and [setting-difference witness](checks/parametric/final/setting_difference_witness.json) retain two settings, two complete episodes at seeds `0` and `1`, eight distinct inputs, 16/16 Racket label executions matching the independent chain oracle, 3/3 unchanged default canonical labels, 2/2 identifiable production lessons, and 8/8 identifiable query rotations against the other marker setting. The same-input comparison changes six output cells. The [focused prototype tests](checks/parametric/final-tests.json) pass all seven cases. The public [challenge_0001.json](checks/parametric/final/challenge_0001.json) and [challenge_0002.json](checks/parametric/final/challenge_0002.json) contain demonstrations and input-only queries; parameters and query answers are retained separately as authoring evidence.

The exact evidence command, run from `WORK/` with exit `0`, was:

```bash
python3 run_with_racket.py python3 generators/1b2b9283b4ab/workspace/parametric/prototype.py --seeds 0 1 --out ../checks/parametric/final
```

Use a fresh output directory for another execution. The prototype intentionally omits branching graphs, cycles, disconnections, and repeated-color seeds. Its lesson result concerns the two marker settings, not the five main-repair rivals or all plausible rules. It demonstrates that the parameter changes executed labels and can be inferred from visible examples; it does not approve the variant for production or widen the canonical generator's contract.
