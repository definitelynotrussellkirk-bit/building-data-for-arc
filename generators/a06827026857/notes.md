# Current notes: a06827026857

## Authority and intended rule

Version `3.0.0`, final generator SHA-256 `d3b867be3b70148a7fca5b0ddd602290829ba38c640f52aa1f5116825c339623`. Racket authority is unchanged:
`4f871ddb0a9d`. Scan the original input for all nonzero monochrome 3x3 windows and
union their four colored corners on a zero output. Unmatched pixels disappear.
The canonical ledger has three training pairs and one labeled test pair.

## Current construction and contract

Unrestricted sample indices alternate `clean` and `mixed` (period 2). Clean draws
have two separated, differently colored 3x3 squares and favor the canonical
8x10, 9x9 and 9x11 sizes. Mixed draws include one corner-attached extra cell and
one 3x4/4x3/4x4 overlap block, with two base targets sharing a color. Their base
counts range 2..3 on easy, 2..4 on medium, and 2..5 on hard. Colors, layout,
orientation and dimensions are seeded. All labels still come from Racket.

Exact controls are dimensions 5..20, base `square_count` 1..5 and `case` in
clean/repeated/attached/overlap/mixed. `observe_overrides` derives them from pixels.
Bounds and types are checked, including rejecting bool/float/string integer
coercion. Explicit infeasible combinations raise a ValueError with named axes;
an explicit count is never reduced. Only unrequested defaults can adapt to a
forced small canvas. `None` retains the context's unspecified-value convention.

Placement uses disjoint 3x3 or 4x4 slots with one-cell gaps, plus offsets and
orientation changes. This guarantees counts, but is intentionally conservative:
5x8/count2/attached has a physical packing outside this slot scheme and is rejected
as a layout incompatibility. This is not a proof of geometric impossibility.
The validator now enforces shape grammar, bounded integer grids, a background
gap including diagonals between components, and at least one base target.

## Teaching evidence and limits

Five declared canonical-fitting rivals are color bounding boxes, component
bounding boxes, isolated-squares-only, preservation of unmatched foreground,
and same-color degree-two thinning. `counterexamples/corner_appendage.json`
contains one Racket-executed 5x5 input refuting every rival. Each mixed sample
carries such a distinction. Three demonstrations suffice for the period-two
schedule: any four consecutive draws contain two mixed samples, so every
single-pair query holdout retains a mixed demonstration.

Final-source measurements: all 12 battery stages green; 64 task-test cases from
13 functions; strict input domain 600/600; canonical exact-profile hits
11/20 easy, 12/20 medium and 9/20 hard. The production census materialized
300 three-demo/one-query lessons (1,193 unique inputs among 1,200 pairs) and
1,200 rotations without ambiguity or errors. The task-local direct-start probe
covered seeds 0..7, starts 0..3, every band: 96 lessons/384 rotations; every rival
was refuted in every case. These are finite tests against the five declarations.

The helpful grammar is deliberately bounded. It does not cover arbitrary larger
rectangles, general touching-object layouts, long appendages, or every malformed
near-square. A solver specialized to the few generated component shapes can
still match its entire support. Arbitrary rule identifiability remains unknown.
Forced case overrides can remove teaching witnesses; use the lesson hook and
source-bound census on the actual exported assembly. No training admission or
approval state was altered by the repair.

## Decisions and reversals

- Original placement tried up to 300 positions and silently returned a partial
  grid. Seed0/index0/medium/8x8/count3 produced two squares. Construct all requested
  shapes after checking slot capacity; regression in `counterexamples/count_drop.json`.
- Original palette_kind, palette_size, n_distinct_colors, position_bias, density,
  and helpful texture fields did not implement real controls. Remove those
  advertised axes; unknown keys now fail. The original rationale is unknown.
- Original hollow/wrong-size comments incorrectly described reference behavior.
  Such no-target inputs are not helpful cases; no degenerate texture is advertised.
- An intermediate repair left default base count at two and accepted different
  colors touching. Review found both limitations; mixed count diversity and
  explicit separation validation replaced those choices, with three failing
  regression cases retained before their fixes.
- No prior reviewer return was used as a lead; this task had empty imported
  associated notes and no task-local audit index in the supplied baseline.

Current repair findings are resolved by the returned source and focused tests.
The separate random audits concern 8e034e635c60 and 5573cf8e2aa4; they are findings
only and do not change this task's authority or another task's source.
## Current reviewer considerations

Source SHA-256: `d3b867be3b70148a7fca5b0ddd602290829ba38c640f52aa1f5116825c339623`.

# Decisions — a06827026857

Final source: `d3b867be3b70148a7fca5b0ddd602290829ba38c640f52aa1f5116825c339623`. Baseline: `f2e1fb24698940316029d47cf5ee888e7e452a53ab83191b0c85667e9091cd65`. The selected Racket authority
is unchanged. The initial notes did not explain the old sampling choices, so
those rationales are recorded as unknown rather than invented.

