# Review notes — f99263121e8a

Assignment `review-fe2f6c8ac068e5e6`; source version 4.2.0.

## Rule and first-round repair

The predecessor described three fixed-bank objects but actually sampled 2–6
random polyominoes. It excluded touching bounding boxes, repeated colors and
tied left edges, silently ignored several declared controls, and omitted a rule
hash. Its negative fixture called equal-leftmost ordering ambiguous even though
the existing comparator breaks ties by top row. The canonical held-out example
requires retaining foreign pixels in raw bounding-box crops.

The 4.1.0 repair kept the Racket authority unchanged, validated controls and
cell types, bounded outputs, made placement complete-or-fail, restored canonical
morphology, and added a rotating five-demo curriculum. It explicitly taught raw
cropping, floor centering, left-edge ordering, repeated colors and diagonal-only
same-color contact.

## Second-round adversarial repair

A larger rival search showed that the 4.1.0 schedule still admitted plausible
query-changing alternatives: sort by top/color/area, reverse the object order,
break equal-left ties by bottom, use ceiling rather than floor centering, or use
zero/two separator rows. Six regressions were added first and failed against
4.1.0. Version 4.2.0 then made three targeted changes:

1. `order_conflict` is a canonical-like profile whose intended left order
   conflicts with top, color, area and reversed-left orders.
2. `crop_overlap` now combines raw-crop contamination, different-color contact,
   and a lawful equal-left tie in one exact motif.
3. `wide_narrow` now creates odd horizontal padding and conflicting right-edge
   order, separating floor centering from ceiling/left alignment.

Diagnostic rendering now models fourteen named rivals, including zero- and
two-row separator variants. The shared semantic gate groups related rivals to
avoid duplicate Racket calls; `workspace/rival_search.py` still scores and
records each rival independently. No production label is taken from those
Python mirrors.

## Evidence and limitations

The task-local suite has 56 tests. The retained red run has 6 failures against
4.1.0; the green run passes all 56 against 4.2.0. The twelve-stage generator
battery is green. A 300-seed × 3-band declared-rival scan generated 13,500
overlapping examples and found no surviving five-demo window or rival without a
witness. A separate 30-seed × 3-band compound scan enumerated 503 combinations
of extraction, crop masking, ordering, alignment and separator width; none fit a
complete five-demo window. An exhaustive override stress exercised 48,000 cases
with no failure. Final source-bound census and Racket counts are recorded in the
review return rather than hard-coded here.

The rival library remains finite. The guarantee applies only to consecutive
default examples using one fixed seed and difficulty; forced single textures,
shorter lessons, arbitrary nonconsecutive sampling, or downstream reshuffling
can discard it. Seed outputs changed across both version boundaries. Two of
five default draws intentionally stay canonical-like, reducing hard-band
complexity for those anchors.

The repository's synthetic solve-fixture failure was traced to a test library
that omits `src/arcpuzzles` even though its generated packet launcher imports
that source-bound API. A first global-fixture correction fixed that test but
broke the portable-packet test by pre-creating a directory it deliberately
copies; that rejected iteration is retained. The narrowed fixture-only diff
copies the API only in the solve-test packet helper and passes the focused test,
the whole solve-test module, the conflicting portable test, and the complete
166-test repository suite. The assigned task patch does not edit shared tests;
maintainers can evaluate this separate proposal independently.

`workspace/review_probe.py` reproduces the source-bound census and the two
assigned audit-only findings. `workspace/rival_search.py` searches teaching
windows against the full declared rival set. `workspace/relocation_probe.py`
checks a moved runtime in isolated Python. These are evidence tools, not label
authority. Keep them closed during any independent Python solve.
## Current reviewer considerations

Source SHA-256: `332417ad3aa8d4080764ea505fc476ef72311365efe1613ed8729e19d4f84d83`.

# Distribution, adversarial-search, and fixture decisions

Task `f99263121e8a`; assignment `review-fe2f6c8ac068e5e6`.
Final version 4.2.0; generator SHA256
`332417ad3aa8d4080764ea505fc476ef72311365efe1613ed8729e19d4f84d83`.
The unchanged Racket authority, not the diagnostic Python mirrors, defines
labels.

