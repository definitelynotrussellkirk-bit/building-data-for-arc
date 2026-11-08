# Working notes: `a7a47f5cee60`

## Current rule and source

Version `3.0.2`; generator SHA-256 `0b6a6de52c5d0ca364cb727ef89325e6e263e4d154fbf0653181b3233690a0c3`; selected authority hash `2c1f4bbab8e6` (unchanged).

Treat every monochromatic four-connected nonzero component as a graph vertex. Two vertices share an edge when any cells touch cardinally. On a blank same-size grid, paint every component whose removal increases the graph's connected-component count cyan (8). Ordinary generated inputs contain exactly one multi-cell articulation component and one disconnected 2×2 distractor.

## Repaired distribution

- Profiles: `star`, `triangle`, and shortcut-breaking `cycle`, with random dihedral transform and translation.
- Lesson assembly: three demonstrations plus one query; four-slot schedule `star, cycle, triangle, cycle` so every one-pair holdout leaves a cycle contrast.
- Palette: each object has a unique color; color 2 marks a wrong candidate; target color varies; input 8 appears on about 10% of draws and only on the disconnected distractor.
- Exact public controls: `grid_h` 9–18, `grid_w` 11–22, and helpful texture. Zero/multiple-articulation and empty grids are explicit-only degenerates.

## Reversals and evidence

The issued singleton/pixel representation was replaced because it rejected every canonical multi-cell input (`checks/before/result.json`). Version 3.0.0's one-decisive-contrast schedule passed production ordering but left 201/1,200 rotations ambiguous; the exact retained witness is `counterexamples/query-rotation-v3.0.0.json`. Version 3.0.1 then failed output-marker drift because cyan appeared in 30/60 inputs (`checks/after-v2/result.json`); version 3.0.2 restricts it to the disconnected-distractor minority.

Final evidence: 12/12 battery stages green (`checks/after-v3/result.json`), 49/49 task tests (`checks/task-tests-v3/result.json`), and 300 lessons / 1,200 rotations with zero declared-rival ambiguity (`checks/lesson-census-v3.json`). The independent future-review tool is `workspace/review_probe.py`.

## Known limits

The finite rival set covers fixed input color 2, maximum graph degree, and largest area in the main cluster. It does not prove unique induction against arbitrary hypotheses. Ordinary training examples use three compact topology families and exactly one articulation; explicit degenerates are diagnostic only. Broader topology coverage is the main open distribution improvement, but it should preserve the two-decisive-contrast lesson guarantee.
## Current reviewer considerations

Source SHA-256: `0b6a6de52c5d0ca364cb727ef89325e6e263e4d154fbf0653181b3233690a0c3`.

# Decisions for `a7a47f5cee60`

## D1 — Keep the canonical authority unchanged

**Choice.** Retain the selected Racket rule and pin `RULE_HASH = "2c1f4bbab8e6"`.

**Why.** Rule smoke was already the one green before-stage, and the canonical outputs consistently select articulation **components** in a cardinal-contact graph. The defect was in the generator's representation and curriculum, not the authority.

**Rejected alternative.** Rewrite the Racket rule to match singleton pixels. That would preserve a generator bug by changing a working labeler. **Evidence:** `checks/before/result.json`, final `authority_sync` and `rule_smoke` receipts under `checks/after-v3/checks/`.

## D2 — Model graph vertices as monochromatic components, not pixels

**Prior choice.** v2 encoded each vertex as one colored cell and tested pixel removal.

**New choice.** Each vertex is a monochromatic four-connected shape; cardinal contact creates edges; removing a whole component determines articulation status.

**Reason.** All three canonical selected objects are multi-cell, and the old `self_check` rejected them. **Probe.** `workspace/review_probe.py` and the test suite independently reconstruct the graph and compare labels. **Limit.** Ordinary draws use compact components and do not span every possible topology or morphology.

## D3 — Use audited symbolic topologies, then randomize geometry

**Choice.** Build `star`, `triangle`, and `cycle` component graphs, then apply one of eight dihedral transforms and a random translation.

**Why.** Randomly placing arbitrary shapes and hoping for one articulation produced a difficult-to-audit rejection sampler and made semantic contrasts accidental. Symbolic templates give a small topology certificate while preserving geometric variety.

**Rejected alternatives.** Pure random walks risk unintended contacts and multi-articulation graphs; all-canonical copying would overfit three layouts. **Failure mode.** The three-family signature is learnable; broader graph families are future expansion, not silently claimed coverage.

## D4 — Include a disconnected distractor on every ordinary draw

**Choice.** Add one isolated 2×2 component, separated by an empty cardinal halo.

**Why.** Canonical examples contain disconnected foreground, and articulation must be measured relative to the full graph's component count. This prevents solvers from assuming every object belongs to one connected cluster and ensures the validator handles the baseline correctly.

**Rejected alternative.** Ignore disconnected components when scoring articulation. That changes the graph definition and would make the implementation fragile to canonical distractors.

## D5 — Make color 2 a decoy and keep colors object-unique

**Choice.** Every object receives a distinct color; target color varies; color 2 is always assigned to a wrong object.

