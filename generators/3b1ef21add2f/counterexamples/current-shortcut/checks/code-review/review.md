# Independent code review: 3b1ef21add2f

## Verdict

**GO. No blocking correctness, contract, or witness-integrity findings remain on the final candidate.** This verdict covers the bounded teaching generator and its declared seven-rival contract. The main battery and the runner's 300-lesson census are separate gates owned by the parent reviewer; this review does not claim their results.

The reviewed final `generator.py` is SHA-256 `5e7c468218a1b11c8c73e5d2d00af64889245fd02f6672975401a2764c0b5965`, version `3.0.0`. Its canonical Racket rule hash is `200a2c36d86e`. The source did not change during the final probe. No repository commits are used as evidence.

The first repaired candidate reviewed here was SHA-256 `88e035b21672c2223a2c0f4e8a25f8dac51d9e0a266f4606b84cbe5ebbe95d9b`. The parent supplied the pre-repair source hash `934fe2bb8aa53ad9e4edc3a954c0aca912c6ac993c22db3f7a57c8c637838e81`; this reviewer did not independently rerun that baseline.

## What was checked

The selected generator, its tests, the relevant grid/object/context helpers, the public Catalog view of its canonical pairs and Racket rule, and `docs/SEMANTIC_GATE_CONTRACT.md` were reviewed. Selected source and tests were not edited. Authored `solve` and `solve-blind` artifacts were not inspected. All review files and receipts are under `WORK/checks/code-review/`.

The probes use independent coordinate loops for original-input window membership, independent D4 transformations, and an independently implemented graph 2-core. They do not import the task-local test oracle. The private tile enumeration deliberately covers a superset of public tile choices; it is a finite geometry check, not a replacement for public runner or override tests.

| Reviewer-executed check | Result | Evidence |
|---|---:|---|
| All simple tiles for counts 0..4 and all rich tiles for counts 0..8, three ring-tail choices, eight foreign-square configurations, and eight orientations | 1,768 cases; zero failures | `probe-v2.json`, `cases-v2.json` |
| Each default-rich geometry refutes every named rival and fires every witness | 1,008 cases × seven rivals and six witnesses; all pass | `probe-v2.json` |
| Witness-to-rival implications on all binary 3×3 red patterns with independent distractors | 920 claims across 512 patterns; all pass | `probe-v2.json` |
| Four-pair holdouts over every period-3 starting residue and all four difficulty bands | 48 holdouts; all seven rivals refuted by remaining demos | `probe-v2.json` |
| Fresh-process deterministic replay with hash seeds 0, 1, and 35791 | Identical digest for 24 default draws per process | `probe-v2.json`, `replay` field |
| Returned-grid mutation and intervening unrelated calls | Exact replay retained | Same replay receipts |
| Canonical pairs | All three match the independent original-window rule; all declared canonical shortcuts fit them; all inputs pass the strict hook | `probe-v2.json` |
| Literal ring-plus-square counterexample executed by public Catalog.apply | Rule confirmed; graph-core rival wrong on eight cells | `racket-v1.json`, `counterexample-v1.json` |

The final probe command was `.venv/bin/python checks/code-review/probe_v2.py`, run from `WORK`, exit code 0. Exact commands and nested replay process outputs are retained in `commands-v2.json` and `probe-v2.json`. The supplied 125-test result and full 3,600-combination override test are parent-reported; this reviewer did not repeat them.

## Correctness and geometry

The immutable Racket rule creates a new grid and tests every candidate window against `g`, the original input. It considers the four possible 2×2 top-left positions covering each red cell and preserves cells outside their union. That directly supports simultaneous recoloring and overlapping-window counting.

The generator's `n_windows` is an observed count of original complete red neighborhoods, including overlaps. Its row-length construction has exactly the requested primary count: adjacent rows contribute `min(width_a, width_b) - 1` windows, and the one-cell primary tail contributes none. The separate square contributes one when the requested count is at least two. The count-one special case correctly retains one primary square while using an incomplete secondary component.

The new hollow ring occupies rows 4..6 and columns 4..6 before orientation. Its missing center prevents every potential 2×2 in that 3×3 box. Either optional cell at `(4,3)` or `(3,6)` remains a one-cell tail and does not complete another window. The ring and either tail remain separated from the primary red component and the secondary square. The foreign square lies at rows 0..1 and columns 5..6, with a nonred color. All of these claims held across the finite enumeration, including the 7×7 boundary. Translation and D4 transforms preserve counts and component separation.

