# Working notes: b4d9320e0d9d

## 2026-10-06 review repair

Baseline generator SHA-256:
`f6a2bfae7e866b4d96972550e0e8397ddb93f3d1801aa8bde91eb447f77c7440`.
Final generator SHA-256:
`b2bd90b14c66887139bac83196d9f66f7805a99147e3353659bc424726fddf39`.

The baseline generated only positive diagonal pairs and therefore could not
refute three rules that fit all three canonical pairs:

1. fill whichever opposite corner is empty even when the other is occupied;
2. ignore equality of the two diagonal colours; and
3. complete same-colour orthogonal pairs as well as legal diagonals.

It also advertised a broad, partly dead axis surface, accepted unknown override
keys, omitted `RULE_HASH`, and did not provide an executable semantic contract.
The retained before battery records 7 green, 2 advisory, and 3 failed stages.

The repair reduced the public axes to `grid_h`, `grid_w`, and `n_pairs`, made all
joint combinations constructive and observable, rejected unknown/type/range
errors, pinned the canonical authority hash, and added a complete teaching
scene plus executable witnesses/rivals. A sparse 1-in-20 calibration slot was
added after defect-lint showed that an all-teaching sampler was systematically
denser than the canonical examples. Band-specific keyed geometry avoids a dead
difficulty control while leaving rule semantics unchanged.

Final evidence:

- 12/12 after-battery stages green;
- 53/53 portable task-local tests pass;
- strict semantic gate: 600/600 lawful, 3/3 canonical accepted, 0/48 ambiguous
  required query rotations;
- lesson census: 300/300 lessons, 1,200 pairs, 1,200 held-out rotations,
  0 production ambiguities, 0 rotation ambiguities, 1,159 unique inputs;
- fresh final-source solve: 3/3 visible examples in one revision.

Limitations: the rival set is finite, so these checks do not prove unique
induction against every imaginable hypothesis. The teaching template is more
structured than arbitrary legal scenes, though transforms, offsets, palettes,
bands, four size profiles, and sparse canonical rows provide controlled
variation. No canonical Racket rule or canonical example was changed.
## Current reviewer considerations

Source SHA-256: `b2bd90b14c66887139bac83196d9f66f7805a99147e3353659bc424726fddf39`.

# Decisions — b4d9320e0d9d

## D1 — Reduce the public axis surface to observable controls

**Original rationale:** unknown. The imported generator advertised dimensions,
palette, position, distinct-colour, density, and texture controls, but several
were aliases, singleton domains, dead, or much broader than the implemented
sampler.

**Choice:** retain only `grid_h`, `grid_w`, and `n_pairs`; reject unknown keys,
non-integer values (including booleans), out-of-range values, and unknown
difficulty labels. Add `observe_overrides` and construct every joint combination
instead of relying on rejection sampling.

**Alternatives rejected:** keeping decorative axes as “diagnostic” would preserve
API breadth but not useful controllability; expanding all advertised spans would
move far outside canonical scale. The chosen surface is smaller but falsifiable.

**Probe/failure mode:** the before override gate accepted unknown keys and emitted
more than 22,000 direct findings plus tens of thousands of multi-axis legacy
rejections. The final override gate and all 24 dimension/pair combinations pass.

## D2 — Use a four-slot profile schedule

**Choice:** cycle through 7×7/2-pair, 8×8/2-pair, 9×9/3-pair, and 9×10/3-pair
profiles. Reuse exactly `n_pairs` nonzero colours, yielding palette sizes 3, 3,
4, and 4 including background.

**Rationale:** the first three match canonical size/palette/component profiles;
the fourth exercises the declared width endpoint. Cycling guarantees coverage
without hoping random samples hit every endpoint.

**Alternative rejected:** independent uniform draws give broader mixtures but
weaker per-lesson guarantees and made profile-floor coverage probabilistic.

**Limitation:** schedule position is predictable. Tests verify that this does not
resolve the task or let any declared competitor survive a query rotation.

## D3 — Teach exact preconditions with lawful near-misses

**Choice:** ordinary rows contain legal main- and anti-diagonal pairs plus:

1. a same-colour diagonal with exactly one occupied opposite corner;
2. a diagonal with two different nonzero colours; and
3. a same-colour orthogonal pair.

