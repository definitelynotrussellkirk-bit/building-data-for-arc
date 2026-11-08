# Working notes: abee0b4bed48

Imported associated notes retain original evidence and timestamps in
`evidence/associated_notes.jsonl`.

## Current decision: separate parametric family, reviewer-ready

Production v2.0.0 and the selected canonical program are unchanged.
`workspace/parametric/` adds the episode-fixed setting `order=input|frequency`.
The default returns the exact canonical bytes. Every aligned 3×3 tile decodes
as follows: one gray cell → 4; eight → 3; a three-gray top row → 6; a bottom row
→ 1; another three-gray pattern → 9; all other counts → 0. The alternative
orders tiles by descending decoded-class frequency, then ascending numeric label,
and paints whole tiles. Original index breaks equal-label ties, which are
unobservable after identical zones are painted.

The decoded label vector is the intermediate consumed by the ordering stage.
Raw gray-count frequencies conflate top/bottom/other triples. A native protected
wrong-intermediate witness retains the correct painted labels but uses those
raw counts for ranking; its output differs. See
`checks/abee0b4bed48/causal/{witness,replay}.json` in the return.

## Domain and sampler

Admit exactly three rows, width 3–30 divisible by three, exact Python lists and
exact integer 0/5 cells. All 512 binary tile patterns are lawful. A meaningful
maximum is 3×30 with ten zones and 51 gray cells. The canonical task reads only
three rows; extra rows would be ignored context, so 30×30 is outside this family.

The sampler supports seeds 0 through 2**63−1, 3–6 demonstrations and 1–4 queries.
Input streams match across settings. Counts have independent prefixes and the
full four-query bank is shuffled before selection. Every returned grid is fresh.
Three core examples teach an isolated eight-gray tile, a ten-zone repeated-class
scene and an all-distinct scene. Marker/hole positions and three-gray shapes vary;
numeric ties deliberately oppose the input order. Optional demos preserve their
ordinary prefix.

## Review findings and retained repairs

The initial repeated-class lessons hid fixed decoder-label permutations: 0/9
and top/bottom could swap while every demonstration histogram stayed unchanged.
Repaired counts and a shared vertical reflection give all six labels different
count vectors across the three demonstrations. This excludes every nonidentity
fixed permutation of those labels, not arbitrary shape-dependent decoders.
The reusable `checks/class_histogram_audit.py` exposes this particular ambiguity.

A separate fresh reviewer then found that counting contiguous label runs fitted
all demos at frequency seeds 2 and 6 while changing a query. Its minimal protected
example is a 3×9 strip decoding to [9,9,3]. The last repair groups all three
label-9 tiles in the large demo into one run, distinguishing zone frequencies from
run frequencies without changing class counts. The final independent audit
rejects this rival at demo index 1 in all 32 reviewed frequency lessons.

Every audited query and optional demo is unchanged across both repairs: 256
query pairs and 192 optional-demo pairs match the original sampler byte for byte.
Original sources, failing checks and minimal Racket witnesses remain under
`checks/abee0b4bed48/`.

The existing six tests needed a portable canonical fixture lookup; their test
function bodies and assertions are unchanged. Strict parsing also exposed an
extra closing delimiter in the first frequency program. Removing it preserves
its intended protected output behavior; a parsing regression now requires one
complete rule expression.

## Final evidence and next action

The native task suite passes all 75 tests. `independent-ready.json` covers all
512 patterns, 64 episodes under the frozen 38-rule bank, 15 separate label-pair
swaps, the run-count rival, count/prefix boundaries and 321 fresh protected
executions. A fresh independent review contributes 188 protected checks and
37 strict validation probes with no remaining finding. Native qualification
passes both settings at seeds 0 and 17 with three demos and four queries (40
protected evaluations). The causal witness replays; the actual 16 public
one-query views pass byte, privacy, ordering and tamper checks.

Current prototype SHA-256:
`c6996ceef4257085b4e599cd2edb8151b2695dd75c59cc88e6ab98949422d9e3`.
The task-local manifest binds the exact returned code, tests and small evidence
summary. Finite checks do not establish unrestricted uniqueness or training gain.
Next action belongs to the owner: intake, fresh native qualification and exact
source acceptance. Reviewer-ready is not acceptance or training admission.