| Choice | Original / problem | Returned choice and reason | Evidence / limitation |
|---|---|---|---|
| Placement | 300 attempts per color could silently omit a square; stronger-than-described zone exclusion | Construct all shapes after checking a finite slot capacity; exact requested count or structured error | Seed0/index0/medium/8x8/count3 had 2 targets; now 3. Slot packing is conservative |
| Control domains | Advertised bounds differed from difficulty-specific draw bounds; several axes were ignored | Four real axes, strict integers, all-band dimensions 5..20/counts1..5, observable case; reject unknown keys | 58,140 override attempts: 58,050 accepted, 90 explicit compatible-policy rejections, zero findings/warnings |
| Palette | Distinct colors per square made global color bounding boxes sufficient | Repeated colors in mixed/repeated cases; retain distinct-color clean cases | Five rivals fit all four canonical pairs, but fail a retained generated-domain appendage witness |
| Geometry | Only isolated 3x3 squares | Add a corner appendage and 3x4/4x3/4x4 overlapping windows | Reveals unmatched-foreground erasure and original-input corner union; bounded shape grammar remains |
| Canonical support | Hard band had zero exact-profile hits; pooled envelope10% | Keep a clean canonical-size component in every band | Final exact hits11/20,12/20,9/20; clean geometry is newly sampled, not replayed examples |
| Difficulty | Mostly canvas/count restrictions; advertised legal overrides rejected | Keep all exact controls available; mixed base counts2..3/2..4/2..5 and broader canvas preferences | A requested feasible override is never clipped; hard counts >2 appear in ordinary draws |
| Lesson schedule | No executable semantic/lesson contract | Period-two clean/mixed, EXAMPLES_NEEDED=3, five executable rivals and actual-label hook | 300 production lessons/1,200 rotations and 96 direct lessons/384 rotations; finite declared-rival scope |
| Validation | A single 3x3 anywhere sufficed; malformed/full-canvas grids passed | Rectangular bounded integer grid and explicit component grammar/gap checks | 11 initial regression failures fixed; two additional separation failures fixed after review |
| Rule changes | None justified | Keep canonical and archival Racket bytes unchanged; pin RULE_HASH | Authority-sync/rule-smoke gates and original archive comparison |
| Negative examples | Dead textures mixed into valid axis domain | Remove those axes; retain genuine solve attempts only | No manufactured solve failure; unrelated negative shapes are authoring probes only |
| Tooling | No task-specific test or reusable exhaustive-start verifier | Portable tests and dynamic rival/canonical/Racket window probe | 64 pytest cases/13 functions; helper uses actual declarations and batched reference execution |

## Alternatives considered

Keeping the rejection loop but raising after its cap would stop silent truncation,
but still reject feasible requests randomly. Exact constructive placement is
predictable and makes capacity limits inspectable. General rectangle packing
would widen support but adds a separate search problem; the returned slot scheme
states its limitation honestly, including the physically feasible 5x8 attached
case that it does not represent.

Increasing random sampling without changing the old support cannot refute the
color-box rival: that rival is equivalent on every old helpful input. A rewrite
of the Racket rule to preserve distractors would change the task, so it was rejected.
Purely overlapping examples can become identity transformations (a 4x4 block),
so mixed samples always retain reducible base squares.

Every default mixed grid combines the three required distinctions. This makes
all four-pair query rotations retain a refuting demonstration. It does not prove
that the visible data determines all conceivable rules. Component-template
solvers remain possible within this finite shape domain; arbitrary larger or
jointly modified inputs are untested. Override-driven exports must be checked
with their own production lesson assembly.

## Iterations and actual evidence

The initial12-test regression run had11 failures/1pass. The first implementation
passed12 tests and a full battery, but independent review identified separation
validation and fixed default count restrictions. Three additional tests failed
against that intermediate source before the final fixes. The final focused suite
has64 cases from13 functions and no skips. Retained initial and intermediate
failures are not described as final results. Initial isolated task tests failed
because pytest was only installed in the user site, which staged runtimes suppress;
an explicit local virtual environment resolved that environment issue.

The public census is the production sampler. The task-local verifier is direct
consecutive assembly of seeds0..7 and starts0..3 across three bands, with cached
Racket labels. Its168 draws contain142 unique generated inputs;96 overlapping
lesson windows are not96 independent sets of grids. The production census has
1,193 unique inputs in1,200 pairs. Both reports preserve exact identities.

See RESULTS.json for argument arrays, actual working directories, return codes,
evidence paths and the fresh-copy replay. Large intermediate green reports are
losslessly compressed with path/size/SHA mappings in checks/history-manifest.json.

## Native parametric build — review-9b9444e5e15d6661

- Built a native `window_scope` family with `all_windows` and
  `dominant_color`. The default `all_windows` file is the byte-exact 401-byte
  canonical program.
- Step A enumerates solid monochrome nonzero 3x3 windows in the original input
  and counts them by color. Step B either paints every window's corners or,
  for `dominant_color`, consumes the unique support winner and paints only
  that color's windows.
- Teaching scenes deliberately make the first row-major window a decoy and
  give that decoy more foreground area through separated two-row strips.
  Thus neither “first window color” nor “largest foreground color” can replace
  the intended window-support intermediate. A four-seed, 24-job audit found
  zero survivors for both rivals.
- The family supports 2–6 demonstrations, 1–4 matched and shuffled queries,
  and a substantive 30x30 stress query with 371 foreground cells and 141
  qualifying windows. Protected qualification passed both settings over two
  seeds with 40 Racket evaluations. The causal witness replays the exact
  30x30 case where support counts are 90/35/16 and the first-window
  counterfactual changes the output.
- Public projection produced 16 single-query views with no first-turn leaks.
  Evidence is finite and reviewer-reported; exact-source owner acceptance,
  training admission, and measured learning gain remain downstream.