| ID | Selected choice | Alternatives considered and why rejected | Evidence and limit |
|---|---|---|---|
| D1 | Preserve the canonical Racket rule and rule hash. Interpret objects as monochromatic 4-connected components, order by `(left, top)`, retain raw bbox contents, insert one blank row, and floor-center. | Editing the rule to match the old restricted generator, masking foreign pixels, or treating color as identity. Rejected because canonical examples and held-out crop semantics require the existing rule. | 5/5 canonical and 240 generated comparisons match Racket; canonical bytes and rule hash are unchanged. |
| D2 | Retain first-round truthful controls, exact component counts, complete-or-fail placement, malformed-grid checks, and output bounds. | Silent no-op overrides, clamping, or returning partial scenes. Rejected because they make the declared distribution false. | 600-case explicit matrix, 48,000-case stress, 56 tests, and override battery stage pass. |
| D3 | Keep two canonical-like anchors in every five-example cycle. | Purely random generalized shapes or literal replay of public grids. Random-only loses morphology; replay risks memorization. | Strict canonical predicate: 360/900 final versus 0/900 baseline. Anchors vary position, palette, and roles rather than copying stored arrays. |
| D4 | Replace one canonical slot with `order_conflict`, a canonical-like scene whose left order conflicts with top, color, area, and reverse-left order. | Add more independent random scenes and hope conflicts occur. Rejected because a short lesson needs deterministic semantic coverage. | Four order rivals are directly refuted; the regression failed against 4.1.0 before passing in 4.2.0. |
| D5 | Make `crop_overlap` a compound exact motif: raw-crop contamination, different-color touching, and equal-left components with distinct top rows. | Separate those properties across rare random examples. Rejected because five demonstrations would not reliably carry all clauses. | `mask_each_component`, `merge_touching_colors`, and `left_then_bottom` disagree on this profile. |
| D6 | Make `wide_narrow` use widths four and one with odd padding and a right-edge conflict. | Widths whose padding difference is even, or a profile that tests only alignment. Rejected because floor and ceiling centering can otherwise coincide. | `left_align`, `ceil_center`, and `sort_by_right_edge` all disagree; exact unit tests cover each. |
| D7 | Retain same-color diagonal singletons as an explicit default profile. | One object per color or eight-connectivity. Rejected as unfaithful shortcuts that fit all canonical pairs. | The final census emits 180/900 such witnesses and verifies the saved counterexample against Racket. |
| D8 | Expand the declared rival library from six to fourteen, but group related semantic witnesses in the shared gate. | One Racket evaluation per rival on the same input. Rejected as redundant; grouping preserves a firing witness while task-local reports still score rivals independently. | 300-seed × 3-band scan has zero surviving windows and zero missing witnesses; census stores 14 Racket-verified exact counterexamples. |
| D9 | Add a finite 503-candidate compound search over extraction, masking, ordering, alignment, and separator width. Fail if any candidate fits a complete five-demo window. | Only compose the fourteen named hooks informally, or claim the named list is exhaustive. Rejected because cross-axis combinations can survive even when every one-axis alternative has a witness somewhere. | 30 seeds × 3 bands: zero candidates fit a complete window. This product family is still finite and not a uniqueness proof. |
| D10 | Keep `EXAMPLES_NEEDED=5` and a deterministic periodic cycle. | Shorter lessons or independent sampling. Rejected after 4.0.0 and 4.1.0 evidence showed per-example diversity does not imply lesson identifiability. | 180 census lessons and all contiguous phases in the 300-seed scan pass. Forced textures, reshuffling, and fewer than five examples lose the guarantee. |
| D11 | Return the shared fixture correction as a separate proposal, not part of the generator patch. | Modify global `conftest.py`, or smuggle a shared-test edit into an allowed task path. Global fixture modification caused a new portable-test failure; scope escape would violate the assignment contract. | Rejected v1 full suite: 165/166. Narrow v2 proposal: 166/166. `patch-application.json` confirms it is outside `patches/source.patch`. |
| D12 | Bind every final receipt to the exact generator hash and retain red/rejected evidence. | Rename failed logs as green, delete unsuccessful hypotheses, or infer correctness from a source snapshot. Rejected because it hides causal evidence and allows stale receipts. | Patch verifier checks all final report hashes, exit codes, exact-byte application, unchanged authority, and both fixture iterations. |

## Why five profiles rather than more randomness

The goal is not maximal raw variety per draw. It is a compact teaching set that
contains the clauses needed to identify the rule. A five-example cycle gives one
instance of each semantic role at every start phase while still allowing random
palette, translation, extra components, and band-dependent counts. Adding
unstructured diversity could increase unique-input counts yet reintroduce
ambiguous lessons. The final distribution therefore accepts some repetition:
297/300 unique inputs per band, with canonical-like anchors responsible for the
three repeats.

## Measurement discipline

The final census uses seeds 0–299 and index `seed % 11` in each band: 900 calls.
Uniqueness is reported per band, not globally. Racket authority checks are
counted separately from mirror metrics: 240 generated, five canonical, and
fourteen counterexample calls, 259 total. The 13,500 examples in the declared
rival scan overlap across windows and are not independent samples. The 180
lesson cases use seeds 10000–10059 and one five-demo-plus-query lesson per band.
The compound scan uses seeds 0–29 and all start phases; its 503 candidates are a
fixed enumerated product, not all computable rules.

The baseline census has `passed=true` because execution and sampled Racket parity
succeeded. It is not a semantic-coverage pass: strict canonical support is
0/900, and several important rivals have no witness. Likewise, an audit report
can pass because it successfully reproduces a defect. Claims in this return
therefore name the metric, source hash, denominator, and authority boundary.

## Rejected fixture patch and final proposal

The first shared fix added `repo/src` to the global `library` fixture. That made
the solve launcher importable but pre-created `library/src`, violating the setup
assumption of `test_relocated_full_packet_round_trip`; the full suite stopped at
165 passed, one failed. The final proposal moves ownership to the consumer that
needs it: the solve-test `packet()` helper copies only `src/arcpuzzles`. This
leaves source-free fixture semantics intact for other tests and passes all 166.
Both diffs and both full-suite logs are retained.

## Remaining uncertainty

The finite rival libraries do not prove unique human or model inference. The
schedule guarantee does not survive arbitrary downstream shuffling, fewer than
five examples, or forced single textures. The visible Python solve is not blind
because earlier rule exposure is declared, and masked correctness is unknown.
No model training, leaderboard gain, approval, or training-safety status is
claimed.
