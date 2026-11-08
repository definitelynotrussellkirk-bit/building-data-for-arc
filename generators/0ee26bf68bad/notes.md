# Current working notes: 0ee26bf68bad

## Selected implementation and authority

Version `2.0.0`; generator SHA-256 `92caaf858ae07f4d83f9d097870d1b21b809fedc0c54478ba77c85984b790717`.
The unchanged canonical Racket source SHA-256 is `d66e3a1b4a29b54e31e6840e6b3b1678065ca61b6402fe12393321e662c9def1`; `RULE_HASH` pins its `d66e3a1b4a29` prefix. Generated labels still come from Racket. `rule_mirror` and the Python rivals are authoring diagnostics, not label authorities.

The rule selects the largest **monochromatic four-connected component by cell count**, retains cells having at least one absent cardinal neighbor in that component, and crops to its bounding box. Internal hole boundaries count. Different colors may touch. Racket resolves largest-size ties by minimum bounding-box row, then column; the sampler deliberately restricts production to a unique largest object. Empty input, a single object, and tied winners are outside this generator's chosen domain even though the rule has behavior on some of them.

The retained witness replay checked all four canonical labels and all 11 handcrafted witness labels with the actual unchanged Racket program. Evidence paths below are relative to the review packet's `WORK/`.

## Current input decisions and reversals

- The baseline `1.2.1` described a bounding-box outline. This was corrected to the actual component contour; no reference-program change was needed. The internal-hole witness distinguishes them.
- The baseline required distinct colors and claimed strictly distinct sizes for all blobs. The repair requires exactly three monochromatic four-connected objects and only a unique maximum size; smaller objects may tie, and separate objects may share a color. Repeated-color distractors distinguish component selection from whole-color aggregation.
- The baseline separation restriction was removed. Differently colored touching objects are lawful and occur in the canonical test. Joint scenes also use diagonal contact between same-colored distractors to distinguish four- from eight-connectivity.
- The baseline's ignored palette/count/density controls and invalid degenerate textures were removed. Four exact controls remain, with explicit validation and rejection of unknown keys.
- The baseline hard-band dimensions excluded all canonical shapes. Every difficulty now mixes canonical shape support with additional band-sized canvases. This is an implemented sampling choice, not a claim that every emitted input is a canonical example.
- Random blob growth could silently omit an object. Both current scene constructors place all three objects directly in a fitting layout.

These choices supersede the baseline source SHA `0d135e3eccf52ec7f95d9f191fdf660ab3d5042a604dc65fb4d58476efe374dd`. The baseline's original undocumented design rationale is unknown; the reversals above are justified by the canonical rule, retained witnesses, and final emitted lesson evidence.

## Distribution and exact controls

The complete canonical input profiles `(height, width, distinct colors including 0)` are `(7,10,4)`, `(8,9,4)`, `(7,11,4)`, and `(8,10,4)`.
Three of every four two-index blocks request one of those canonical **height/width** pairs in every difficulty. The fourth block uses easy `7..10 × 9..12`, medium/default `7..12 × 9..14`, or hard `9..14 × 10..14`. Explicit dimension overrides take precedence. Rectangle scenes have four total colors and can match an exact canonical profile; joint scenes have three total colors and therefore do not match its color count even on a canonical shape. No numeric profile-floor result is inferred merely from this design.

| Exact override | Legal values in every difficulty | Implemented behavior |
|---|---|---|
| `grid_h` | Integers `7..14` | Exact input height |
| `grid_w` | Integers `9..14` | Exact input width |
| `winner_color` | Integers `1..9` | Selected object's color and output foreground color |
| `texture` | `rectangle` or `joint` | Force the requested scene family |

Booleans, floating-point values, and strings are rejected for the integer controls; `None` retains ordinary drawing. Unknown overrides and unknown difficulty names fail explicitly. No combination of the four legal controls is declared incompatible. Forcing a texture changes the default teaching schedule; default-lesson evidence must not be presented as evidence for arbitrary forced-texture lessons.

Rectangle scenes contain a solid `3..5 × 3..5` winner and two smaller shapes with distinct colors. Joint scenes contain an `a×b` winner (`a,b≥4`, bounded by the canvas and capped at 6), minus one internal cell and optionally one corner. The two same-colored distractors have sizes `a+b` and `(a−1)(b−1)`, jointly exceeding the winner's `ab−1` or `ab−2`; they touch only diagonally. The sparse L's bounding-box area is `a(b+1)>ab`. Palette, sizes, placement, reflections, and fitting transposition vary.

