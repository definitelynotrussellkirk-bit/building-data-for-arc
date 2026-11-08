# Review notes: 531e65dffc0a

## Source and scope

The selected packet baseline was version 1.2.1, SHA-256
`1e23bb1c7e683034cf28ac6c354b9b3e8a9f43ef3310d8244a82d08fbb1c03bb`.
Associated notes were empty. No earlier returned repair was used as evidence.
Canonical authoring data contains two demonstrations and one test pair. The rule
and base authority are unchanged; the canonical program pin is `4acd30f1e03a`.

## Reproduced defects and corrections

1. All four original override controls were ignored, and unknown controls were
   swallowed. Every advertised axis now goes through a public keyed draw, strict
   type/domain checks, and a pixel-observable return contract. Prototype color is
   also an exact control. The accepted joint domain is the full Cartesian product
   of heights/widths 8..18, sizes 2..6, counts 1..6, and colors 1/6/7/8/9.
2. Missing prototypes and malformed or disconnected scenes passed self-check.
   The validator now enforces the declared one-prototype domain while retaining
   every canonical input, empty bounding-box corners, clipping and overlap.
3. The canonical yellow example uses a 180-degree symmetric S tetromino, so
   yellow-as-identity fits every canonical pair. A retained baseline census also
   exposes clipping, overlap, source-erasure and normalization shortcuts. Each
   teaching scene now differs from all six canonical-fitting rivals in pixels.
4. A first three-anchor repair passed those six rivals but still omitted rotation
   codes from some lessons. The independent mapping audit found 37/183 ambiguous
   medium linear windows and 159/732 cyclic rotations. Version 2.1.0 uses all four
   codes and additionally checks all twelve single-code substitutions before
   returning a teaching scene. The earlier result and failures are preserved.
5. Initial task-test imports worked under ordinary pytest but failed the official
   stage's importlib mode. Tests now load their sibling by its own file path.

## Distribution decisions

Polyominoes are sampled from a finite deterministic enumeration of all fixed
connected shapes of the requested size, rather than an unbounded random walk.
The broad branch includes symmetric shapes and all permitted axis values. Its
placement capacity is constructive: on 8x8, six prototype cells exclude at most
30 candidate positions; five existing anchors exclude at most 25 more, leaving
at least nine choices for the sixth anchor. Counts are never silently shortened.

Default even indices use square 11/12 canvases, asymmetric 4..6-cell prototypes,
and four distinct anchor codes. Two stamps overlap, one clips, a fourth supplies
the missing code, and a stamp intersects the source footprint. The final predicate
checks actual predictions against all 18 declared competitors, so geometry that
masks a nominal witness is rejected. Placement retries are bounded at 256 and
failure raises explicitly. No exhaustion was observed in the retained checks.

Odd indices use a 75% ordinary profile component: a random 10/11/12 square,
3/4-cell prototype, and two distinct codes on 10x10 or three on 11/12. This supplies
canonical dimension/palette support without replaying any canonical arrangement.
The remaining 25% of odd indices draw the full broad domain with difficulty
weights. The overall default mixture is therefore 50% teaching, 37.5% ordinary
canonical-profile component, and 12.5% broad; these are design probabilities,
not measured proportions. Exact overrides select broad sampling directly.

Three consecutive default demonstrations include a teaching scene; four
consecutive pairs include two. Thus each three-of-four query rotation retains a
teaching witness, provided assembly preserves accepted sequential draws. Actual
production lessons and independent rotations are checked separately. Duplicate
or invalid-pair rejection can advance sample indices; production evidence is
reported as measured, not inferred solely from requested residues.

## Limits and continuation

Six canonical-fitting shortcuts and twelve code-mapping errors are finite rival
families, not a proof of universal induction. Single-code substitutions do not
cover every simultaneous mapping change or arbitrary conditional rule. The
sampler deliberately does not add distractor prototypes, touching anchors,
multicolor shapes, holes larger than the small polyomino family, or arbitrary
rotation-angle semantics. Exact-override batches are research probes and need
separate lesson checks before use as training curricula.

