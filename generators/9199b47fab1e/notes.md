# Working notes: 9199b47fab1e

## 2026-10-07 review-aae0bbad2bb6c284

Baseline version `2.0.1` advertised dead texture/degenerate controls, ignored
exact overrides, used small random bars that often did not affect labels, and
accepted most destructive validator mutations. The selected target Racket text
also differed from canonical by one comment despite behavioral parity.

The repair uses a zero moat around a closed wall frame plus eight deterministic
chamber profiles. It preserves the canonical BFS rule and pins normalized hash
`b0749d721740`. The selected `target_code` was text-synchronized to canonical;
no Racket behavior changed.

Declared rivals:

- `nearest_seed_manhattan_ignoring_walls`: killed by every generated input.
- `color_8_only_barrier`: fits all five labeled canonical pairs, but is killed
  by non-8 wall lessons. The wall-color schedule guarantees two non-8 examples
  per three consecutive samples, so ordered lessons and all one-pair query
  rotations remain identifiable.

Retained probes and tests live in `workspace/reference_probe.py` and `tests/`.
Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `4a7acdbf7f6e9e36969e843b410bbb746252739953a686634f42e8983fd8cac6`.

# Decisions for `9199b47fab1e`

## D1 — Preserve the selected rule; repair sampling and teaching

**Choice.** Keep the canonical multi-source cardinal BFS exactly as selected:
only colors 0 and 2 are traversable, reachable cells become 3/4/5 by distance
modulo three, and every other color is preserved as a wall.

**Why.** The baseline Racket rule reproduced all five labeled canonical pairs.
The failure was the generator's input manifold and lesson evidence, not its
labels. Rewriting the rule to match the old random-bar distribution would have
changed the task rather than repaired it.

**Authority change.** The duplicate selected `target_code` contained one comment
that canonical text did not. Removing that comment made exact authority sync
green; normalized rule hash and behavior remained `b0749d721740`.

## D2 — Use closed chambers instead of independent short bars

**Choice.** Surround a seeded interior with a closed wall frame and a seedless
zero moat, then optionally add one of eight internal profiles: box, vertical or
horizontal split, cross, nested box, gated split, double split, or staggered
walls.

**Why.** A closed barrier guarantees that wall blocking changes the output:
interior cells are reached and recolored while exterior zeros remain unchanged.
The profiles add topology without weakening that invariant and better match the
canonical chamber morphology than tiny random segments.

**Alternatives rejected.** More random bars still permit bypasses and redundant
walls. Fixed replay templates would be easy to validate but would collapse input
diversity. Fully random cellular mazes were unnecessary for this single static
rule and would make exact overrides less predictable.

## D3 — Expose only three truthful controls

**Choice.** Advertise `shape`, `n_seeds`, and `wall_color`; reject unknown keys,
wrong types, booleans masquerading as integers, and out-of-domain values.

**Why.** Each value is recoverable from pixels through `observe_overrides`.
Baseline texture and degenerate names either did nothing or deliberately left the
ordinary rule domain, and therefore should not be production axes.

**Measured result.** The final override gate is green across all difficulty
bands and complete axis combinations. Nine shapes, all seed counts 1–3, and all
wall colors 6/7/8/9 appeared in every 128-draw independent band census.

## D4 — Keep canonical dimensions common without making the domain fictional

**Choice.** Use nine legal shapes from 9×9 through 18×20. Difficulty changes the
weight placed on five canonical-scale shapes, while every shape remains legal
and has nonzero default support in every band.

**Why.** Canonical support and broad diversity are both useful. A
canonical-only sampler would make the declared broad shape domain misleading;
a uniform broad sampler would weaken profile-floor support.

**Limitation.** Difficulty is a distributional bias, not a different semantic
rule or a disjoint range.

## D5 — Make the canonical color shortcut explicit

**Choice.** Add `color_8_only_barrier` to `CANONICAL_SHORTCUTS`,
`SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`.

**Why.** Every canonical pair uses color 8 as the barrier, so the wrong program
“only 8 blocks; every other color is traversable” fits `5/5` public labels. The
weaker wall-ignoring Manhattan rival alone was not enough to establish the
meaning of non-8 colors.

**Probe.** `checks/shortcut-color8/counterexample.json` retains an exact emitted
9×9 color-6 chamber. The supported Racket rule preserves the color-6 barrier and
recolors only the seeded chamber; the rival recolors through the barrier and
differs at 76 cells.

## D6 — Schedule wall colors for lesson-level, not merely sample-level, teaching

**Choice.** Use the repeating wall-color curriculum `8, non-8, non-8` over
consecutive sample indices. The non-8 colors rotate among 6, 7, and 9.

