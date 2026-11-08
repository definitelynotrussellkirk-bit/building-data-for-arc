# Working notes: bcac0c8a0478

## Baseline finding

The selected `1.4.0` generator produced lawful labels but did not reliably teach
the rule. It placed markers and sparse walls independently, exposed fake or
non-observable axes, accepted unknown overrides, had no pinned `RULE_HASH`, had
no executable semantic contract, and hit no exact canonical profile in the
60-draw floor. The strongest rival—shortest 2→3 first, then shortest 3→5—fits all
four canonical pairs.

No retained prior review was used as a repair lead; `evidence/associated_notes.jsonl`
was empty. The frozen baseline itself and the before battery were the authority
for the diagnosis.

## Repair

Version `2.0.0`:

- pins canonical rule hash `076228df68df` and leaves Racket authority unchanged;
- advertises only four observable axes (`grid_h`, `grid_w`, `use_portal_6`,
  `use_portal_7`) and rejects unknown or out-of-range values;
- carves a randomized perfect maze, adds bounded loops, then searches marker and
  portal placements;
- accepts a candidate only when the exact selected-rule mirror finds a route,
  every requested portal color is used, and the generated output disagrees with
  goal-first, direct-to-goal, and applicable ignore-portals rivals;
- schedules exact canonical profiles for roughly four of every five draws and a
  deterministic broad-dimension draw every fifth sample;
- declares executable rivals, witnesses, witness-to-rival claims, canonical
  shortcuts, and `lesson_identifiable`;
- adds an independent oracle/probe under `workspace/reference_probe.py` plus
  task-local regression, override, determinism, canonical, and Racket parity tests.

## Final measurements

Final generator SHA-256:
`0a81fd0feea8978daa5584364100493c4161318f569c78b9c428d11d6d0214e0`.

- battery: 12/12 stages green (`checks/after/`);
- task tests: 49/49 passed (`checks/task-tests/result.json`);
- profile floor: 50/60 exact, 51/60 envelope;
- semantic gate: strict 490/600, canonical accepted 4/4, all four witnesses and
  all four rival claims verified, 12/12 smoke lessons identifiable;
- independent sampler probe: 600/600 unique, deterministic, validator-clean,
  and counterexamples to each tested rival;
- source-bound census: 300 lessons, 1,200 query rotations, 1,200 unique inputs,
  zero ambiguous rotations or scoring errors.

These are finite checks against declared and independently implemented rivals,
not a proof of unique induction over every conceivable rule.
## Current reviewer considerations

Source SHA-256: `0a81fd0feea8978daa5584364100493c4161318f569c78b9c428d11d6d0214e0`.

# Decisions

## D1 — Keep the canonical rule unchanged

**Input choice.** Treat `repo/shared/data/canonical/puzzles.jsonl` and rule hash
`076228df68df` as authority; repair only the sampler and its contracts.

**Rationale.** The selected Racket program reproduces every canonical pair and
the before battery's rule smoke and authority sync were already green. The
failure was lesson construction, not label semantics.

**Alternatives rejected.** Rewriting Racket to match the old generator's
reachability helper would have changed the task and hidden the defect. No rule
file or canonical row was edited.

## D2 — Remove fake axes instead of emulating them

**Input choice.** Advertise only `grid_h`, `grid_w`, `use_portal_6`, and
`use_portal_7`; validate exact integer ranges and reject unknown keys.

**Rationale.** These four values are directly observable in the returned grid.
The baseline's palette, density, texture, and count names were aliases or did
not control output. The override gate needs truthful controls, not more names.

**Probe/failure mode.** Boundary and joint override tests cover all bands,
portal combinations, unknown keys, and type/range failures. Exact controls can
make constructive search harder at large sizes, so the search is bounded and
failures are loud rather than silently ignoring the request.

## D3 — Construct maze topology before semantic placement

**Input choice.** Carve a randomized perfect maze, open a small band-dependent
number of loop walls, then sample semantic positions.

**Rationale.** Sparse independent walls left too many ordinary shortest paths and
made portals/checkpoint incidental. Maze topology creates meaningful route
choices while retaining guaranteed connected open space before markers are
placed.

**Alternatives rejected.** A fixed template/replay bank would make tests easy but
sacrifice diversity. Fully random walls had too many disconnected or trivial
candidates. Hand-authored corridors would risk a visual shortcut.

## D4 — Reject candidates by executable rivals

**Input choice.** Return a candidate only if intended output differs from:
`goal_first_then_checkpoint`, `direct_to_goal`, and, when applicable,
`ignore_portals`. Require every requested portal color to occur on the selected
state path.

**Rationale.** The goal-first rule fits all four canonical pairs, so mere
canonical likeness cannot teach the ordering state. Candidate-level rejection
turns every ordinary sample into a direct counterexample rather than relying on
lesson-level chance.

**Probe/failure mode.** `workspace/reference_probe.py` independently reimplements
the intended and rival rules. In 600 final-source draws all 600 contradicted all
three rivals. This remains a finite rival set; an unmodeled shortcut may exist.

## D5 — Bias toward canonical profiles while exercising the declared domain

**Input choice.** Default profiles cycle among `(7,9,p6)`, `(7,10,p7)`, and
`(8,11,p6+p7)`. Every fifth sample draws height 7–13 and width 9–16 broadly.

**Rationale.** The baseline had zero exact-profile hits in its 60-draw floor.
A fully broad sampler would weaken canonical support; a canonical-only sampler
would make the declared dimension ranges false. The 80/20 design satisfies both.

**Measured result.** The gate found 50/60 exact profiles and 51/60 envelope
matches; the independent probe found 483/600 exact profiles.

**Limitation.** Broad coverage depends on sample indices reaching residue zero
modulo five. This is deterministic and testable but not distribution-free.

## D6 — Use bounded constructive search, not a hidden fallback

**Input choice.** Try up to 24 fresh topologies and 320 placements per topology,
then raise a detailed `RuntimeError`.

**Rationale.** Returning a weaker fallback would violate the teaching contract
exactly when generation gets difficult. Bounded failure is preferable to a
quiet semantic regression.

**Probe/failure mode.** All advertised override combinations passed the final
contract gate. The final override stage took 42 seconds; this is acceptable but
kept as a performance boundary.

## D7 — Make semantic claims executable and source-bound

**Input choice.** Add `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`,
`WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and
`lesson_identifiable` alongside task-local tests and an independent probe.

**Rationale.** Prose that says a lesson “covers portals” cannot show that the
answer actually changes. Executable claims let the shared gate and local census
replay the exact final source.

**Alternatives rejected.** Counting portal cells or witness frequency alone was
insufficient; a complete lesson can still be ambiguous even if some unrelated
sample contains a witness.

## D8 — Treat test failures as evidence, not erase them

The initial task-local test run failed 29 tests and passed 17, establishing the
missing contracts before implementation. An intermediate defect-lint run caught
that canonical-only defaults did not exercise the full height domain; that led
to D5. The first post-repair visible solve passed 2/3 examples and its second
revision passed 3/3. These records remain under `checks/` and `solve/`.

## Domain limits

The selected tests establish correctness for canonical pairs, generated samples,
axis boundaries, deterministic replay, and the named rivals. They do not prove
universal program identification, distributional fairness for arbitrary caller
sample-index schedules, or bounded runtime on hardware substantially slower than
the review environment.
