# D4 odd-shape selection with canonical or observed pose

Reviewer-native prototype for `004ca3500787`; production generator 4.1.0,
approval state, and the inherited production finding are unchanged. The
`pose=canonical` program is the exact 1,716-byte selected canonical Racket
program (SHA-256 `27bae96c0fff8a536a7862ccffebfb040721843016c42dae1b2d06697f456aca`).
`pose=observed` selects the same singleton shape class and renders that object's
observed tight crop in cyan. Pose changes the rule's output, not its scene style.

## Grammar and contracts

An input is an exact built-in list of equal-length built-in lists, with axes
1..30 and exact integer cells in `{0,2}`. Red objects are four-connected
components; diagonal contact is allowed. There are at least three components
and exactly two equivalence classes under all rotations and reflections, with
multiplicities `n-1` and `1`. Component size, bounding box, and shape are otherwise
unrestricted. The implementation rejects inputs outside this grammar. Both
program settings are total on this grammar; the Python oracle does not limit
validation to the sampler's named shapes, scales, or arrangements.

Canonicalization matches Racket's **string** comparison of formatted, numerically
sorted normalized coordinate lists. Comparing numeric coordinate tuples instead
would choose the wrong orientation for some shapes spanning coordinate 10.
The connected 13-cell S13 witness has row 0 at columns 0..9 and row 1 at
columns 0,9,10; its exact string-canonical pose is the 180-degree rotation of
its numeric-canonical pose. A separate protected design probe checks this
literal against the exact canonical program.

`generate(seed, settings=None, demos=3, queries=4)` accepts exact integer seeds
0..2**63-1, 2..6 demonstrations, and 1..4 private queries. A supplied settings
dict must contain exactly `pose`, whose value is `canonical` or `observed`.
Omitting it selects one setting once per episode. Separate SHA-256-derived
random streams control settings, demonstrations, and queries. The full six-plus-
four input bank is built before slicing, so count changes preserve prefixes and
changing the rule setting preserves the inputs. Ordinary omitted demo count is
three; qualification explicitly requests six. Every call returns fresh lists.

## Constructive teaching bank

The first two demonstrations reject complementary shortcuts without depending
on the optional demonstrations. Core A's common F5 pair contains both chiral
forms, and its singleton W5 has the same five-cell area and 3x3 bounding box.
The singleton is the middle component. Core B's common P5 pair also contains
both chiral forms; its singleton S13 is first in row-major component order and
touches one common component only diagonally. This distinguishes four- from
eight-connectivity and teaches the exact two-digit canonicalization rule.

Observed W5 is a noncanonical rotation. Observed S13 is a reflected pose chosen
so no single D4 transform maps both canonical singletons to their observed
poses. This choice accounts for W5's stabilizer rather than assuming all shapes
have eight distinct poses. Background spacing and object poses vary by seed.

| Bank slot | Canvas | Content |
|---|---|---|
| Demo 1 | 12x20 | Three objects: F5 / W5 / reflected F5, equal area and boxes |
| Demo 2 | 16x23 | First singleton S13; reflected common P5 pair; diagonal contact |
| Demo 3 | 1x6 | Two common monominoes and a singleton domino |
| Demo 4 | 12x18 | Six independently posed F5/P5 objects |
| Demo 5 | 24x27 | Nine F5/P5 objects at scale two |
| Demo 6 | 30x30 | Nine F5/P5 objects at scale three; 405 red cells |
| Query 1 | 7x12 | Three I3/L3 objects |
| Query 2 | 17x22 | Eight F5/T5 objects |
| Query 3 | 26x29 | Four P5/F5 objects at scale four; 320 red cells |
| Query 4 | 30x30 | Sixteen F5/W5 objects at scale two; 320 red cells |

The 30x30 scenes distribute many components across the canvas; their different
occupancies guarantee distinct demo/query inputs. Other input dimensions are
distinct. Field layouts allocate disjoint slots with at least one blank row or
column between them; the only deliberate diagonal contact is in core B. No
rejection sampler, retry budget, solved-output filtering, or difficulty knob is
used.

## Sequential dependency and causal boundary

In the observed-pose Racket program, A computes each component's full D4
signature once and stores `(object, signature)` pairs. B counts the stored
signatures, selects the object whose stored signature occurs once, and renders
its observed normalized crop. B does not recompute A's signature.

The causal intervention replaces only A's tag expression with the
translation-normalized observed signature. B's counting, selection, and
rendering remain byte-identical. On core A, the intervention splits the two
reflected common shapes into separate classes; B then chooses the first common
object instead of the actual middle singleton. The retained witness must show
the executed intermediate tags and both protected full/counterfactual outputs.
Reversing the stages is not an appropriate control because selection consumes
tags that do not yet exist.

## Evidence and limits

`audit_native.py` independently extracts objects, classifies shapes, and renders
labels. Its finite named rival set checks D4 versus rotations/translation,
bounding-box classification, size and position heuristics, common versus rare,
eight-connectivity, numeric canonicalization, and output shape/pose/color rules.
It checks protected Racket outputs, reports every survivor and private-query
disagreement, and binds the task and protected runtime sources before/after.
Finite seeds and a finite rival set are evidence, not a proof against every
possible rival. The shared sampler probe separately checks deterministic request
contracts and matched inputs; it is not the label authority.

The inherited production finding `review-205ebfa3d89039c8:v0001` remains
**unresolved**. It concerns arbitrary reassignment of a production pair as query.
This new bank fixes demonstration/query roles and preserves both teaching cores
at the minimum demo count; public query shuffling changes presentation order
within the private query bank only. This prototype does not repair or close the
production finding. Reviewer readiness is separate from owner acceptance and
training admission.