`self_check` validates the broader task domain: rectangular integer colors `0..9`, background 0 present, dimensions at most 30, exactly three monochromatic four-connected components, and a unique largest. `strict_canonical_like` intentionally uses this domain test; canonical dimension/color support is a separate question. Validator acceptance is not proof that the generator emits every accepted geometry.

## Teaching support: implemented and reproduced

The default semantic family schedule is period 2: even sample indices use `rectangle`, odd indices use `joint`. `EXAMPLES_NEEDED=3`. This period describes scene families, not repeated grid bytes or the separate dimension schedule. Four consecutive unskipped samples contain two joint witnesses, so a single-pair query rotation still leaves one. Actual accepted indices, not the requested index alone, determine a materialized lesson.

Six rivals fit all four canonical labels: `color_frequency`, `objects8`, `contour8`, `bbox_area`, `bbox_frame`, and `bbox_strip`. The seventh competitor, `crop_full_object`, already fails canonical interior erasure. `counterexamples/joint_six_rivals.json` preserves the exact handcrafted 7×9 joint witness, its Racket 4×4 output, rival predictions, and provenance. It is reproduced reference-lawful evidence, not a claimed sampled input.

Actual family emission is retained in `checks/lesson-final.json`: easy lesson index 0, seed `3819559487`, accepted training sample index `1`, input SHA `30b2754490c0e5398ee2a8980e7d9c8b966224a42c43a0c9ffd5f4b83befc214`. Its generated 7×11 joint input and Racket label are at `lessons[0].instance.train[1]`.

The final source-bound census retained 300 lessons (100 per band), 1,200 pairs, 1,200 query rotations, and 1,197 unique inputs. It reported no production or rotated query ambiguities against the seven unique declared rivals, and no materialization errors, scoring errors, or lesson-hook warnings. This is finite production evidence; the ordinary census does not exhaust all seeds or accepted-pair schedules. See `checks/lesson-final.json` and `checks/lesson-final.summary.json`, bound to the selected source SHA above. The full report SHA is `fe9242c97fcc30d987d2b037305efaa1a25ab92ecfe499315bfd6ecf0e0fa8aa`.

From `WORK/`, reproduce the retained canonical and witness labels with:

```bash
python3 run_with_racket.py python3 ../checks/rival-review/replay_authority.py
```

The observed replay exited 0 and checked four canonical plus 11 witness labels. The label receipt is `checks/rival-review/authoritative-witnesses.json`. The final census's retained invocation is:

```bash
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 0ee26bf68bad --per-band 100 --rotate-query --rotation-policy require --timeout 1800 --out ../checks/lesson-final.json
```

Use a new output path for a fresh rerun; the existing path is retained evidence.

## Open support limits and audit status

Two alternatives remain compatible with both implemented scene families by source inspection: **discard colors occurring in multiple components, then choose the largest remaining object**; and **prefer a hole-containing object, otherwise choose the largest object**. Neither is a declared competitor or a measured differing-query ambiguity in the final census. Rectangle scenes use distinct colors and hole-free shapes; joint scenes repeat only distractor color and place the only hole in the winner. These correlations remain narrower than the validator's domain.

Potential future negative support would let a winning object share its color with a smaller separated object, or place a smaller holed distractor against a larger solid winner. Those extensions are proposed only, not implemented or measured here. Seven-rival success does not establish universal identifiability or training admission.

The prior `review-2df2d57bc7252408:v0001` override audit remains retained in `evidence/review_index.json` as `needs_triage`, bound to the baseline SHA. It was used as an implementation lead. The changed API addresses its listed defect categories, but this note does not automatically close that source-bound audit or assert maintainer approval. Imported associated notes retain their original provenance in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-2df2d57bc7252408:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `0d135e3eccf52ec7f95d9f191fdf660ab3d5042a604dc65fb4d58476efe374dd`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted reviewer-reported source92caaf858ae07f4d83f9d097870d1b21b809fedc0c54478ba77c85984b790717 replaces inert/invalid axes with exact observable controls, validates components and rejects unknown/scalar errors.63 portable tests and22320 override draws reported clean with zero findings. Resolves named old-source public-contract finding only; no fresh maintainer run or universal rival coverage.

### Assessment or prior finding

## 0ee26bf68bad

**Finding A2 — reproduced override-contract defect; no semantic-rule patch was attempted.**