**Rationale:** all three corresponding overgeneralizations fit every canonical
pair, because the canonical set contains positive cases only. These negatives
are therefore necessary teaching evidence, not arbitrary decoration.

**Alternatives rejected:** more positive examples cannot distinguish these
rivals; malformed/degenerate inputs would test robustness rather than the rule.

**Failure modes checked:** accidental triggers between nearby motifs, overwrite
behavior, one-orientation-only rules, rival mutation, and cascade semantics.
Constructive spacing plus exhaustive focused tests keep these isolated.

## D4 — Add sparse canonical-scale calibration at 1 in 20 indices

**Choice:** `sample_index % 20 == 4` emits only the legal pairs; the other 19
indices emit the complete teaching scene.

**Rationale:** an intermediate all-teaching sampler was consistently denser than
the canonical examples. The sparse slot restores canonical component scale while
keeping any four consecutive examples at least 3/4 fully diagnostic.

**Alternatives rejected:** making every row sparse recreates the original lesson
ambiguity; random sparse selection weakens deterministic lesson guarantees.

**Measured result:** final semantic sampling had all three near-misses in
578/600 inputs and both orientations in 600/600. All 1,200 census rotations were
identified against the declared competitors.

## D5 — Vary geometry without changing semantics

**Choice:** apply one of eight transpose/reflection transforms, legal translations,
random distinct colours, four profiles, and a difficulty-keyed layout RNG.

**Rationale:** this removes dead difficulty behavior and discourages memorization
of absolute coordinates while keeping the exact rule invariant.

**Alternative rejected:** independent random placement of every motif increased
rejection complexity and risked accidental 2×2 interactions.

**Limitation:** the underlying template remains structured. Diversity/grammar
gates and 1,159 unique inputs in 1,200 sampled pairs provide evidence, not a
proof, that layout memorization is insufficient.

## D6 — Separate authority, diagnostics, and semantic competitors

**Choice:** pin `RULE_HASH = "e1a9213544fb"`; keep the Racket program unchanged;
use `diagnostic_output` only as a pure mirror. Declare witnesses, rivals,
canonical shortcuts, lesson competitors, and `lesson_identifiable` explicitly.

**Rationale:** labels must remain authority-backed, while executable Python
competitors make teaching defects cheap to test before invoking an LLM.

**Failure mode caught during review:** the first orthogonal competitor completed
only orthogonal pairs and therefore did not fit the canonical outputs. A red
canonical-fit test forced the corrected definition: apply the intended rule,
then additionally complete orthogonal pairs.

## D7 — Require arbitrary query rotation for this curriculum

**Choice:** treat each four-pair materialized lesson as three demonstrations plus
one query and require every one of the four pairs to be holdout-safe.

**Rationale:** downstream assembly may rotate the query. A curriculum that works
only in one order would be fragile even if each individual label were correct.

**Evidence:** official required semantic gate 0/48 ambiguous; broader census
0/1,200 ambiguous rotations. The focused test also exhausts all cyclic four-row
starts over deterministic schedule windows.

**Limitation:** these checks cover declared rivals and actual production draws;
they do not prove identifiability against undeclared hypotheses or arbitrary
nonconsecutive assembly.

## D8 — No canonical or Racket rule edit

The canonical behavior was internally consistent and rule smoke passed before
repair. The defects were in generation, contracts, and lesson composition, so a
reference-rule edit would have added risk without correcting the root cause.

## D9 — Native two-setting family and source-bound cascade witness (2026-10-25)

- Added `completion_rounds = one_pass | two_pass`; `one_pass` preserves the accepted canonical program byte-for-byte.
- Inputs are setting-independent, support 2–6 demonstrations and four distinct queries, and include a populated 30×30 stress profile.
- The two-pass branch has a real first-pass → intermediate-grid → second-pass dependency. The official protected-Racket witness uses the qualified one-pass program as a skip-A counterfactual and changes the final output.
- Bounded self-review covered 16 seeds × 2 settings × 5 demo counts = 160 episodes and 640 one-query public projections with no surviving declared rival. Native qualification passed four jobs and 32 protected-Racket evaluations.
- Regressions retained: orthogonal-rival output accumulation, all four orthogonal orientations, and bounded seeds that previously left `main_only` or `orthogonal_too` alive.
- Limitation: finite seeds and named rivals do not prove universal uniqueness; owner acceptance and training admission remain separate.
