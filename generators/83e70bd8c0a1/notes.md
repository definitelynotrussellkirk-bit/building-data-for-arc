# Working notes: 83e70bd8c0a1

## Review-16f4747de86c964a

The selected `2.0.1` baseline did not pin `RULE_HASH`; advertised `grid_h`,
`grid_w`, `palette_kind`, `anchor_corner`, `asymmetry_force`, `palette_size`,
and `texture` controls were dead, aliases, or capable of producing inputs
outside the stated task; and `self_check()` accepted all 59 destructive
mutations used by the defect probe. A 60-draw profile check produced only one
canonical-size/palette hit and none in easy or hard. No prior return supplied a
usable lead: `evidence/associated_notes.jsonl` was empty, so all findings were
remeasured against the pinned baseline.

Version `3.0.0` keeps the canonical Racket rule unchanged and rebuilds the
sampler around four observable semantic controls. Each draw contains fixed
anti-diagonal cells, occupied mirror pairs, singleton orbits, a corner witness,
and a repeated moving color while retaining exactly six foreground colors.
This supports the canonical 5×5/6×6 seven-color profiles and gives executable
witnesses against five plausible rivals. `strict_canonical_like()` deliberately
matches `self_check()` because the owned manifold now includes all canonical
inputs.

Final generator SHA-256:
`271ba6e1f2d47e5f992b277033d290de1bcff93d506bf82b1373b3945e3d64f7`.
The hash-bound after battery is 12/12 green. The shared 300-lesson census
(100 per band, three demonstrations plus one query) materialized 1,200 unique
inputs with zero declared-rival ambiguity, warnings, or scoring errors. The
additional task-local probe checked all 1,200 cyclic query placements and every
boundary override combination with zero failures. These are finite declared-
rival tests, not a proof that no other induction shortcut exists.

The reusable probe is `workspace/qualify_distribution.py`; it reads the
sampler's live rival/witness declarations rather than duplicating their names.
## Current reviewer considerations

Source SHA-256: `271ba6e1f2d47e5f992b277033d290de1bcff93d506bf82b1373b3945e3d64f7`.

# Decisions for 83e70bd8c0a1

## D1 — Keep the Racket authority unchanged

**Choice.** Retain the canonical rule `(rotate-180 (transpose g))` and pin
`RULE_HASH = "ea62a41435bf"`.

**Rationale.** The canonical examples, independent Python transform, rule-smoke,
and authority-sync checks all agree on full anti-diagonal reflection. The defect
was in the sampler and contract, not the transform.

**Alternatives rejected.** Editing canonical data or the Racket program would
add authority risk without repairing lesson identifiability. Implementing output
logic inside the generator would also duplicate authority rather than improve
inputs.

**Probe/failure mode.** Canonical-pair tests and the Racket rule-smoke compare the
independent Python mirror with authoritative outputs. A source change with a
stale pin fails lint/authority checks.

**Limitation.** Equality on tested inputs is not a formal proof of the Racket
runtime, but the selected rule is a simple total transform and the authority is
hash-bound.

## D2 — Replace decorative axes with four observable semantic controls

**Choice.** Advertise only `grid_size`, `diagonal_marks`, `mirror_pairs`, and
`singletons`, each with an exact legal range and `observe_overrides()` recovery.

**Original rationale.** Unknown. The imported `2.0.1` source listed eight axes,
but several were never read and `texture` could escape the documented domain.

**Alternatives considered.** I could have retained names such as `grid_h` and
`grid_w`, but square grids make them redundant and permit incompatible requests.
I could have kept `palette_kind`, but color-family labels are not semantic to the
rule and do not improve identifiability. I could have kept degenerate textures,
but empty/full/single-mark examples are low-value or unlawful training data.

**Probe/failure mode.** Task tests enumerate every min/max control combination in
every difficulty band and compare requested values with `observe_overrides()`;
invalid keys, types, values, and difficulties must raise. The shared override
gate also passes.

**Limitation.** Difficulty-aware defaults expose only four joint combinations per
band in the pinned 400-item probe; exact overrides cover the complete boundary
cartesian product. This is deliberate curriculum shaping, not uniform sampling.

## D3 — Preserve canonical palette structure while adding semantic witnesses

**Choice.** Draw exactly six foreground colors and assign them across 1–3 fixed
points, 1–2 occupied mirror pairs, and 4–5 singleton orbits. Reserve `(0,0)` as a
singleton and repeat one color on a moving singleton.

**Rationale.** The canonical examples use six nonzero colors plus background, so
this raises profile support while ensuring each individual input distinguishes
important rival rules. The corner singleton separates anti-diagonal from
main-diagonal reflection. Differently colored occupied pairs expose what happens
when both mirror locations are occupied. Repeated moving colors defeat the only
plausible shortcut that fits every canonical pair: reflect only colors occurring
once.

**Alternatives rejected.** Pure random sparse marks reproduced the baseline's
poor profile support and often omitted fixed points, collisions, or repeats.
Forcing only one witness per lesson was rejected because cyclic query placement
could hide it in the query. Dense textures were rejected as unlike the canonical
sparse domain and liable to make copy/collision behavior harder to read.

**Probe/failure mode.** `WITNESSES`, `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS` are executable. The 300-lesson
Racket census and 1,200 cyclic task-local rotations report no surviving declared
rival.

**Limitation.** Mandatory witnesses narrow the training manifold. The validator
still accepts every canonical input, and actual draws span 5×5, 6×6, and 7×7,
but this generator is optimized for teaching the rule rather than representing
every lawful sparse grid.

## D4 — Make strict profile equal to the owned lawful manifold

**Choice.** `strict_canonical_like()` delegates to `self_check()` and
`MIN_STRICT_FRAC = 1.0`.

