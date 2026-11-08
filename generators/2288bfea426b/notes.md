# Working notes: 2288bfea426b

Final repair version: `3.0.0`
Final generator SHA-256: `84d0de4a5429d97799bf1746f3a6a530b4105c1746b71110efe1b164c34cd4c1`
Pinned canonical rule hash: `4df94edcd4cc`
Canonical/Racket authority changed: **no**

## Baseline diagnosis

- Missing `RULE_HASH`; dead/singleton controls; unlawful negative textures in the ordinary domain.
- Declared exact ranges did not survive difficulty branches, unknown controls were swallowed, and several controls were not consumed.
- Canonical 13×13/five-color profile support was absent from easy and medium.
- No executable semantic witnesses, rivals, lesson hook, or schedule contract.

The exact baseline source is retained as `workspace/generator-v2.0.1-baseline.py`.

## Repair summary

- Four exact axes only: height 10–18, width 11–18, prototype size 3–6, markers 2–5.
- Every valid joint control is constructive in every band.
- All fixed 4-connected polyominoes of size 3–6; repeated codes and all four marker codes are represented.
- Even indices are teaching scenes; odd indices alternate canonical-core and broad scenes.
- Fourteen executable rivals: two canonical-fitting marker-count shortcuts and twelve code-map errors.
- Three demonstrations per lesson; production and all query rotations checked.
- Portable independent probe uses `reviewer_support` rather than parent-depth guesses.

## Final evidence index

- Full battery: `checks/after/checks/2288bfea426b_after_battery_summary.json` — 12/12 green.
- Protected tests: `checks/task-tests-final/result.json` — 36/36 passed.
- Lesson census: `checks/lesson-census.json` — 300 lessons, 1,200 rotations, zero declared ambiguity.
- Independent sampler/Racket audit: `checks/reference-probe-final.json` — 1,000 samples and 52/52 parity.
- Decisions and limitations: packet-root `DECISIONS.md` and `REVIEW.md`.

## Remaining caution

The alternating profile schedule is visible from dimensions/layout if raw sample order is retained. Shuffle completed lessons and treat the 14-rival result as finite evidence, not universal identifiability.
## Current reviewer considerations

Source SHA-256: `84d0de4a5429d97799bf1746f3a6a530b4105c1746b71110efe1b164c34cd4c1`.

# Decisions for 2288bfea426b

## D1 — Keep the canonical Racket authority unchanged

**Original rationale.** The baseline notes did not document a rule-design rationale. Direct inspection showed that the canonical program, canonical examples, and base selected authority agree on a coherent rule: normalize the color-2 prototype by its bounding box, rotate according to marker code `1/3/4/6`, stamp color 8 on a fresh grid, clip at edges, and union overlaps.

**Selected choice.** Pin `RULE_HASH = "4df94edcd4cc"` and repair only the input sampler and lesson contract.

**Alternatives considered.** Narrow the authority to the baseline's 2–3 distinct markers and four hardcoded shapes; preserve input pixels in the output; or edit the historical archival copy to silence sync diagnostics. Each would turn a sampling accident or archival mismatch into authority rather than fixing the generator.

**Probe and result.** Rule smoke executed 120 generated inputs with zero crashes, identities, mutations, or invalid dimensions. The independent oracle matched 4/4 canonical pairs and 52/52 real-Racket applications. Authority sync reports selected execution parity `PASS`.

**Failure mode / limitation.** The independent Python oracle is still a second implementation and could share a conceptual mistake. The unchanged source-bound Racket checks reduce that risk; they do not constitute a formal proof.

## D2 — Remove fake axes instead of preserving compatibility aliases

**Original rationale.** Unknown. Baseline `AXES` advertised eight controls, but several were singletons, silently ignored, aliases, or unrelated to output. Ordinary `texture` values included unlawful negative fixtures.

**Selected choice.** Expose only four observable integer axes: `grid_h`, `grid_w`, `template_size`, and `n_markers`. Reject unknown keys and invalid types/ranges before generation. Add `observe_overrides` for independent measurement.

**Alternatives considered.** Keep old names as no-op aliases; mark every dead axis diagnostic; or add low-level position/shape IDs as exact controls. Aliases preserve misleading API surface, diagnostic labels would not make them useful training factors, and low-level controls would greatly enlarge the joint matrix without a current curriculum need.

**Probe and result.** The final matrix accepted all 22,680 planned draws over 252 cases and three bands with zero findings or warnings; the unknown-key probe was rejected. Boundary controls are also covered by task-local tests in every band.

**Failure mode / limitation.** Exact placement, marker-code multiset, clipping, and overlap are intentionally distributional rather than public controls. Experiments needing exact values must add an observable tested axis instead of depending on RNG internals.

