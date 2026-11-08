# Working notes: a950d6dbe2e0

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-04 reviewer repair: review-07e1d618a0904d24

Baseline source: `a178970b81f5660c93339f696cf53f131c00795347cb08ff5d839b750612b593`.
No prior task-specific return or retained substantive notes were present as a lead.
The original sampler advertised controls it ignored, rejected valid declared
sizes under difficulty-specific bounds, and never produced canonical 10x10 or
12x12 canvases. Its validator accepted empty/invalid/exterior-seed cases.

The replacement samples inputs only and pins the already verified Racket rule.
It preserves even canvases and the upper-left source convention, broadens the
size/count/palette support, uses constructive sampling without replacement,
and reports the four realized axes from pixels. Exact single-axis requests stay
feasible by conditioning the other dimensions/counts. Joint impossibilities name
the axes involved instead of clipping, retrying forever, or ignoring the request.

### Domain and compatibility decisions

- Two or more colours make colour preservation visible in every training example;
  square core examples also guarantee repetitions. This excludes legitimate
  one-colour rule inputs; it is an intentional curriculum restriction. A future
  mono-colour mode needs its own explicitly balanced lesson design.
- `palette_kind`, `palette_size`, `texture`, `position_bias`, and `density` were
  inert/redundant/fixed declarations in the baseline. They are removed, including
  the negative-fixture texture path. They now raise an unknown-axis error.
  `palette_size` callers should use `n_distinct_colors`. The version is bumped
  to 2.0.0 because this is an observable API change.
- `grid_h`/`grid_w` support every even size 4..30 in all bands. `n_cells` is 2..64
  bounded by quadrant capacity, and colour count is 2..min(9,n_cells).
- Odd dimensions, empty motifs, one-colour motifs, and exterior distractors are
  outside this sampler's declared training domain. No reference rule was changed
  to enforce these authoring choices.
- Exact overrides take priority over the square/rectangle schedule; an override
  that forces all-square lessons loses the square-shortcut teaching guarantee.
- The default period is three: square, rectangle, rectangle. Every consecutive
  three-example window contains a rectangle; every four-example window contains
  at least two, so removing any one as query still leaves a rectangular demo.
  Resampling or downstream assembly that changes the window needs its own check.
- The generator has no reference outputs, private-answer reads, canonical grid
  replay, or calls to the rival solvers while generating inputs. Rival functions
  exist only for authoring checks.

### Verification and reusable probes

`tests/test_generator_contract.py` covers exact and infeasible joint controls,
all canonical inputs, missing canonical sizes, invalid grid data, observer
honesty, immutable fresh return values, retired controls, and all three cyclic
starts with every query rotation for the declared rival set. Its geometric test
oracle is independently expressed by concatenation. Production labels come from
Racket in the separate lesson census and witness replay.

Run `workspace/probe_witnesses.py --out NEW_DIRECTORY` through the packet's
`run_with_racket.py`. It reads the current rival declarations, verifies each
canonical-shortcut claim, and executes six controlled boundary/counterexample
inputs plus all three canonical inputs with the public `Catalog.apply` API.
It preserves outputs, source/rule hashes, and the command's actual cwd.

The accompanying return retains the complete failed baseline, the initial
47-fail/8-pass regression run, the later 67-pass portable run, the twelve-stage
after battery, and 300 production lessons / 1,200 query rotations. The initial
portable invocation could not import user-site-only pytest; this environment
failure is retained separately from the passing isolated-environment rerun.
Finite rival results do not prove uniqueness against all possible programs.
## Current reviewer considerations

Source SHA-256: `c4c6cb2a11096dff0d692a977387a0108e48807f4c51627bd6db79fa3a3ba3f3`.

# Design decisions — a950d6dbe2e0

Final generator SHA-256: `c4c6cb2a11096dff0d692a977387a0108e48807f4c51627bd6db79fa3a3ba3f3`.
Canonical Racket rule hash: `6c2ec896ad53`, unchanged. Full rule-file hashes are
retained in checks/witnesses/racket.json and the check manifests.

| Decision | Original rationale / defect | Adopted choice | Alternative and limitation |
|---|---|---|---|
| Canvas support | Original rationale unknown; defaults 6..8 excluded canonical 10/12. | Every even dimension 4..30; independently realizable rectangular shapes. | Odd sizes are reference-defined but outside the chosen quadrant curriculum. |
| Canonical support | Canonical inputs have 5/6 cells and 2/3 foreground colours. | Every third default index draws an 8/10/12 square with 5/6 cells and 2/3 colours. | Pure broad random sampling can starve exact profiles; replaying canonical grids would introduce memorization. Neither is used. |
| Rectangular teaching | Square canonical examples cannot distinguish axis-extents. | Other two residues are non-square in every band; all orientations/sizes remain available. | Independent square/rectangle draws allow all-square lessons. The explicit period avoids that. |
| Cell count | Old `n_cells` declaration was ignored; placement could silently shorten. | Exact count 2..64, without-replacement positions and capacity-aware shapes. | Unbounded dense sources add cost and weaken motif clarity; capacity beyond 64 is intentionally unadvertised. |
| Colour count | Old palette controls were inert and summary incorrectly promised distinct colours. | Exact 2..9 distinct colours, each used, random identities and repeated occurrences. | One-colour inputs are lawful but excluded so every ordinary example shows colour preservation. This is a real restriction, not an assertion of rule invalidity. |
| Source region | The authority reads upper-left seeds and leaves/overwrites exterior pixels according to its program. | Training seeds remain upper-left, with all other cells initially zero. | Arbitrary-quadrant symmetry completion would change the task's contract and is not introduced. |
| Exact controls | Difficulty bounds contradicted advertised bounds. | Validate global domains first, condition other choices on supplied values, name joint impossibilities. | Clamping, ignoring values, or broad exception exemptions would conceal defects. |
| Retired axes | `palette_kind`, `palette_size`, `texture`, `position_bias`, `density` were misleading. | Remove them and raise explicit errors; use n_distinct_colors for palette_size. Version 2.0.0 marks the API change. | Maintaining fake aliases would preserve false independent degrees of freedom. |
| Validator | Accepted invalid colour types, exterior seeds, empty inputs and negative fixtures. | Check rectangular integer ARC grids, domain dimensions, placement, and multicolour nonempty motifs. | Requiring exact canonical coordinates would overfit; validator remains broader than the default teaching schedule. |
| Authority | Before rule smoke/authority checks passed. | Keep canonical and archived Racket bytes unchanged. | No Python label fallback or source-rule rewrite is justified. |
| Rival set | No executable semantic contract existed. | Two square-only shortcuts, plus identity and the two one-axis rivals. | This finite family does not cover every conceivable shortcut. |
| Solves | Packet requires blind-before-repair and exposed-after-repair episodes. | Keep separate finished logs and one actual revision each; 3/3 visible matches each. | Hidden-query correctness stays unknown; no invented failure/teaching negative. |