The exact override stage failed on generator SHA `0d135e3eccf52ec7f95d9f191fdf660ab3d5042a604dc65fb4d58476efe374dd`. Across 384 cases and 34,560 draw attempts it reported **11,056 findings** and 4 warnings: 780 generation errors, 3,780 override mismatches, 6,480 self-check failures, 13 axis-effect findings, 2 axis-metadata findings, and 1 accepted unknown key. It also recorded 13,020 unstructured multi-axis rejections. Evidence: `checks/audit/0ee26bf68bad/override-after/checks/0ee26bf68bad_after_override_results.json` and the concise command log `checks/audit/0ee26bf68bad/override-after.console.log`.

Concrete failures include advertised `grid_h`/`grid_w` values being rejected by narrower difficulty-specific draw ranges (for example, easy `grid_h=10` rejected as outside `[7,8]`), accepted draws whose observed dimensions do not match the override, degenerate `texture` values that fail `self_check`, silently accepted unknown override keys, singleton axes (`n_blobs`, `n_distinct_colors`, `palette_size`) that cannot demonstrate an effect, and never-probed single-token metadata axes. The stage exited 1, as expected for this reproduced defect.

I also inspected the main largest-blob/cropped-contour behavior for a simpler bounding-box rival. Irregular generated blobs commonly distinguish the actual contour from a bounding-box outline, so I do **not** claim that shortcut as a reproduced semantic defect. The override-contract failure above is the supported audit finding. No files for this audit target were changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-2df2d57bc7252408-v0001/audit_assets.json), manifest SHA-256 `0d7a98c2b098d28795eaa0fad22873fd3fc6534838ec949955767d7a6668fff3`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `92caaf858ae07f4d83f9d097870d1b21b809fedc0c54478ba77c85984b790717`.

# Decisions for review-069a9b841ebabc26

## M1 — Make every advertised control exact and testable

The retained baseline advertised dimensions that were narrowed again by difficulty, accepted unknown names, and included singleton or ineffective axes. The before battery independently reproduced the contract problem. The new `AXES` consists of `grid_h` 7–14, `grid_w` 9–14, `winner_color` 1–9, and `texture` in `rectangle` or `joint`. Explicit dimensions have the same full legal range in all three difficulty bands. Keyed random choices provide provenance; an override changes the controlled property rather than silently overriding a later draw. Unknown keys and invalid types/ranges raise a structured error.

Dead aliases were removed instead of retaining accepted inputs with no observable meaning. This is an intentional v2 contract change; callers of the old ineffective keys must migrate. `seed` accepts exact Python integers, including negative and large values; Boolean, float and string seeds are rejected. `sample_index` must be an exact nonnegative integer. The final [override receipt](checks/after-final/checks/0ee26bf68bad_after_override_results.json) records 248 cases across three bands and 30 seeds per case, totaling 22,320 accepted draw attempts, with no findings or warnings. This finite matrix is not every combination of random support.

## M2 — Validate objects, preserve the selected authority

The rule acts on monochromatic components joined through shared edges. Counting colors is not an object count: repeated colors can belong to separate objects, and different-colored objects may touch. The validator therefore checks rectangular integer grids, background zero, exactly three monochromatic cardinal components and a unique largest component; equal smaller-object sizes are allowed. It accepts the documented domain more broadly than the emitted templates, including valid repeated-color and touching-color scenes.

The selected rule remains unchanged at `d66e3a1b4a29`. Its Python mirror is an authoring diagnostic, never the authoritative source of generated labels. Tests use an independently written component/contour oracle and portable `reviewer_support` helpers. The semantic tools and witness probes use the selected Racket authority. `lesson_identifiable` compares the finite declared rivals and validates output grids with exact integer colors before equality; otherwise Python would treat `True == 1` and `1.0 == 1` as evidence of a valid label. Genuine red regressions for both cases and malformed seed types are retained.

## M3 — Generate a compact witness for several plausible rivals

All four canonical winners are solid rectangles. Six incorrect rules fit all four pairs: aggregate by color, connect diagonally, use eight-neighbor erosion, choose greatest bounding-box area, draw a bounding-box frame, or strip the entire bounding-box interior. The exact handcrafted joint witness in [QUESTION_ANSWER.md](QUESTION_ANSWER.md) refutes all six with one Racket-checked output. A seventh competitor, keeping the whole selected crop, is useful for lesson diagnostics but already fails the canonical examples.