## D3 — Make all advertised joint controls constructive in every difficulty band

**Original rationale.** The baseline declared global ranges but difficulty branches narrowed them, causing valid advertised controls such as `grid_h=10` to fail in easy mode. Marker placement could also terminate short after retries.

**Selected choice.** Validate against one global domain and use difficulty only as a weighting preference. Enumerate a lawful shape first, then construct marker candidates and remove neighbors after each draw; if an internal capacity invariant were ever violated, fail loudly instead of returning a shortened example.

**Alternatives considered.** Clamp controls into each band, declare many incompatibility clauses, or retry until a scene happens to fit. Clamping makes controls non-exact, incompatibilities would describe an avoidable implementation artifact, and retries make support seed-dependent.

**Probe and result.** `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty, every planned combination passed, and task tests exercise the lower/upper control boundaries across `None`, easy, medium, and hard.

**Failure mode / limitation.** The public canvas domain is 10–18 high and 11–18 wide, not the full ARC 30×30 envelope. This is an intentional training range, not an authority restriction.

## D4 — Replace four hardcoded templates with all fixed connected polyominoes of size 3–6

**Original rationale.** The baseline selected four asymmetric shapes of 3–4 cells. That was enough to execute the rule but made shape support very narrow.

**Selected choice.** Deterministically enumerate every fixed 4-connected polyomino through six cells, normalize each bounding box, and sample from the requested size. The shape library is cached and independent of Python hash order.

**Alternatives considered.** Random growth with retries, free polyominoes modulo rotations/reflections, disconnected templates, or canonical-only silhouettes. Exhaustive fixed shapes give exact size support and retain orientation diversity; free-shape deduplication would reduce orientation coverage; disconnected templates are outside the repaired contract; canonical-only shapes would encourage memorization.

**Probe and result.** The 1,000-sample audit observed 574 distinct source shapes, 1,000 distinct grids, and 904 shapes with all four rotations distinct. Determinism held for all draws and across two `PYTHONHASHSEED` values.

**Failure mode / limitation.** Connected size-3–6 prototypes are a chosen domain. The Racket selector may execute on larger or disconnected color-2 sets, but those are not claimed training support.

## D5 — Add a recurring canonical-profile component in every band

**Original rationale.** Baseline canonical support was absent in easy and medium: both produced 0/20 exact profile hits, while hard produced 5/20.

**Selected choice.** On odd indices with `sample_index % 4 == 1`, emit a 13×13, five-cell prototype with three distinct rotation codes—the canonical dimension/palette profile—regardless of difficulty. Other odd indices remain broad, and even indices are teaching scenes.

**Alternatives considered.** Use canonical dimensions exclusively, depend on random weighted hits, or special-case only hard. Canonical-only sampling would collapse diversity; probabilistic support can disappear in a finite run; hard-only support repeats the baseline defect.

**Probe and result.** The source-bound floor found 21 exact hits in 60 draws with at least one hit in every band. The larger audit found 254 exact-profile cases in 1,000 draws and accepted all four canonical inputs.

**Failure mode / limitation.** The recurring profile creates a visible 13×13 schedule component. It is mixed with broad and teaching cases in every lesson, but raw sample indices should not be exposed to a learner.

## D6 — Use explicit teaching scenes rather than hope random examples teach all branches

**Original rationale.** Canonical examples use only three markers and no repeated marker code. Consequently two plausible wrong rules—process only three markers, or process only one marker per code—fit every canonical pair.

**Selected choice.** Every even default index is an 18×18 teaching scene with five markers in disjoint stamp regions, all four codes, one repeated code, and a prototype whose four rotations are distinct. `EXAMPLES_NEEDED = 3`; every four consecutive pairs contain two teaching scenes, one canonical-core scene, and one broad scene.

**Alternatives considered.** Pure random sampling plus rejection, one giant fixed lesson, or label-time resampling until rivals happen to be refuted. A deterministic schedule gives bounded teaching support and reproducible failures; a single fixed lesson would reduce diversity; label-time rejection obscures accepted-index behavior.

**Probe and result.** Every tested teaching scene refuted all 14 rivals. The shared semantic gate passed 12 lesson smoke cases. The 300-lesson census found zero production ambiguity and zero ambiguity across all 1,200 held-out query rotations.

**Failure mode / limitation.** Teaching geometry is recognizable and scheduled. The finite rival pass does not rule out a position- or dimension-based hypothesis not represented in the contract.

## D7 — Declare executable rivals, including canonical-fitting shortcuts

**Original rationale.** The baseline had no semantic contract, so correct labels could still be assembled into an underdetermined lesson without any gate noticing.

**Selected choice.** Declare 14 predictors: `deduplicate_marker_code`, `first_three_markers`, and every single-code replacement among `1,3,4,6`. The first two are also declared as `CANONICAL_SHORTCUTS`; each is verified to fit all four canonical pairs and to fail a generated witness.

**Alternatives considered.** A prose list, all 255 arbitrary code maps, or a generic mutation fuzzer. Prose is not executable, exhaustive arbitrary maps add redundancy because each code is individually taught, and unguided mutations often do not represent plausible induction rules.

**Probe and result.** The semantic gate passed all 14 witness and rival claims. The independent 1,000-sample audit found hundreds of counterexamples for every rival, and the census refuted every namespaced rival in every lesson.

**Failure mode / limitation.** The set does not explicitly model every wrong anchor, crop, rotation-origin, or output-preservation convention. Passing means finite separation from these 14 hypotheses only.

## D8 — Strengthen `self_check` to define a lawful input domain

**Original rationale.** Baseline validation required only at least two color-2 cells and two distinct marker colors. It did not require rectangular integer grids, one connected template, a marker-count bound, or separation.

**Selected choice.** Validate ARC colors and dimensions, exactly one 4-connected 3–6-cell color-2 component, 2–5 marker cells from the four legal codes, and no 4-touching marker/template or marker/marker pair. Repeated codes are lawful.

**Alternatives considered.** Treat rotation-symmetric templates and missing branches as ordinary degenerates, or enforce that every output stamp fits fully in bounds. Missing template/marker cases do not teach the selected rule; forcing in-bounds stamps would remove the authority's clipping branch.

**Probe and result.** The strict semantic census passed 600/600 generated inputs and accepted 4/4 canonical inputs. Malformed, ragged, boolean-valued, and unsupported-color grids return diagnostics rather than raising.

**Failure mode / limitation.** `self_check` validates inputs, not the correctness of a predicted label. Racket remains necessary for authoritative output checks.

## D9 — Keep the Python predictor supplementary and fail closed on Racket parity

**Original rationale.** A Python mirror is useful for fast rival scoring and unit tests, but using it as label authority would risk silently replacing the selected Racket program.

**Selected choice.** Keep `_prediction` and `workspace/reference_probe.py` explicitly supplementary. The probe's `--racket` mode raises on an unavailable or failed runtime and records source/probe/rule hashes.

**Alternatives considered.** Fall back silently to Python, import internal generator helpers into the oracle, or omit independent parity. Silent fallback weakens evidence; shared helper code can reproduce the same bug; no parity leaves the semantic contract unbound to authority.

**Probe and result.** Final parity passed 52/52 grids: all canonical pairs plus retained generated cases. The protected task suite separately ran the real-Racket regression.

**Failure mode / limitation.** Only 52 parity cases were executed in the independent batch. The source-bound rule smoke supplies 120 additional Racket executions, but neither is exhaustive.

## D10 — Add portable task-local tests and reusable review tooling

**Original rationale.** The selected task had no local regression suite. The first probe also used a fixed `parents[3]` root, which happens to work in the source tree but is not a portable contract.

**Selected choice.** Add tests before implementation, retain the baseline source, and make the finalized probe use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`. Add a regression that copies the probe to an arbitrarily deeper runtime and verifies root discovery.

