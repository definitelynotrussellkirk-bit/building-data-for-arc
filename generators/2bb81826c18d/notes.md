# Current notes: 2bb81826c18d — version 2.1.0

## Rule and domain

One to four separated solid monochromatic rectangles on zero background,
distinct nonzero colors, rectangle dimensions at least 3x3, canvas 10..24 in
each dimension. The canonical Racket rule preserves borders and erases even
checker parity relative to each rectangle's top-left interior. RULE_HASH
`b0e1d6662c7a` and all authority/approval files are unchanged.

## Current decisions

The old independent default sampler had 1/60 canonical-profile hits and could
produce three demonstrations fitting a thin-object-omission or canvas-column
phase shortcut before a distinguishing query. Default indices now cycle through
teaching / broad / teaching / canonical-profile. Three demonstrations plus one
query are intended. The two teaching rectangles jointly distinguish twelve
declared rivals; only skip_thin_rectangles claims full canonical fit. Raw
four-index windows retain a teacher under any one-pair holdout. Production
acceptance/rejection and rotation behavior have separate real-Racket evidence.

Profile support uses actual canonical height/width/count tuples with random
colors and geometry; a broad slot retains additional support. Any explicit
non-None override selects the prior constructive control path, so the default
teaching claim does not cover overridden lessons. Literal integer seed/index
validation rejects coerced types, with sample_index nonnegative.

Reversal during this review: profile geometry was initially substituted after
recorded draws; the full override gate exposed provenance drift. The final
sampler selects the feasible domain first, then records singleton dimension/
count draws and the actual teaching edge value. The corresponding failing and
passing observer regression is retained. Final source SHA-256:
`2ce12fb99622a5ea1e7958e036849171fd84b8903f0a64e4e063a59dfaf58fff`.

## Evidence and limits

Minimal task-owned counterexamples: `counterexamples/thin_3x3.json` and
`counterexamples/baseline_ambiguous_lessons.json`, bound to original source
`f4b85948212752aa24e5c08ff174cb850645663a6140f952eba2019154abf28b`.
The original recipes are historical; replay their saved inputs after version
changes. Tests use portable reviewer_support paths. Final retained return
reports 35 test items plus 170 subtests; profile 41/60 exact, 46/60 envelope;
300 real-production lessons / 1,200 rotations, no ambiguity against twelve
rivals, 1,196 unique inputs. Fixed seed 0 separately covers four start residues
per band: 12 lessons / 48 rotations. See the return's RESULTS.json and checks/.

Teaching geometry introduces deliberate size/position correlations. Broad
draws preserve alternatives, but this finite rival inventory is not proof of
universal induction; arbitrary overridden lessons and fewer demos may remain
ambiguous. No current review_index.json was present at this draw; no prior
audit was silently resolved.

## Proposed parametric extension

`workspace/parametric/` is a separate runnable prototype with period in {2,3}
and phase in range(period), canonical (2,0). It keeps object roles and border
preservation and uses zero-based interior coordinates. A >=5x5 demonstration
distinguishes all five settings. Exact Racket programs label all pairs.
35 episodes / 140 pairs / 140 parameter-rival checks and 35 deterministic
replays passed; canonical equivalence covers 8 records / 4 unique inputs.
Public challenges omit parameters, code and query labels. The ordered prototype
does not claim rotation safety, production registration or variant approval.

## Open blocker

The original packet's selected target-code copies differ in exact text from
canonical code. The final full battery passes 11/12 stages; authority_sync
remains failed, with execution parity passing. The two destinations are outside
this task's edit scope. The return includes the exact non-applied, hash-guarded
`checks/authority-alignment-proposal.json` for the maintainer. Approval is not
refreshed by these local checks.
## Current reviewer considerations

Source SHA-256: `2ce12fb99622a5ea1e7958e036849171fd84b8903f0a64e4e063a59dfaf58fff`.

# Decisions — 2bb81826c18d

## D1. Preserve the canonical rule and object roles

The selected Racket rule remains `b0e1d6662c7a`. Inputs contain one to four
separated solid rectangles of distinct nonzero colors on zero background.
Borders survive; the interior checker phase is anchored independently to each
rectangle's top-left interior cell. The canonical labels, authority files and
approval records were not edited. The existing rectangle validator already
accepts every supplied canonical input and remains the domain definition.
The rationale for the historical 10..24 canvas and 1..4 component limits was
not recorded in the empty current notes; those boundaries were retained.

## D2. Teach thin rectangles and coordinate anchoring

Baseline source `f4b85948212752aa24e5c08ff174cb850645663a6140f952eba2019154abf28b`
admits a natural shortcut: leave any rectangle narrower or shorter than five
cells unchanged. It fits all eight labeled canonical records, representing
four unique inputs. Real Racket execution confirmed a generated 3x3 witness
whose center must become zero, plus a complete ambiguous production lesson at
easy seed 2, start 0. A second real lesson at easy seed 11, start 0 fits a
canvas-relative column phase until the query. Retain
`counterexamples/thin_3x3.json`, `counterexamples/baseline_ambiguous_lessons.json`
and `checks/shortcuts/`.

Merely increasing the marginal frequency of thin or odd-position rectangles
does not ensure that a complete lesson teaches them. Default draws now use a
four-index schedule: teaching, broad, teaching, canonical-profile. A teaching
scene contains two designated teaching rectangles, with additional rectangles
when the selected profile requires them: A has height 3, even width, odd top and
odd left; B has even height, odd width, even top and odd left. Their dimensions
and legal positions vary. Together they distinguish all twelve named rivals.
Every four consecutive raw indices contain two such scenes, so any one-pair
holdout leaves a distinguishing demonstration. Three demonstrations and one
query are the intended assembly. Actual production rejections/duplicates were
checked through the shared census, separately from this raw-index argument.