**Why.** Three demonstrations then always include two direct counterexamples to
the canonical-fitting color-8 shortcut. In a four-pair lesson, holding out any
one pair still leaves at least one non-8 demonstration.

**Alternatives rejected.** IID wall-color sampling gives good aggregate
frequency but can produce all-8 lessons. Always using a non-8 wall refutes the
shortcut but abandons canonical color support. Alternating 8/non-8 is adequate
for ordered lessons but less robust under arbitrary hold-one-out queries than
the chosen three-slot schedule.

**Measured result.** The final public census found no ambiguity in `300/300`
ordered lessons or `1,200/1,200` query rotations. The independent probe found no
surviving declared rival in 400 windows or 1,600 rotations.

## D7 — Validate semantic structure, not just syntax

**Choice.** `self_check` requires a canonical-scale shape, 1–3 seeds, exactly one
wall color in 6–9, substantial connected wall support, at least one seeded open
component, and a meaningful seedless open component.

**Why.** Those conditions make the key distinction observable. The baseline
validator could accept grids whose walls did not separate anything and missed
many destructive mutations.

**Probe/failure mode.** All five canonical inputs and all 512 independent final
draws pass. The validator intentionally does not prove a unique intended program;
that is why rival and lesson contracts remain separate.

## D8 — Separate authority, mirror, and independent evidence

**Choice.** Retain three levels of checking:

1. selected Racket execution as label authority;
2. a task-local `rule_mirror` for fast executable contracts and tests;
3. `workspace/reference_probe.py`, which independently reimplements BFS,
   inspects declarations dynamically, and batch-checks Racket parity.

**Why.** A mirror alone can share a bug with the generator. Independent code plus
Racket parity makes the fast tests useful without pretending Python is authority.

**Measured result.** The independent probe matched Racket on 29/29 canonical and
generated inputs. Focused tests passed 57/57 and the shared battery passed 12/12.

## D9 — Preserve failed iterations and source binding

The initial TDD run failed 43 tests and passed 9; after the first repair it passed
52/52. A later self-review discovered the color-8-only shortcut, added six
failing regressions, and ended at 57/57. An initial portable helper also failed
because the staged runtime mirrored authority under two roots; the helper now
prefers `shared/data` and falls back only when needed. These records remain under
`checks/tdd-red*`, `checks/tdd-green-color8`, and `checks/task-tests*`.

No generator change was made after the final exposed solve was prepared and
finished. Final source binding is SHA-256
`4a7acdbf7f6e9e36969e843b410bbb746252739953a686634f42e8983fd8cac6`.

## Domain limits

The tests establish canonical parity, deterministic generation, exact declared
overrides, validator behavior, the named rivals, and the measured lesson policy.
They do not enumerate every conceivable shortcut, prove identifiability in the
program-synthesis sense, or guarantee the same wall-color coverage if an
external caller discards or reorders generated pairs outside the documented
lesson assembly.

## D10 — Add a native `source_mode` family with a real relay dependency

**Choice.** Keep the exact canonical program as `source_mode=original_seeds` and
add `source_mode=farthest_relay`.  The alternative first runs the canonical
wall-aware multi-source BFS, selects the row-major first reachable cell at the
maximum primary distance, and then runs a second wall-aware BFS from that relay.
The second distance field, not the original one, determines the 3/4/5 coloring.

**Why.** This preserves the source task's topology and barrier reasoning while
adding an input-dependent A→intermediate→B dependency: B's source cannot be
chosen until A has computed the obstacle-aware primary distance map.  It is not
a palette-only or collapsing remap variant.

**Episode contract.** The adapter supports 2–6 demonstrations and 1–4 queries,
uses matched inputs across settings, retains four controller-side novel queries,
and keeps public projection prefix-stable: the first revealed query is identical
for one-query and four-query use.  The fixed query set includes a substantive
30×30 labyrinth.  Private settings, programs, and query answers stay out of the
public challenge.

**Bounded evidence.** `workspace/parametric/evidence/current/prequalification.json`
checks 96 episodes / 736 pairs across seeds 0–15, demo counts 2/3/6, matching
settings, constructive teaching, query-prefix stability, and 96 substantive
30×30 queries.  Native qualification passed all four jobs (two settings × seeds
0 and 17) with protected Racket labels.  The finite self-audit tested five
plausible rivals per setting over the qualified episodes and found no surviving
or query-ambiguous rival.  The causal witness changes only the intermediate from
the farthest relay `(2,2)` at primary distance 15 to the first original seed;
the same qualified input then produces a different protected-Racket output.

**Handoff limit.** Status is reviewer `ready`, not owner accepted.  Exact-source
owner qualification/acceptance and any training admission remain pending.  The
finite rival audit and one causal witness do not prove universal identifiability
or algorithmic depth.