The Python contract predictions are not label authority. Racket supplies all
retained generated labels, and an independent coordinate implementation checks
both reference and rival parity. See workspace/semantic_probe.py,
workspace/code_mapping_audit.py, workspace/replay_baseline.py, and the review
packet's REVIEW.md, DECISIONS.md and RESULTS.json for source-bound evidence.


## Maintainer overlap resolution, October 3

Selected exact v2.1.0 from review-da130648b0bc2752 over earlier reviewed v2.0.0.
Earlier source, notes and tests are retained in workspace/history/v2.0.0/.
The new review expands the mapping-rival family and lawful clipping/union
domain. Reported104 tests and2,196 query checks are retained, not newly rerun.
## Current reviewer considerations

Source SHA-256: `704565e2cac3d04a427b95e0550d6461d948626144a5eb9598968a60554d1e58`.

# Decisions for 531e65dffc0a v2.1.0

All decisions concern the assigned generator and its task-local review tools. The canonical program and task authority remain unchanged. Finding IDs match REVIEW.md. Baseline source is 1e23bb1c7e683034cf28ac6c354b9b3e8a9f43ef3310d8244a82d08fbb1c03bb; final generator is 704565e2cac3d04a427b95e0550d6461d948626144a5eb9598968a60554d1e58.

## D1 — Keep the actual rule and make its operational domain explicit

The reference takes a prototype shape, interprets isolated colored markers as rotation codes, and paints normalized rotated stamps on a fresh background. Same-color overlaps merge; individual out-of-bounds pixels clip; a stamp may repaint the source's old location; an empty bounding-box corner remains meaningful. These behaviors are supported by the canonical program and independently checked official outputs, including the six hand witnesses in checks/semantic-review/v21-witnesses/.

The sampler remains a one-prototype task with one monochrome 4-connected component and isolated single-cell anchors. The authority can have behavior outside this narrower domain, but introducing distractor objects, ties or additional marker semantics would change the teaching problem. I rejected that expansion because it is unnecessary to repair R1–R4 and would need its own ambiguity analysis. Prototype colors exclude 0 and marker colors 2..5, so source and marker roles are unambiguous within the declared domain.

The original notes did not explain historical domain choices. No unintegrated earlier review was used as measurement of this baseline.

## D2 — Honor every advertised exact control (R1)

| Control | Final accepted domain | Pixel observation |
| --- | --- | --- |
| grid_h | Integer 8..18 | Row count |
| grid_w | Integer 8..18 | Column count |
| proto_size | Integer 2..6 | Number of prototype-colored pixels |
| n_anchors | Integer 1..6 | Number of marker pixels |
| proto_color | 1, 6, 7, 8 or 9 | Prototype color |

These axes use public keyed draws, strict domain/type validation and an observable return contract. Non-null overrides select the broad branch before draw options are chosen. Unknown keys fail; bool does not stand in for an integer; unsupported values do not silently fall back.

Shrinking the public domain to the teaching branch would evade rather than repair the original ignored-control behavior. Silent clamping or fewer returned anchors would likewise misstate the caller's request. The full Cartesian domain is supported constructively, while the official override check supplies finite evidence: 599 cases × 3 bands × 30 seeds = 53,910 accepted draws with zero findings. That census is not an exhaustive enumeration of every possible seed.

The first repaired color metadata used a list where the shared contract expects a pipe-separated declaration. This produced actual after-phase failures, preserved under checks/after-v1/. The corrected type=color and valid=1|6|7|8|9 representation preserves exact behavior.

## D3 — Use finite shapes and capacity-backed anchor placement

The broad branch samples cached, deterministically ordered fixed polyominoes of size 2..6. It includes symmetric and asymmetric shapes. This finite construction avoids a random-walk growth loop that might keep retrying and gives exact requested area without constraining every scene to an L or other memorized silhouette.