Twelve rivals cover thin-object omission, canvas row/column/full parity,
opposite local phase, the three other corner anchors, stripes, whole-interior
erasure and identity. Only thin-object omission is declared a
`CANONICAL_SHORTCUTS` member; the other eleven do not claim full canonical fit.
The lesson hook reports finite rival ambiguity and never supplies labels.

## D3. Preserve canonical-profile support and broad variation

The baseline's independent dimension draws produced only 1/60 exact profile
hits and 12/60 envelope hits, with no exact hits in easy or hard. Default
profile-supported draws select real canonical (height,width,rectangle-count)
tuples by difficulty. Because colors remain distinct, rectangle count plus
one is the observable distinct-color count. The broad slot retains the old
difficulty-dependent dimension/count sampler; explicit controls retain its
full 10..24 range. The canonical slot can still produce the one-object
medium profile. Final measured support is 41/60 exact and 46/60 envelope,
with positive exact support in every band. Canonical inputs: 8/8 accepted.

`strict_canonical_like` explicitly means the original size/color envelope
inside the lawful rectangle domain; it does not assert that every sampled
rectangle has a canonical shape. Its 25% floor is exceeded in the retained
final checks. Keeping completely independent default dimensions was rejected
because it misses the measured profile gate. Restricting all draws to
canonical profiles was rejected because broad geometry remains useful.

## D4. Honor keyed draw provenance as well as explicit overrides

Seed must be a literal Python integer; sample_index must be a literal
nonnegative integer. Existing strict scalar override validation remains.
Signed integer seeds remain accepted; the defect was coercion, not sign.

An intermediate repair selected profile geometry after recording different
axis draws. The full override stage correctly caught this defect. The fix
chooses the feasible profile first, then draws dimensions/count from singleton
domains and the teaching edge value from `(False,)`. The public GenCtx observer
regression failed on the intermediate bytes and passes on the final source.
The intermediate source, full failing battery and red test remain retained.

Any non-None explicit override uses the existing constructive sampler, including
all exact dimensions/count/edge requests and palette/size-profile behavior.
This avoids silently ignoring caller controls. Default teaching guarantees do
not extend to arbitrary overridden lessons or fewer demonstrations; callers
must inspect the lesson result. Setting any one explicit control may therefore
change the default distribution of the remaining dimensions. This boundary
is deliberate and documented, not a claim of independent conditional sampling.

## D5. Parametric prototype: period and phase

The separate prototype under `workspace/parametric/` executes
`(ir + ic) % period == phase` in zero-based interior coordinates. Period is
2 or 3 and phase ranges from 0 through period-1: five settings total. `(2,0)`
is canonical. The parameter is chosen once per deterministic episode and is
shared by all demonstrations and queries. This changes the executed erasure
pattern while retaining the original object decomposition, borders, palette
roles and independent rectangle-relative reasoning.

A >=5x5 rectangle in the first demonstration distinguishes all five settings.
The exact emitted Racket, not a Python mirror, generates all labels and rival
predictions. Public challenge files whitelist demonstration input/output and
query input; they omit hidden settings, seeds, reference programs and query
labels. Tests preserve genuine initial failures and cover a naturally ambiguous
small demonstration, explicit parameter rejection, public/private isolation,
determinism, canonical equivalence and manifest integrity.

Bounded evidence: all five settings at seeds 0,7,19 and twenty seed-selected
episodes at seeds 0..19; 35 episodes, 140 pairs, 140 alternative-setting checks,
35 exact replays, zero measured ambiguities; 8 canonical labeled records / 4
unique inputs agree with original and prototype Racket. This remains a
**proposed prototype**, with ordered demonstrations, no rotation-safety claim,
no production registration and no variant/training approval.

## D6. Portable tests and unchanged frozen fixtures

The existing task-local test used a fixed parent-depth canonical path and a
private generator alias. It failed the public portable preflight before pytest.
That editable task-local file now uses reviewer_support. The stale separate
grounded-authority assertion is covered by the explicit authority-sync battery
stage, whose actual failure remains visible; it was not disguised as a pass.
Canonical-label assertions, distribution/override cases and invalid-scene
regressions remain. No frozen root fixture was edited. Final task tests report
35 pytest test items plus 170 unittest subtests, 205 JUnit cases, zero failures,
errors or skips. The full library's unrelated test suite was not run.

## D7. Authority alignment remains a maintainer action

The original packet's two selected target-code copies differ in exact text
from canonical program_solution, although token equivalence is certified by
the existing proposal tool and the authority stage's execution parity passes.
The task permits edits only within this generator; the destinations are under
shared/data/base/solutions/. Therefore `checks/authority-alignment-proposal.json`
contains the exact hash-guarded, non-applied patch. It changes selected target
text only and preserves archival raw_code. The final battery is honestly
11/12 stages passing, with authority_sync the sole remaining failure.

## D8. Limits, self-review and retention

Teaching scenes deliberately favor small rectangles, particular position
parities and separated zones. The broad and canonical slots keep other shapes,
colors, boundary contact and positions in support, but an untested
shape-conditioned rival could still exploit these correlations. Twelve rivals,
300 random production lessons and a fixed-seed schedule enumeration are finite
evidence, not a proof of universal induction or a new training admission.

No current review_index.json was present for the repair target; no historical
repair claim was substituted for a measurement. The two assigned audit targets
were findings-only and remain unchanged. Their prior evidence was used only as
a lead, with fresh public generation and independent Racket confirmation.
The blind and post-repair solve records each preserve one real attempt; hidden
query correctness is unknown. Work logs are authored summaries, not token-level
model traces or probability records.
