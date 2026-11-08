# Final independent census: cc8c719680e6 v2.2.0

Generator SHA-256: `cce7ec4c8d4b5b951816f73467aae8539d2e3364b88d2694a889be2fd2a744c5`.
Canonical Racket rule: `8f9e53b42241`.
Baseline SHA-256: `fcb5e074619f09fc2cdbac112de79105426765a444efe592284d15f071d52a78`.

The repaired source refuted both independently implemented connectivity rivals
in every one of the same 3,000 four-demo windows used for the baseline review.
It also refuted every actual declared rival in every window. No baseline file
was overwritten; all final artifacts are in this `final/` directory.

## Identical population, improved lesson coverage

The direct-generator census uses 1,000 windows per difficulty, with seed
`810000 + 10000 * band_index + repetition` and indices `4 * repetition` through
`4 * repetition + 3`. It contains 12,000 inputs. Aggregate output comparisons
use the independent audit implementation; the separate reference calibration
below checks selected cases against Racket. This is a generator-level census,
not a replacement for the root's production lesson census.

| Rival | Baseline windows surviving all demos | Final windows surviving all demos | Final individual discriminators |
|---|---:|---:|---:|
| Same-color 8-connected components | 2,983 / 3,000 | 0 / 3,000 | 3,000 / 12,000 |
| Color-blind 4-connected components | 2,434 / 3,000 | 0 / 3,000 | 6,000 / 12,000 |

The final probe discovers `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and
`CANONICAL_SHORTCUTS` dynamically. It retains all 25 namespace-qualified entries,
which refer to 11 distinct rival functions. Every entry has zero surviving
four-demo windows in each band. The producer's two connectivity rivals matched
the independently implemented rivals on all 12,000 inputs. There were no rival
execution errors, structural failures, or missing required contacts.

All 144 exact override combinations were generated with the same seeds and
indices as the baseline override census. They passed self-check, exact observable
axis checks, and the independent/declared rival crosscheck. As before, this is
one draw per override combination, not an exhaustive seed claim.

Strict canonical support remained exactly 2,000 of 4,000 inputs (50%) per band.

## Reference calibration and regression directions

The public `arcpuzzles apply` command executed 64 retained final inputs using
canonical Racket. All 64 were valid and matched the independent outline. The
calibration includes:

- 36 ordinary generated inputs spanning all scheduled profiles and difficulties;
- 10 grids from the two previously ambiguous consecutive lessons, regenerated
  using v2.2.0 at their exact original seeds and indices;
- 18 exact override examples selected to cover additional axes and morphology.

By construction branch, the batch contains 25 canonical-profile inputs, twelve
four-component contact inputs, seventeen three-component contact inputs, and ten
noncanonical two-component inputs. Both orthogonal contact directions and both
diagonal slopes appear in the calibration.

Both regenerated lessons now refute every declared rival within their four demos,
and the final lesson hook returns `[]` using their Racket labels. Their replays
remain easy seed 810004, demos 15–18/query 19, and easy seed 810078,
demos 311–314/query 315.

The other regression direction was checked as well: when the new hook receives
the exact retained **old** demonstrations and Racket labels, it rejects both
lessons and explicitly identifies the two surviving connectivity rivals. This
confirms that the hook recognizes deficient evidence independently of the new
sampler's improved placements. See `baseline_lesson_rejections.json`.

## Diversity and geometric restrictions

Exact uniqueness was recomputed for both versions on the identical population.
Counts below are per difficulty, out of 4,000 inputs/outputs.

| Difficulty | Baseline unique inputs | Final unique inputs | Baseline unique outputs | Final unique outputs |
|---|---:|---:|---:|---:|
| easy | 2,112 | 2,110 | 2,044 | 1,918 |
| medium | 2,110 | 2,102 | 2,025 | 1,885 |
| hard | 2,112 | 2,109 | 2,034 | 1,908 |

The new contact requirement improves finite-lesson semantics at a measurable
cost in output diversity. Input uniqueness remains close to baseline. The
canonical slots retain their small fixed supports: 48 unique 7x7 inputs and 64
unique 9x9 inputs in each 1,000-input slot sample. The four-component generalized
slot produced 1,000 unique inputs per band, with 998–1,000 unique outputs. The
three-component slot produced 990–998 unique inputs and 773–808 unique outputs.

The main remaining restrictions are explicit:

1. Every natural three-component input has a 5x5 foreground bounding box. Its
   objects form a transformed, translated contact cluster. All 3,000 such inputs
   exhibit a same-color diagonal contact; 1,503 have the down-right slope and
   1,497 the down-left slope.
2. Four-component inputs keep a three-object contact cluster but place the fourth
   component freely in a disjoint 2x2 footprint. Their foreground spans cover
   many dimensions rather than remaining fixed at 5x5.
3. All 6,000 generalized inputs contain both horizontal and vertical contacts
   between different colors. Far-separated three- and four-component scenes are
   no longer a natural branch. Separated two-component scenes remain available.
4. Generalized primary shapes still span 3x3; their cell counts now vary between
   five and six. Secondary shapes remain 2x2 L-components. Natural generation
   has six joint morphology profiles, up from four, but still omits canonical
   training pair 1's distinct joint morphology.

These are bounded distribution restrictions, not newly found reference-label
failures. The measured repair resolves the two reported lesson defects. The
remaining finite template support should remain visible in the handoff rather
than being described as unrestricted geometry coverage.

## Files and exact commands

- `final_probe.py`: reusable census and reference comparison. Requires explicit
  `--generator` and `--out-dir`; census mode refuses preexisting core output
  artifacts. All JSON writes use exclusive creation.
- `reviewed_generator.py`: exact evaluated v2.2.0 source snapshot.
- `result.json`: source/probe/helper hashes, exact population, all declared-rival
  counts, uniqueness, contact orientations, geometry, and override results.
- `inputs.json` and `input_metadata.json`: 64 calibration inputs and replays.
- `racket.json`: public reference execution receipt, input/output hashes and labels.
- `reference_verification.json`: 64 comparisons and Racket-backed lesson results.
- `baseline_lesson_rejections.json`: the new hook rejects both fixed old lessons.
- `commands.json`: exact command argument arrays, working directories, exit codes,
  and result paths for the census, public reference execution, and verification.

The three recorded main commands all completed with exit code 0. Run from the
packet root; choose a new output directory for any new census run. Do not reuse
the retained `final/` output directory.

```bash
python3 run_with_racket.py python3 generators/cc8c719680e6/workspace/distribution_review/final/final_probe.py --generator generators/cc8c719680e6/generator.py --out-dir generators/cc8c719680e6/workspace/distribution_review/final
python3 run_with_racket.py python3 -m arcpuzzles apply cc8c719680e6 --input generators/cc8c719680e6/workspace/distribution_review/final/inputs.json --out generators/cc8c719680e6/workspace/distribution_review/final/racket.json
python3 run_with_racket.py python3 generators/cc8c719680e6/workspace/distribution_review/final/final_probe.py --generator generators/cc8c719680e6/generator.py --out-dir generators/cc8c719680e6/workspace/distribution_review/final --verify-reference
```

The commands above are the commands actually exercised, not instructions to
overwrite those paths. The census source remained unchanged during measurement,
and the public apply receipt names the same generator source hash.