The smallest 8×8 canvas has 64 cells. Six prototype cells exclude at most 30 candidate anchor cells when their four-neighbor neighborhoods are included. Five already-placed anchors exclude at most 25 more. Thus at least nine cells remain available when placing the sixth anchor, even under the loose union bound. Actual overlaps among exclusions only improve capacity. Anchor count is never shortened after a failed search.

The teaching branch has finite geometry searches and at most 256 layout attempts. Exhaustion is explicit. No retained final check exhausted it, but finite empirical success is not proof of success for every random stream; a future exhaustion should be investigated with its seed, not hidden by returning a weaker scene.

## D4 — Validate the declared scene rather than the generator's favorite layout (R2)

The validator rejects nonrectangular grids, invalid integer colors, missing anchors, missing or too-small source shapes, disconnected prototype pixels, multiple source colors and anchors touching another nonzero cell by an edge. It accepts every canonical input.

It intentionally does not ban clipping, output overlap, source-footprint overlap, empty bounding-box corners or small lawful hand witnesses. Restricting validation to the sampler's 8..18 bounds would incorrectly make the small semantic counterexamples disappear. Validation acceptance and sampler support are reported separately: the 5×5 yellow witness is lawful under the rule and accepted by the validator, while the actual sampler emits grids of at least 8×8.

## D5 — Teach the geometry rivals at lesson level (R3)

Six simple rivals independently fit all three usable canonical pairs: yellow_identity, suppress_clipped_stamps, shift_stamp_to_fit, xor_overlap, erase_source_after_stamping and absolute_source_offsets. The first is especially compelling because the only canonical yellow example uses a 180-degree symmetric S tetromino; yellow-as-identity therefore produces the same canonical output.

I rejected two insufficient responses: adding only a rare standalone witness, and merely asserting that a witness appears often in individual samples. A lesson can still supply three uninformative demonstrations followed by a query that needs the missing distinction. The baseline retained labels demonstrate that problem: the full final rival registry produces 80/183 ambiguous linear windows and 322/732 ambiguous cyclic query choices on the medium comparison set.

Default even sample indices instead produce asymmetric teaching scenes with visible geometric distinctions. Candidates must differ from every declared lesson rival in actual output pixels. This protects against clipping or union masking erasing a nominally present witness.

## D6 — Add all four rotation codes after a concrete failed intermediate repair (R4)

The first three-anchor design passed the original six-rival checks and the battery. An independent posthoc code-mapping audit then found a gap: some lessons omitted a code from all demonstrations but used it in the query. Medium results were 37/183 ambiguous linear windows and 159/732 cyclic query choices; easy was 39/183 and 160/732; hard was 37/183 and 157/732. Source 3d5acb565e4eb85a561c32a3a507d0a7f6f09e690eebc22fceef1951d7d2837d and the actual counterexample remain retained.

In the first recorded medium cyclic failure, seed 0 and base window 0 use demo indices 2, 3 and 0, none containing code 2, while query index 1 contains it. Treating code 2 as code 3 agrees on all demos but changes zero-based query pixels (6,4) and (6,5). This is a reproduced teaching defect even though the official labels themselves are correct.

Version 2.1 adds the missing fourth anchor with a fully visible stamp disjoint from the existing stamp support. It checks all twelve code_C_as_D substitutions for C,D in 2..5, C≠D, in addition to the six geometry rivals. A candidate that nominally contains all codes but still masks one substitution fails acceptance. Focused tests implement recoding independently instead of asking the generator to judge itself.

These twelve substitutions are lesson competitors; most do not fit every canonical pair. The canonical-fit table is measured and retained. The eighteen names include the duplicate yellow_identity = code_4_as_2. I do not claim universal identifiability or coverage of every coordinated multi-code change.

## D7 — Preserve canonical-profile support without copying canonical examples