The generated joint layout uses a target rectangle of `a × b` cells with one internal hole and optional corner removal, where `a,b` range from 4 to 6 when the canvas allows. Its target contains `ab−1` or `ab−2` cells. Two distractors share another color: an L of size `a+b` and a rectangle of size `(a−1)(b−1)`. Their combined color population is `ab+1`, larger than the true target, while each separate component is smaller. The L's bounding-box area is `a(b+1)`, larger than the target's `ab`. The distractors have diagonal contact but no cardinal connection. These relationships jointly distinguish color aggregation, connectivity and selection by bounding box; the hole distinguishes contour definitions. Translations, palette choices, flips and fitting transpositions vary incidental appearance while maintaining the invariants.

A simple rectangle scene remains in the mixture for canonical-like support. The input `(height,width,total colors including background)` profiles include `(7,10,4)`, `(8,9,4)`, `(7,11,4)` and `(8,10,4)` in every difficulty band. Three out of every four two-sample canvas blocks request a canonical shape; the remaining block draws extended dimensions. Both texture families and legal explicit controls remain available in every band. The final profile floor accepted all four canonical inputs and completed 60 draws without a crash; observed exact/envelope hits were easy 9/20, medium 6/20 and hard 9/20. The reference outputs did not change.

A rejected design split the diagnostic evidence into three separate texture families. It required longer lessons and did not make the requested small-lesson query rotations as direct to justify. The adopted joint family puts the six distinctions together, and the rectangle/joint alternation supports three demonstrations plus one query. We also rejected an unqualified claim that any irregular object or a large unstructured random sample automatically establishes teachability: those observations do not test the assembled lesson or every query position.

## Production and rotation policy

`EXAMPLES_NEEDED = 3`. Default generation alternates rectangle and joint semantic families with declared period two. Four consecutive draws contain two joint scenes, so holding out any one leaves a joint demonstration. The actual accepted sampler, not just this source argument, was checked by the final census: 100 requested lesson starts per band (indices 0–99), 300 materialized lessons, 1,200 pair occurrences, 1,197 distinct grids and all 1,200 query rotations. Both production and rotation report `no_ambiguity_found` against the seven declared competitors. No materialization, hook or scoring errors occurred.

The separate fixed-seed run exhausts the declared two start residues in all three bands at seed 0: six lessons and 24 holdouts, with five unique inputs because windows overlap. The semantic period is not the full eight-index canvas cadence. Neither this enumeration nor the random census proves all-seed coverage, the complete validator domain, or universal identification against undeclared rules. Exact seeds, accepted indices and labels are retained in the full final reports; the summaries bind their raw hashes.

## Remaining support restrictions

A new self-review found two meaningful next extensions: allow the winner's color to recur in a smaller component, and place a hole in a losing object while the winner is solid. Current support lets “discard repeated-color components” and “prefer a hole” remain consistent. They are disclosed limitations; this return reports finite success against the declared seven-rival contract. Adding these scene variants later must preserve the existing joint counterexamples and rerun both production and rotation checks. No generator or solve bytes were changed after the final exposed solve was prepared.

## Audits, runtime and handoff

A5998-1 and A3216-1 are source-bound findings-only audits with public Racket counterexamples. Their generators and rules remain unchanged; per-grid checks are not claimed as fresh lesson or battery evaluations. [AUDIT.md](AUDIT.md) gives exact inputs, output disagreements and actual command records.

The first portable task-test preflight found an environment issue: pytest existed only in the host Python user site, which the isolated runner intentionally disables. There was no failing inherited fixture and no test source was staged. The new helper reconstructs the already installed pure-Python distributions as ordinary wheels and installs them with `pip --no-index` into a new venv. It leaves the host unchanged and keeps `PYTHONNOUSERSITE=1`. NumPy/Pillow are supplied by the base interpreter's system site. The final isolated gate passed 63 tests; [F1](FEEDBACK_TO_CODEX.md#f1-offline-portable-test-prerequisites-top-shared-suggestion) proposes a shared opt-in setup improvement.

The return is the official task delta, not another repository copy. The exact source patch was replayed against a full extraction of original ZIP bytes. Git top-level identity, all six changed paths and the final generator hash were checked; all 63 focused cases passed in the fresh copy with zero failures, errors or skips. A filesystem inode limit required freeing the reproducible original repo after protected recovery copies were verified, then moving the fully reconstructed and tested repo back without source changes. Exact commands and recovery receipts are retained in RESULTS.json and checks/fresh-replay/. Full runtime directories and installed environments are reproducible local state and are excluded. Failed logs, exact counterexamples, finished solve notes and source-bound receipts are included. Prior large reports are reversibly compressed with size/hash mappings and restoration instructions.
