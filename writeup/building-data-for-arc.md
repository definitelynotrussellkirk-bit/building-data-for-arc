# Building data for ARC

## How the data was made

A synthetic ARC task is useful only if its label is right and its
demonstrations determine that label. Volume fixes neither: a wrong rule or an
ambiguous lesson teaches the wrong thing however often it is sampled. ARCpuzzles
is built around that constraint. It holds 4,061 generators, of which 1,984 are
currently approved for training.

| Source | Generators |
|---|---:|
| ARC-AGI-2 training tasks | 1,000 |
| ARC-AGI-2 public evaluation tasks | 120 |
| Puzzle bank (Claude and GPT Pro, author-seeded) | 2,859 |
| Custom | 30 |
| Untagged (49 generic concept generators, 3 per-puzzle) | 52 |

Every generator went through the same path:

1. **Rule.** A reference rule is written in a constrained Racket DSL. It is the
   only source of output labels.
2. **Generator.** A Python sampler is written against a shared runtime. It
   states the rule, its sampling axes and its invariants, and optionally
   declares textures that teach or hide the rule, rival rules and a lesson check.
3. **Battery.** Twelve automatic checks run on the generator and rule together.
4. **Review.** A reviewer receives a packet for the generator, attacks it,
   repairs it or extends it, and returns the change with evidence.
5. **Approval.** An accepted review is recorded against the exact generator and
   rule hashes. Any later edit revokes approval.
6. **Export.** Only approved generators are sampled for training, with answers
   kept apart from the model-visible challenges.

Puzzle banks were written outside the repository by Claude and GPT Pro, the
models available at the time, seeded with the author's own puzzle ideas, as
21-puzzle bundles, and imported from 16 April. The first generators were
written the same way. Later generators were written and repaired by coding
agents under the author's direction; the July review records Codex, Kimi and
OpenAI models as reviewers, and the October reviews were done by Claude and
GPT Pro.

## What a generator does

A generator draws fresh tasks for one ARC rule, as many as its input space
allows; for the six measured below it ranges from 2,376 grids to billions. It has
two halves:

1. A Python sampler, `generate(seed, sample_index, difficulty, **overrides)`,
   returns one input grid.
2. A Racket reference rule computes the output. The sampler never writes
   outputs, so a sampler bug can produce a poor input but never a wrong label.

`arcpuzzles generate` draws inputs at successive sample indices, drops any that
fail the generator's `self_check`, labels the rest with the Racket rule, and
assembles demonstrations and held-out queries into an episode. Each episode
records the executed rule hash, the hash of every input, and its lesson check.

Generator `0005ab5b7704` ("Marked Column Compression"): yellow cells in row 0
mark columns, and the output keeps only those columns of the remaining rows.
This is its complete reference rule:

```racket
(rule!
 ;; Keep only the COLUMNS whose header (row 0) is yellow(4); header dropped.
 (let ((keep (filter (lambda (c) (= (at g 0 c) 4)) (range 0 w))))
   (for/list ((r (in-range 1 h)))
     (for/list ((c (in-list keep))) (at g r c)))))
```

One demonstration it generated (seed 17):

```
input     output
0004040
0003708   30
6080393   09
6005790   59
0002002   20
0060500   00
0000270   07
8070000   00
```

## Sampling: one shared runtime and keyed draws

All generators share one runtime (`shared/runtime/puzzle_generators/`) rather
than each carrying its own random-number and grid code.

- **Keyed draws.** Every random choice goes through a named draw such as
  `ctx.draw_int("grid_h", 6, 8)`. The name is hashed with the seed, sample index,
  generator version and task ID to seed an independent random stream. The same
  arguments always give the same grid, and adding, removing or reordering one
  draw cannot change any other. Bare `random` calls are forbidden.
- **Overrides.** Any named axis can be pinned by the caller, and the pinned value
  passes the same validity check as a random one. The override checker probes
  every declared axis at its boundaries and in combination.
