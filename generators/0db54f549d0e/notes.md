# Pairwise-intersection gallery — current notes (v2.2.0)

## Rule and authority

Selected Racket hash: `2a9df9793155`. No reference-rule change. Four fixed 3×3
windows have origins row0=(0,0), row1=(4,0), col0=(0,4), col1=(0,8). For each
row/column pair, intersect nonzero occupancy and paint the matching positions
8 in a 7×7 output, with a zero separator row and column. Input prototype colors
do not select roles. Python `rule_mirror` is diagnostic only.

## Input contract

Rectangular genuine-integer colors 0..9; canvas 7..11 rows and 11..15 columns.
Ink occurs only in the four fixed windows; each window is monochromatic or
empty. Each count axis is exact 0..9 in every band. Known None is unspecified;
unknown controls and malformed values raise. Empty/full/single-overlap textures
fix counts at 0/9/1, with precise declared incompatibilities for conflicting
counts. The old blanket rejection of empty windows is reversed because empty
intersections are lawful under the reference and exact axes.

## Default distribution and lesson design

Even unpinned random draws use 7×11, independently drawn counts 3..6, four
distinct intersection panels, and all four Boolean input cases. A color
permutation of 2,3,4,5 is selected only if it refutes the canonical color-role
shortcut. Geometry retries keep the counts fixed and are capped at 512.
Odd draws vary padding, geometry, palette and difficulty densities. Palettes
are four distinct colors or one shared color, including input 8. The shared
branch and variable padding broaden the teaching appearance. Explicit counts
and endpoint textures do not promise informative lessons.

Three demonstrations are declared; the period is two. Ten distinct rivals
cover Boolean, copying, ordering, color-role and color-equality alternatives.
The canonical color-role rival fits all five canonical pairs. Retained
counterexamples and the workspace probe verify a legal recoloring with real
Racket outputs and additionally inspect numeric color rank.

## Checks and open limits

Final 116 task tests pass. The official override matrix has 72,630 attempts,
zero findings; independent probes cover all 10,000 joint count tuples and
2,048 teaching constructions. The 300-lesson/1,200-rotation census has no
ambiguity for the declared rival set; fixed-seed schedule enumeration covers
both starts in all bands (six lessons, 24 rotations, nine unique inputs).
Full receipts are in the assignment return, with source hashes and exact seeds.

The after battery remains 11/12 green: generic minimal-impostor lint flags
all-zero and top-left 2×2 inputs that the unchanged Racket rule accepts. The
counterexamples preserve that evidence; no validator distortion or shared-tool
exemption was installed. Acceptance requires a maintainer decision on this
warning and does not change training approval.

The manifold excludes multicolor prototypes, arbitrary translations and larger
padding. Default palettes do not sample partial two-/three-color aliasing across
four nonempty windows. Teaching forces counts 3..6 in all bands; the broader
0..9 domain is available through explicit controls. Finite probes do not prove
all RNG states avoid the bounded retry failure or that every possible rival,
override curriculum or model is taught. Original rationale beyond supplied
baseline files is unknown; prior placeholder notes were replaced by this account.
## Current reviewer considerations

Source SHA-256: `4cc8402043331811424b70646861a9b0e66dc82cfa0d7e1ee411e94faf166561`.

# Decisions and limitations

## D1 — Authority and scope

Keep the selected Racket transformation and canonical/base authorities intact.
The five canonical outputs and independent reference applications support the
fixed-window Boolean AND interpretation. Python `rule_mirror` is a diagnostic
for contracts; production labels remain Racket-owned. Neither audited generator
is repaired in this delta. Original design rationale beyond the supplied code
and placeholder notes is unknown; no earlier return was used as a measurement.

## D2 — Replace ignored controls with exact counts

The prior generator advertised four counts but drew internal counts regardless
of them. Each axis now supports a genuine Python integer from 0 through 9.
Known `None` means unspecified; unknown names, even with `None`, raise. Counts
are drawn once through keyed strict helpers and are observed from pixels.
Bool, float, string, out-of-range and malformed values are rejected.

Clipping, post-draw rewriting and silently ignoring out-of-band counts were
rejected because they make an exact caller request untruthful. Explicit counts
use the full domain in every difficulty. All 10,000 joint tuples were tested
once; the official pairwise/axis/texture matrix adds 72,630 attempts. These are
finite settings, not all possible seeds.

## D3 — Legal degeneracy and texture conflicts

Reverse the old rejection of empty windows. Empty, full and singleton-overlap
textures are explicit legal endpoints: required counts 0, 9 and 1 respectively.
A matching count override is accepted; a conflicting one raises and is declared
in the incompatibility matrix. Empty windows and disjoint prototypes can yield
all-zero outputs under the unchanged rule. Degenerate textures are diagnostic
and caller-requested endpoint cases, not sufficient lessons on their own.