The teaching branch uses square 11/12 canvases, asymmetric 4..6-cell prototypes and four different codes. An ordinary profile component on odd indices uses a 10/11/12 square, 3/4-cell prototype, and two different codes on 10×10 or three on 11/12. Its random shapes and placements are not canonical scene replay.

Odd indices choose that component with probability 3/4 and the broad branch with probability 1/4. The resulting overall design proportions are 50% teaching, 37.5% ordinary profile, 12.5% broad. Rectangular defaults occur through the broad component; exact overrides can request the full dimension domain directly.

Uniform broad defaults were rejected because merely including canonical shapes/palettes somewhere in a large domain did not reliably satisfy the canonical-profile floor. Teaching-only defaults were rejected because they eliminate ordinary two/three-anchor tasks and many simple/symmetric shapes. The mixture gives positive ordinary support while retaining broad probes and reliable demonstrations.

Final profile-floor evidence is 5/20 easy, 11/20 medium and 10/20 hard exact matches for size/palette profile. This is a floor measurement, not distributional equality with the three canonical examples. Difficulty affects dimension preferences only in the broad branch; most default scenes are shared across labels. No strong difficulty separation is claimed.

## D8 — Test actual assembly and cyclic query choices

Every three consecutive default scenes includes an even teaching scene. Every four consecutive scenes includes two, so any three-of-four demonstrations retain at least one. This argument relies on accepted sequential draws; materializer rejection or deduplication may advance indices.

Accordingly I retained both production and independent evidence. Production materializes 100 lessons per band with period 2 and balanced starting residues, using 1,200 unique inputs total; all declared competitors are refuted. Independent probes use seeds 0/1/17 and indices 0..63 per band, check all 183 sliding windows and all 732 cyclic query choices per band, and use official Racket labels. The independent cases have 241 globally distinct grids, not 576; overlapping windows are not independent draws.

Explicit-override collections bypass the schedule and carry no teaching promise. They should be run through separate lesson checks before curriculum use.

## D9 — Keep the reference independent from contracts and tests

Racket remains label authority. The generator's Python predictor supports executable semantic contracts but does not replace official labels. semantic_probe.py obtains labels using the supported public apply command, independently checks reference predictions and discovers the actual CANONICAL_SHORTCUTS/LESSON_COMPETITORS declarations. code_mapping_audit.py exposes undeclared mapping gaps using retained official labels. replay_baseline.py separates original input-source identity from the current rival-source identity.

The probe initially needed mapping-name support after the registry expanded; that compatibility concern was fixed before final v21 reports were accepted. Final independent reference, generator predictor, validator and rival-parity mismatches are all zero. Earlier tool versions and intermediate results remain retained.

## D10 — Match the official test environment (R5)

Task-local tests are explicitly invoked; root pytest does not discover them. Ordinary pytest initially hid a sibling-module import dependency, while the official stage uses --import-mode=importlib. The tests now load sibling support relative to Path(__file__) and register the module explicitly, preserving portable layout.

An isolated child also lacked pytest because user-site packages are disabled. A packet-local interpreter exposes the installed testing dependencies; this changes no shared source and is excluded from the return. Final official task tests pass 104/104, and the one generic repository test affected by the same environment issue passes on a targeted retry. The original generic result (271 pass, 1 fail, 3 skip) is preserved and is not rewritten as a full-suite pass.

## D11 — Preserve failures and make future checks reusable

Every actual failed repair/test iteration, both solve records and both audit witnesses are retained. The final exposed solve was prepared after the generator stabilized; the unattempted earlier preparation is explicitly archived with its old hash.

Large JSON reports are compressed byte-for-byte with an original-path/size/SHA mapping and a stdlib-only restoration tool. This follows the packet's explicit compression provision while keeping the delta small. Installed environments, duplicate repository trees and private query labels are excluded. The source patch is replayed against a fresh original extraction before acceptance, so final delivery does not depend on the working directory's accumulated state.