The exact integer draw helper checks `type(value) is int` before conversion. The generator explicitly rejects unknown and obsolete keys, widens requested dimension/window bounds to the documented override range, and treats a known key with `None` as omitted. The source has no rejection loop or silent clipping path. The public joint-axis matrix remains a separate supplied test rather than an inference from this geometry argument.

`self_check` consistently implements the stated teaching subset: a rectangular exact-integer digit grid with dimensions 1..30, colors 0 and 2 present, at least two orthogonal red components, and an uncovered red cell whenever windows exist. It accepts no-op teaching inputs. Its narrower sampling domain does not incorrectly claim to define the total Racket rule domain.

## Rival integrity and the resolved review finding

The first repaired candidate supported a new shortcut: iteratively remove red graph vertices with fewer than two orthogonal red neighbors, then recolor the remaining vertices. This graph 2-core rule matched all 2,344 enumerated initial tile variants and all three canonical pairs. A 7×7 input containing a hollow 3×3 red ring plus a separate 2×2 red square passes `self_check`, but the correct rule changes only the square. Public Catalog.apply confirmed that the rival incorrectly changes all eight ring cells. The exact input, correct output, wrong output, and cell differences are retained in `counterexample-v1.json` and `racket-v1.json`.

This was initially classified as a nonblocking distribution limitation, not a violation of the specified input/output rule. The final candidate nevertheless closes it: every rich tile contains the ring, `red_two_core` is now a declared canonical shortcut and lesson competitor, and `red_cycle_without_window` explicitly claims that rival. All 1,008 default-rich variants distinguish it. The implementation of the rival also agrees with the independent graph implementation on the full final tile enumeration and the 512 adversarial local patterns.

The six original rivals remain substantively distinct and are still refuted. Attached red cells distinguish component-wide or exact-component rules; overlapping primary windows distinguish the in-place scan; unequal window-bearing component sizes distinguish the largest qualifying component rule; a nonwindow red component distinguishes mass-based recoloring; and the nonred square distinguishes color-insensitive square detection. The new ring provides the seventh distinction without deleting those contrasts.

The witness mappings satisfy the semantic contract. In fact, the probes verify that **every** rival listed for each firing witness disagrees on the checked input, which is stronger than the contract's required “at least one.” The hooks and rivals were pure on the checked inputs, and witnesses returned actual booleans.

## Schedule change

The final candidate uses period 3: anchor, rich, rich. This supersedes the first candidate's exact period-4 mix of one anchor and three rich scenes. The parent explicitly authorized that revision to provide more margin for the canonical profile floor. Source invariants and the revised distribution tests express the new contract.

Every four consecutive positions now contain either one or two anchors and at least two rich scenes. Holding out any one pair leaves at least one rich demonstration. Because each rich demonstration refutes all seven named rivals, every such holdout has the needed finite-rival evidence. The 48 concrete holdouts verify this for all start residues and difficulty bands. This review does not assess whether the revised schedule passes a particular finite-sample profile-floor run; that is the parent's main battery result.

## Nonblocking limitations and documentation boundaries

The distribution remains deliberately small in topology. All objects inhabit one transformed 7×7 motif, with extra dimensions supplied by padding and translation. Rich scenes have exactly three red components. Window-bearing primary bodies come from a short row-length table; the nonwindow ring has zero or one attached cell. Default scenes contain no input color 3 and only one nonred distractor color. Counts 0, 1, and 2 in rich construction are reachable by override, while default rich draws have at least three windows.

The period-3 branch allocation is fixed. Rotations, reflection, placement, dimensions, count, ring-tail choice, and distractor color provide variation, but they do not establish full support over accepted teaching inputs or the total rule domain. Seven named-rival tests cannot prove unique identification against arbitrary alternative programs. No further rival search was performed after the parent asked to keep this review bounded.

The code now states the bounded grammar and finite-rival nature of `lesson_identifiable`. Final notes and the repair summary should retain those limits and use the period-3 guarantee, rather than the superseded exact four-draw ratio or “red tetromino” description. Those standalone notes and summary files were outside this review's permitted read scope; their synchronization is not asserted here.

There are no remaining blocking findings within this review's scope. The authoritative main battery, relocated runtime validation, production lesson census, and subsequent evaluation remain separately attributable evidence.