Tightening the validator to silence the remaining generic lint warning was
rejected. The two retained witnesses actually execute through Racket and yield
zero 7×7 outputs. Declaring all minimal grids harmless globally would also be
wrong: request a task-scoped, evidence-bound linter acknowledgment instead.

## D4 — Shape and color manifold

Retain four fixed 3×3 windows, monochromatic or empty, on a 7..11 by 11..15
canvas. Zero is background; only those windows may hold ink. Blank padding is
limited to zero through four trailing rows and columns. Nonzero input colors
1..9, including 8, are lawful and may repeat across windows. This deliberately
covers a narrower manifold than arbitrary inputs the Racket implementation can
process; arbitrary translations, resized prototypes, multicolor prototypes,
stray ink and larger canvases are outside the advertised distribution.

The validator now checks container structure, rectangularity, size and genuine
integer ARC colors before indexing. It then checks window occupancy and each
window's monochromatic property. It reports errors instead of crashing on
malformed inputs. Broad acceptance of anything Racket can evaluate was rejected
because it would erase the intended task-domain contract.

## D5 — Two-part default distribution

Even, unpinned, `texture=random` sample indices are teaching examples. They use
7×11 canonical dimensions, independently drawn counts 3..6 in every difficulty,
four distinct output panels, and all four Boolean input cases. Geometry
rejection retains the drawn counts and is bounded at 512 attempts. Among the
24 permutations of colors 2,3,4,5, choose one that actually disagrees with the
canonical color-role rival. The candidate set is nonempty because swapping the
two row colors changes four distinct panels.

Odd indices retain varied geometry, density, padding and palettes. Unspecified
counts use easy 2..4, medium/None 2..7, hard 4..8. The palette selector weights
`distinct` twice, `shared` once and canonical-palette permutations once. This
preserves canonical-size/palette support while also presenting equal-colored
prototypes and input 8. Default four-nonempty-window palettes have either one or
four distinct colors; partial two-/three-color aliasing remains unsampled.
Explicit counts disable the teaching construction, preserving exact requests.

Making every example informative would overconcentrate the distribution.
Leaving all geometry unconstrained would provide no practical protection from
unhelpful lessons. The chosen split retains both. The 3..6 teaching density
range is a stated restriction across all bands, not a hidden difficulty-specific
axis. The geometry probe covered every teaching tuple over eight seeds and
needed at most six attempts, but does not prove the cap unreachable for all RNG
states. No general difficulty ordering or model learning gain is claimed.

## D6 — Lessons and rival scope

Declare three demonstrations, one query for census, and a period-two schedule.
The production materializer's actual accepted indices and any rejections are
retained. Query rotation holds out each pair once and preserves the order of
the rest. Required rotation checks passed 48 smoke positions, 1,200 wider-census
positions, and all 24 positions in the fixed-seed period enumeration.

Ten distinct rival behaviors cover blank, union, XOR, row-only, column-only,
panel transpose, row swap, column swap, canonical color roles and color equality.
The color-role shortcut fits all five canonical labels. Task-local recoloring
also checks ascending and descending numeric-color rank as extra diagnostics;
those two are not inflated into the declared ten-rival census denominator.

Single-grid correctness is insufficient to demonstrate a teachable lesson. The
finite production and rotation verdicts are both reported. Unseen rivals,
unseen seeds, arbitrary override curricula, reorderings beyond the tested
assembly and model generalization remain unproven. The six fixed-seed lessons
contain nine unique inputs, not 24 independent examples. These distinctions are
retained rather than reporting overlapping windows as new data.

## D7 — Tests, tools and actual failures

Use a separately authored coordinate oracle and portable `reviewer_support`
root/data discovery. The first 115 tests produced 100 baseline failures and 15
passes; a further independent canonical-oracle test makes the final 116 tests.
The full isolated task-test stage passed after a task-owned environment copied
already installed pytest dependencies with hashes. User-site isolation stayed
enabled; the initial missing-pytest preflight remains in the return. No downloaded
or installed environment is included in the ZIP. The helper also enables
`system_site_packages`, so this is a reviewer-reported host-dependent test run,
not proof of a hermetic environment. The helper is retained and not selected.

The task also produced a standalone standard-library capacity/pending-checkpoint
helper and 33 tests. It does not integrate itself into `review.py`, select a
new assignment, restore a checkpoint or claim replay certification. Its README
states recovery-format limits. The original disk-space failure was recovered
by moving this session's work to writable temporary storage and resuming the
same journaled draw. No user source or original upload was discarded.

## D8 — Acceptance decision

The maintainer accepted the exact-source repair under the reviewer-reported
policy and explicitly acknowledged the two legal empty-intersection witnesses
against unchanged reference rule `2a9df9793155`. The reported after battery
remains **11/12, exit 1**: the shared minimal-impostor heuristic warning is not
fixed or suppressed. A narrowly scoped, reference-bound acknowledgment mechanism
remains a shared-tool proposal. No owner battery replay, universal correctness,
or training approval is implied. Audit findings and optional shared-tool
proposals are separate from the selected-task patch.