**Why.** The canonical pairs admit the tempting shortcut “paint input color 2.” Unique object colors also prevent accidental same-color merging after contact. **Probe.** `input_color_two` fits the canonical pairs but is refuted on every tested generated input.

**Rejected alternative.** Uniform palette draws. They can place color 2 on the target or merge adjacent semantic vertices, weakening or corrupting the intended lesson.

## D6 — Keep input cyan 8 rare but represented

**Prior choice (v3.0.1).** Sample 8 like an ordinary object color. Version-keyed draws then contained 8 in 30/60 lint samples, so the output marker was not newly introduced often enough.

**New choice (v3.0.2).** Include input 8 on about 10% of draws and only on the disconnected distractor. The target never starts as 8.

**Reason.** This covers the canonical test palette without erasing the strong but legitimate “output introduces cyan” cue on most examples. **Evidence:** failed `checks/after-v2/result.json`; final frequency regression requires 5–20 inputs with 8 per 100 draws in each band.

## D7 — Schedule two decisive contrasts per four-pair lesson

**Prior choice (v3.0.0).** A three-profile cycle supplied one decisive `cycle` contrast in many four-pair lessons. Production order passed, but holding that pair out left `max_degree` and `largest_in_main_cluster` alive in 201/1,200 rotations.

**New choice.** `_LESSON_SCHEDULE = ("star", "cycle", "triangle", "cycle")`, with three demonstrations and one query.

**Reason.** Every possible query holdout leaves at least one cycle contrast among the demonstrations. **Evidence:** exact failed witness in `counterexamples/query-rotation-v3.0.0.json`; final census is 0/1,200 ambiguous rotations. **Rejected alternative.** Declare production ordering mandatory and ignore rotations; downstream assembly explicitly permits query rotation diagnostics, so the safer four-slot schedule is cheap.

## D8 — Expose only observable, exact controls

**Choice.** Public axes are exact height 9–18, width 11–22, and helpful profile `star|triangle|cycle`. Unknown keys, coercible values, invalid difficulty, and out-of-range values reject loudly. Degenerate textures exist for explicit probes but are not advertised as ordinary valid values.

**Why.** The old broad/implicit contract encouraged dead or dishonest controls. Exact dimensions and topology are directly observable. **Evidence:** 19,080 override draws passed with zero findings.

## D9 — Separate lawful-input validation from curriculum witnesses

**Choice.** `self_check` validates the ordinary grammar—one multi-cell articulation, a disconnected distractor, distinct object colors, and a nontrivial main cluster. Shortcut-specific claims live in witnesses/rivals and task tests.

**Why.** Validators should not reject lawful canonical inputs merely because they lack a training-specific contrast. **Rejected alternative.** Require every canonical input to contain the cycle tie/area witness; that would again confuse curriculum policy with rule legality.

## D10 — Use independent, portable probes

`tests/test_articulation_curriculum.py` locates the packet through `reviewer_support.find_root`, reads canonical pairs through the shared helper, and implements its own component/contact oracle. `workspace/review_probe.py` is a command-line inspection tool for future agents. Neither imports the generator's graph helper, so a shared implementation error is less likely to make both production and tests agree falsely.

## D11 — Interpret the final evidence narrowly

The final battery, 49 tests, and 300-lesson census establish deterministic behavior, canonical ownership, exact-control integrity, and identifiability against three declared rivals under the tested schedule and rotations. They do **not** prove universal induction, all graph topologies, or all possible shortcuts. The ordinary curriculum intentionally has exactly one articulation target; explicit degenerate probes cover zero and multiple targets but are not training defaults.


## Reviewer return `review-d0dbf7ec1e680035` — native target-role family (2026-10-25)

Built `workspace/parametric/` around `target_role=articulation|largest_articulation_neighbor`. The default is the exact selected canonical source (`2c1f4bbab8e6…`). The alternative deliberately preserves the hard graph step: it reconstructs monochromatic component contacts and finds the unique articulation before choosing that articulation's unique largest-area neighbor.

The lesson grammar uses a leaf attached to a biconnected four-cycle plus a disconnected biconnected degree decoy. This separates articulation, maximum-degree, global-largest, color-2 and first-object shortcuts. Inputs are matched, 2–6 demonstrations and stable 1–4 query prefixes are supported, and the dense 30×30 query touches all four boundaries. A bottom-boundary regression found during TDD was repaired by translating the decoy template left rather than weakening the test.

The causal intermediate is articulation index 4, neighbors `[2,3,5]` with areas 32, 30 and 9, and selected index 2. Replacing it with articulation index 4 changes 52 protected-Racket output cells. The first 128-seed audit attempt hit a short outer timeout; the final identical 128-seed run completed in 23.86 seconds and covered 768 episodes / 5,888 pairs with zero declared query-changing survivors. Final target suite: 111 tests; minimum/maximum qualification: 96 protected-Racket evaluations; public projection: 16 one-query views.

Production generator and canonical authority were unchanged. Next useful action: integrate these exact task-local bytes, rerun qualification and causal replay, and perform owner acceptance only on the matching live source binding.