- **Axis honesty.** Each draw records the bounds it actually used. The defect
  linter compares those bounds with the declared axes, so a generator cannot
  claim a range it never samples.
- **Difficulty.** `easy`, `medium` and `hard` select bands within each axis's
  range, so a curriculum changes scale without changing the rule.
- **Shared helpers.** Grid, placement, palette, object, shape, panel, room,
  lattice and texture helpers are shared, so a fix to a placement bug reaches
  every generator that uses it.
- **Rejected attempts are logged.** The runner records every rejected pair with
  a phase-prefixed reason, and drops duplicate and identity pairs.

## Textures: making the rule visible

A texture is a named kind of input a generator can draw, such as sparse
objects, stripes or a full grid. A generator can declare *helpful* textures,
which make the rule visible, and *degenerate* textures, which hide it.
Degenerate textures are reachable only by explicit override and never on the
default path; the self-check stage fails a generator if one leaks into ordinary
output. Declaring textures is optional: of the 1,984 approved generators, 264
name helpful textures and 255 name degenerate ones (459 distinct names).
Counting texture sampling axes and lawful degenerate textures as well, 347
declare textures in some form. Across the whole library, 1,881 generators name degenerate
textures.

| Helpful (shared library examples) | Degenerate (most declared) |
|---|---|
| noise, sparse, blob, stripes, gradient | `full_grid` (356 generators) |
| checkerboard, frame, ring, plus | `no_markers` (101), `no_seeds` (77) |
| task-specific palettes: warm, cool, varied | `no_pairs` (73), `no_blobs` (73), `no_objects` (69) |
| | `single_motif` (53), `all_same_color` (52), `monochrome` (38) |

In `0005ab5b7704`, the invariants require content in both kept and dropped
columns, so keep-versus-drop shows in every output; `no_markers`,
`all_columns_marked` and `no_body` are its degenerate textures.

## Rival rules: attacking the rule

A generator can declare rival rules: plausible alternatives a solver might infer
instead of the real one. The semantic gate checks that the generated lessons
eliminate them.

- `SEMANTIC_RIVALS`: named alternative rules, each a function from grid to grid.
- `SEMANTIC_WITNESSES` and `WITNESS_RIVALS`: input features, each tied to the
  rivals it must refute. Whenever an input has a witness feature, at least one
  of the rivals tied to it must give a different output from the reference
  rule on that input.
- `lesson_identifiable`: rejects a lesson in which a rival fits every
  demonstration but changes the query answer, when export chooses the
  demonstration count; with a fixed count the lesson is kept and flagged.
- `CANONICAL_SHORTCUTS`: rivals declared to fit the original ARC task's own pairs.
  Each needs generated counterexamples. Since 23 October the gate also checks
  that declared fit; some generators approved earlier fail it.

1,498 generators declare 6,822 rivals, a median of 4 and up to 25 per generator,
under 5,085 distinct names. Most rivals are written for one task; the common ones
are `identity` (175 generators), `horizontal_only` (42), `vertical_only` (38),
`solid_bbox` (19), `largest_component_only` (15) and `ignore_blockers` (14).

Generator `00ed2544a15e` fills the cells between two red cells with cyan when
nothing else lies between them. Its seed-17 episode passed its lesson check with
every rival contradicted by at least one of the three demonstrations:

| Rival rule | Result |
|---|---|
| identity | refuted |
| horizontal pairs only | refuted |
| vertical pairs only | refuted |
| ignore blocking colours (also fits the original task) | refuted |
| simple pairs only (also fits the original task) | refuted |

These checks are sampled evidence against named alternatives, not proof that no
other rule fits.

## Templates: parametric Racket rules

941 generators have an accepted parametric family: one input sampler shared by
several rule settings, each with its own Racket program. All pairs in an episode
use one setting, and the demonstrations must tell the settings apart and refute
the family's declared shortcuts.

`0005ab5b7704` adds a setting that orders the selected columns by how many
non-black body cells they hold:

```racket
(rule!
 ;; Stage A selects only header-marked columns and measures their body occupancy.
 (let ((keep (filter (lambda (c) (= (at g 0 c) 4)) (range 0 w))))
   (define (body-count c)
     (length (filter (lambda (r) (not (= (at g r c) 0))) (range 1 h))))
   ;; Stage B orders that selected-and-measured intermediate, then packs the body.
   (let ((ordered (sort keep (lambda (a b)
                               (let ((ca (body-count a)) (cb (body-count b)))
                                 (or (> ca cb) (and (= ca cb) (< a b))))))))
     (for/list ((r (in-range 1 h)))
       (for/list ((c (in-list ordered))) (at g r c))))))
```

The family also keeps an adversarial rule, `wrong_intermediate.rkt`, that ranks
every column before selecting the marked ones. To refute it, the sampler gives
the marked columns distinct densities, forces an order that differs from left to
right, and always adds a dense unmarked column. A 32-seed audit and a 256-seed
sweep found no surviving declared shortcut.

| Family | Settings | Lesson requirement |
|---|---|---|
| `57bafcdde8c3` recolour components by size | `min_size` 2, 3, 4 × connectivity 4, 8 | Distinguish all six settings and five shortcuts; queries up to 30×30 |
| `7b0cb3b9a618` crossing bands | front or back band | Reject eight declared shortcuts under both settings |
| `581bb11ff645` rank by holes | count cells or regions × ascending or descending | First demonstration separates every setting |
| `0005ab5b7704` marked columns | left to right or by density | Refute ranking all columns before selection |

## Matching the original task

Generated inputs must cover the task they imitate. A distribution gate compares
object count, component size, palette size and area with the original
demonstrations. A profile floor fails a generator if no generated grid matches
any original (height, width, palette) profile, or if its `self_check` rejects an
original input.

## The check battery

The twelve stages cover structure (`lint`, `override`, `racket_lint`,
`grammar`), execution (`selfcheck`, `rule_smoke`), distribution (`dist_gate`,
`profile_floor`, `diversity`) and semantics (`semantic_gate`, `defect_lint`,
`authority_sync`). Each began as a defect reviewers found by hand:

| Defect found in review | Check that now catches it |
|---|---|
| Generated median object count 12 against the original's 2 | `dist_gate` |
| 0% of generated grids match any original grid profile | `profile_floor` |
| Passed 120 of 120 execution runs while teaching the wrong key-to-direction mapping | `semantic_gate` |
| Ordinary draws that were identity transforms | `semantic_gate` |
| Gold program calls a helper the constrained grammar rejects | `grammar` |
| Generator crashes or emits constant outputs yet passes lint | `rule_smoke`, `selfcheck` |

## Review and approval

Reviewers receive packets for assigned generators and return repairs,
extensions and evidence, which are integrated against the source hashes they
were assigned. 569 integrated review records are retained for 486 generators;
older processed returns were compacted after their content was integrated.

| Review outcome | Records |
|---|---:|
| Accepted repair | 201 |
| Accepted new prototype | 291 |
| Needs more evidence | 69 |
| Blocked, deferred or other | 8 |

568 of the 569 report reviewer-run results that were not re-run at intake.
Approval requires a `reviewed_safe` label recorded against the current generator
and rule hashes: 56 generators are unapproved because their code changed after
review, and 15 because their rule did. Current labels: 1,994 reviewed safe, 584
provisionally safe, 1,007 unverified and 415 unsafe.

## Exporting training data

`arcpuzzles export` samples only approved generators by default, either in
proportion to each generator's mix weight or uniformly. Seeds and the full pool
are recorded. An episode can carry four supervised queries over one shared set of
demonstrations, all under the same rule and setting. Query answers are written to
private files and never to the model-visible challenge file. Each row records the
generator hash and its verified original-task family, or marks the family as
unknown; no train/evaluation split is invented.

TODO: state whether the 120 public-evaluation generators were excluded from
training for any reported score.