**Rationale.** Once the sampler was redesigned around a six-color canonical-like
manifold, a weaker strict predicate would conceal defects and a narrower one
would reject canonical examples or legal override combinations.

**Alternatives rejected.** A size-only strict check would repeat the baseline's
false confidence. Requiring exactly the three canonical cell counts would make
some useful occupied-pair/singleton combinations impossible.

**Probe/failure mode.** The profile floor reports 45/60 exact canonical
size/palette hits with support in all bands, while self-check rejects structural
impostors such as wrong palette cardinality, missing singleton support, excessive
pairs, invalid colors, and malformed shapes.

**Limitation.** The shared profile metric observes size and palette cardinality,
not full structural similarity; task tests cover the latter.

## D5 — Use a pure independent Python mirror only for diagnostics

**Choice.** Add `rule_mirror()` as a pure implementation of the anti-diagonal
mapping for tests and task-local probes; continue to use Racket as the source of
authoritative outputs in the shared census.

**Rationale.** A local pure function makes rival and cyclic checks cheap and
clear, while the Racket census prevents a shared implementation error from
silently redefining the task.

**Alternatives rejected.** Calling Racket for every cyclic permutation would be
more expensive without increasing coverage of the lesson-position question.
Using private runner functions was forbidden and would make the probe brittle.

**Probe/failure mode.** Canonical tests and rule-smoke compare the Python mirror
to the authoritative rule. The qualifier explicitly records this division of
responsibility.

**Limitation.** The cyclic probe inherits any bug shared by `rule_mirror()` and
its test oracle; canonical/Racket parity reduces, but cannot mathematically
eliminate, that risk.

## D6 — Add 19 task-local tests with retained red/green evidence

**Choice.** Put new tests only under the permitted task `tests/` directory and
cover source pins, canonical behavior, determinism, purity, controls, validation,
semantic rivals, cyclic lessons, and structural rejection.

**Rationale.** The root frozen fixture is not patchable and the general battery
does not automatically discover task tests. Test-first failures were retained:
`checks/tdd-red1/` caught the missing pin and `checks/tdd-red2b/` caught the
missing strict-profile contract before implementation.

**Alternatives rejected.** Editing the frozen fixture, relying only on smoke
checks, or adding post-hoc tests that never failed would provide weaker evidence.

**Limitation.** Nineteen deterministic tests do not exhaust the random state
space; the census and 1,200-item qualifier add distribution-level coverage.

## D7 — Add a cyclic-query qualification tool

**Choice.** Build `workspace/qualify_distribution.py` and test every one of the
four items in each generated lesson as the query, using the live declarations in
the generator.

**Rationale.** The shared census explicitly documents that it does not rotate
every pair into the query position. A witness that occurs only in the held-out
item can make the demonstrations underidentify the rule.

**Alternatives rejected.** Checking only aggregate witness frequency was rejected
because it says nothing about every complete lesson. Copying rival names into the
probe was rejected because declarations would drift.

**Probe/failure mode.** The final run checked 100 lessons per band × four query
positions = 1,200 rotations with zero failures, and also recorded profile and
joint-axis support.

**Limitation.** Only declared rivals are tested. `QUESTION_ANSWER.md` recommends
promoting this method into a shared gate and gives an audit case it would catch.

## D8 — Preserve interrupted aggregate evidence rather than rewriting it

**Choice.** Keep `checks/after/result.json` marked `running` after the foreground
transport ended, then finish the exact same hash-bound runtime through the
battery's documented checkpoint interface and retain its 12/12 summary.

**Rationale.** Rewriting the controller result would fabricate evidence. The
stage receipts contain source and authority hashes and are the correct record of
what completed.

**Alternative rejected.** Starting over repeatedly under the same transport cap
would waste work and could create multiple hard-to-match runtimes.

**Limitation.** Maintainers must read the resumed summary rather than interpreting
the interrupted wrapper record as the final aggregate. `RESULTS.json` states this
explicitly.

## 2026-10-24 native parametric review — anti-diagonal probe relay

Retained a two-setting, matched-input family under
`workspace/parametric/`. `full_reflection` is the byte-exact selected canonical
Racket program. `probe_relay` moves the unique blue probe by that same
anti-diagonal coordinate map, reads the unique landing cue, and transposes only
that input-selected cue color's remote payload. The production generator and
canonical authority remain unchanged.

The alternative's real dependency is: **A** move the probe; **intermediate**
read the landing-cue color; **B** transpose that color's payload. The protected
wrong-intermediate witness uses qualified seed 0, query 0: the landing cue is
color 2 while the source cue is color 3. Reading before A transforms the wrong
payload and changes 10 final cells. Evidence is retained in
`checks/83e70bd8c0a1/causal/`.

The adapter supports 2–6 demonstrations and 1–4 prefix-stable queries with
matched inputs. Query sizes are 10, 15, 22, and 30; the 30×30 case has boundary
anchors, all-quadrant content, and at least 90 occupied cells. The first two
constructive demonstrations reject the two admitted rules and declared
identity/transform/probe/fixed-color/source-cue/recolor shortcuts.

Fresh checks: 31 focused tests, 50 complete task tests, a 64-seed finite audit
covering 384 episodes / 2,944 labeled pairs / 640 unique inputs, 48 protected-
Racket audit evaluations, and eight one-query public projections. Native
qualification passed 2 settings × 2 seeds with 40 protected-Racket evaluations.
Manifest SHA-256 is
`046b3cd7614ae3481f2b99e8add6ab202c1ee4a62e17c2bbcddf6914131bab89`.
This is reviewer-ready and owner-pending, not accepted or training-admitted;
finite rivals do not prove universal identifiability.