## Scope and rejected shortcuts in the repair itself

The new source introduces no fixed seed position, fixed colour identity or fixed
output template. Positions are sampled from every cell of the upper-left
quadrant, and the 67 tests include fully occupied small quadrants. The period
correlates shape with sample index, but sample index is not a grid feature; each
rectangle directly demonstrates separate row/column reflection extents.

The two-colour minimum and even dimensions are deliberate distribution limits.
They keep all three canonical inputs and do not change the Racket function.
Custom all-square overrides, fewer examples, nonconsecutive assembly, and unseen
rival families are outside the measured lesson guarantee and need separate
validation. This prevents a finite clean census from becoming a universal claim.

## Evidence populations

- Baseline `a178970...`: the full before battery and the initial 55-test file
  produced 4 failed stages / 2 advisories and 47 failed / 8 passed focused tests.
- Final `c4c6cb2...`: 67 focused task tests, 12 green stages, 6,930 override
  draws (77 cases x 30 seeds x 3 bands), 6,120 accepted and 810 intentional
  incompatible requests, with zero findings/warnings.
- The semantic gate's pinned 200 draws per band total 600; 600/600 satisfy the
  task domain, with 408 rectangular witnesses. Its retained report identifies
  the census and executable source. Exact-profile support is separately 4/20,
  2/20 and 4/20 in easy/medium/hard; profile does not mean exact grid replay.
- The production census uses 100 SHA-derived seeds per band, starts 0..99,
  three demonstrations and one query. All 300 lessons materialized; they contain
  1,200 unique inputs. All four query positions were checked, yielding 1,200
  rotations of those same labelled pairs, not 4,800 independent inputs.
- Unit construction checks cover seed 0..11, starts 0..2, all three bands, and
  all four query rotations. They use an independent geometric test oracle;
  actual reference execution is separately retained in the production census.

All source-bound counts refer to the full final SHA above unless explicitly
labelled before/intermediate. Final handoff evidence lives in checks/handoff/.

## 2026-10-24 native parametric review: review-a38a551c738ff9bc

The production generator and canonical authority remain unchanged. The native
parametric family lives under `workspace/parametric/` and has two matched-input
settings:

- `full_orbit` is byte-exact to canonical Racket SHA-256
  `6c2ec896ad533e5817e06ef1f2c69fc3fc3b61c8df7d9e7f6d11c12570b9f0ad`.
- `largest_after_lateral` first mirrors the upper-left source laterally,
  recomputes same-color four-connected components, and mirrors only the largest
  post-reflection component downward. Its Racket SHA-256 is
  `7053d2e8a1283d19efadff71e5fca2ff8715acfc5d2614c03eb6ce5ea72713f3`.

The first pass deliberately merges a midline-touching source object into its
mirror, changing which component is largest. The retained protected-Racket
counterfactual selects before that pass and produces a different final output;
this is the required sequential-dependency witness, not a metadata-only claim.

Verification retained for the exact adapter SHA-256
`913e11446bcd0ac04bd462295f855045df56ea4ceed7c6f6bacb4b37e915faa6`:

- 99 task-local tests passed, including 32 parametric-family tests.
- A 384-episode finite audit covered 64 seeds, both settings, demo counts 2, 3,
  and 6, four queries, 384 exact 30x30 pairs, and 2,944 cases where the first
  operation changed the largest-component selection; no declared rival survived.
- Native qualification ran both settings at seeds 0 and 17 with two demos and
  four queries: four jobs, 32 protected-Racket evaluations, execution SHA-256
  `a34686f6f29cdf912fd6ebb222034e37db87666eb3fe01478c10f7e0aa1d9403`.
- Eight sequential one-query public projections passed the independent export
  checker.
- The source-bound witness SHA-256 is
  `93d91a274a4db4895c5d3ced7441c77f9a5ce0701e95942477b24971e8c11ca7`.

Limits: the rival set and seed sweep are finite. This is reviewer-ready native
prototype evidence only. Owner integration, fresh qualification, acceptance
replay, and explicit acceptance remain mandatory; no training admission is
claimed.