**Alternatives considered.** Rely only on the shared battery, edit frozen root fixtures, or hardcode source-checkout paths. The battery does not exhaust cheap schedule starts or portability; frozen fixtures are immutable; fixed paths break copied runtimes.

**Probe and result.** The initial feature suite failed 19 tests for the expected missing contract. The portability regression failed against the fixed-parent probe and passed after repair. Final direct tests were 35 passed plus one expected Racket skip; the protected copied-runtime run passed 36/36.

**Failure mode / limitation.** Tests are task-specific and finite. They complement rather than replace the source-bound battery and larger census.

## Final distribution self-review

The most obvious new shortcut is profile-by-index: teaching scenes are even and 18×18, canonical-core scenes recur at one odd residue, and broad scenes occupy the other odd residue. That schedule is necessary for bounded lesson support but should be hidden by shuffling completed episodes. As a concrete check, each four-pair window was evaluated with every pair held out, and all 1,200 query rotations remained distinguishable from the 14 declared rivals.

A second restriction is the connected size-3–6 prototype domain. The 1,000-sample audit shows broad shape and placement diversity inside that domain, including clipping, repeats, and all marker codes, but no claim is made for larger or disconnected templates. A future shared shortcut miner should test low-complexity position, dimension, and morphology rules beyond the hand-authored rival set.
