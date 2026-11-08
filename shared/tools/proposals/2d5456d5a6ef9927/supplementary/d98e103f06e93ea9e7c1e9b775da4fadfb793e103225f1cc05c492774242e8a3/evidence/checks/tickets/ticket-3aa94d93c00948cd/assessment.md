# Bounded allocation-quality assessment

Ticket `ticket-3aa94d93c00948cd`; consumer
`bounded_owner_allocation_experiment_proposal`. This is an allocation proposal,
not a source approval, training admission, or change to current sampling policy.

## Selection and actual pools

The pinned anchor is `6b88648ff0e0`. Starting from the ticket's immutable seed,
`Random(int(seed,16)).sample(sorted(all_ids minus anchor),2)` selected
`1a259ef9a7e7` and `424c822d69f3`. There was no reroll. The probe binds all three
current source hashes and reference hashes, the packet manifest, catalog, and
retained evidence files in `probe_result.json`.

The packet contains 300 of the owner's 3,941 generator records. Its recorded
selection quotas are 150 unfinished-original roots, 60 recent-focus roots, and
90 coverage slots, including 30 public-evaluation roots; these are packet
construction controls, not dataset probabilities. The normal authoring pool has
162 approved original families needing parameters. The union of main IDs has
164 entries. Manifest priority counts additionally record 16 original families
needing repair and parameters, 72 other unapproved records, and 10 current
prototypes. Coverage is 187 of the 1,120 supplied original tasks in this packet.

The executable main draw selects a normal ID by seed modulo the 162-entry
pool and independently assigns evaluation focus on a one-in-ten hash roll.
All 120 supplied evaluation anchors remain eligible; only one currently has
mapped descendants, comprising two eligible related generators. The remaining
anchors use inspiration on a normal target. This 10% focus remains unchanged.
The three sampled catalog records each have `mix_weight: 1.0`; those dataset
mix weights are separate from authoring-pool membership and evaluation focus.
No full-library dataset denominator or actual training mix was measured.

## Source-specific comparison

| Record | Representation and teaching | Parameter and four-query status | Cost and limits |
|---|---|---|---|
| `6b88648ff0e0`, training `aab50785`, catalog also says augmented | Detect paired 2x2 cyan markers, extract two-row interiors, order and stack strips. Current source has six public layouts and eight generalized group-count/width profiles. | Manifest says prototype missing; no parametric directory. This probe obtains three demos plus four distinct candidate queries, with Racket labels. It does not independently establish lesson identifiability. | Dense inputs: 1,793 input cells across seven samples, 128 output cells. Seven hot Racket labels: 0.0492 s. Retained source-bound note reports a 120-case Racket pass, broad prior censuses, and authority warnings A012 (legacy wrapper) and A008 (`for-each`), not execution divergence. Those reports were not rerun. |
| `1a259ef9a7e7`, training `8d5021e8` | Mirror a 3x2 source horizontally, then alternate vertically flipped/original strips. Ordinary inputs expose both branches. The exact structural domain is 44 masks, or at most 396 colored inputs across all nine colors. | Prototype missing; no parametric directory. Seven distinct Racket-labeled candidates obtained. Retained notes report that three demos eliminate named shortcuts, while some single pairs are answer-equivalent to a template. This probe did not replay that rival census. | Only 42 input cells and 252 output cells in seven samples; hot labels: 0.0114 s. Structural deduplication matters despite inexpensive labeling. Retained notes honestly preserve corrected mask-count and diversity assumptions, failed intermediate lint/override checks, and their reported repairs. |
| `424c822d69f3`, training `ddf7fa4f` | Recolor rectangles by the uniquely nearest legend marker to a floored midpoint. Current source excludes exact ties and constructs witnesses against rank pairing and vertical-overlap-only coloring. | Prototype missing; no parametric directory. Seven distinct Racket-labeled candidates obtained. Each of the first three demos independently rejects both declared rivals, so all four candidate queries have those rivals eliminated without using their answers. | Seven inputs and outputs each total 1,029 cells; hot labels: 0.0175 s. Current review index binds the accepted source and labels verification reviewer-reported. Notes retain a resolved old-source tie ambiguity, 80 reported tests, 53 reported Racket cases, and an 11/12 aggregate with a separately completed schedule check. They do not establish an independently rerun 12/12 aggregate. |

All 21 fresh samples passed their current `self_check`; all 21 labels agree
between real canonical Racket and the task-local mirrors. No generation call
raised an error. Internal retries were not measured, and these successful
returned samples do not estimate rare failures. Every sampled
source hash matched the pinned manifest. The probe's first-three/last-four split
is a bounded canonical smoke lesson, not a shipped parametric episode API.

The sample contains no record identified as ARC-GEN or RE-ARC lineage. It cannot
compare those sources or justify increasing any source's volume. Grammar and
linter evidence above is retained, source-bound reporting where available;
there was no fresh grammar gate, linter battery, model job, or repair-time study.

## One concrete alternative, with estimates separated

Compare a future 120-case coverage budget over these same three families:

- **Equal-count baseline:** 40 cases per family, independently sampled.
- **Coverage allocation:** 38 strip cases, all 44 branch-visible mirror masks
  once at an explicit foreground color, and 38 nearest-marker cases. Keep
  demonstration/query grouping separate and keep exactly matched Racket labels.

For the mirror task's default draw, the 42 internal mask indices have probability
1/43 and the two endpoint indices have probability 1/86, because the shared
integer draw rounds a uniform real value. Under independent draws, 40 cases
therefore cover an estimated
`2*(1-(85/86)^40) + 42*(1-(42/43)^40)` distinct role masks. The alternative covers
44 by construction. This counts structural coverage, not learning quality;
fixed-color coverage also needs a separate color-transfer check before use.

Using the tiny measured hot-label timings only as a rough linear estimate,
both allocations take under half a second for reference labeling after startup.
The shared Racket startup cost was 7.2145 seconds and dominates both estimates.
There is no evidence here that a small label-time difference merits a policy
change. The useful hypothesis is that explicit structural coverage reduces
redundant reviewer work while retaining the two more compositional families.
Review minutes, downstream learning, and the other families' structural
duplicate rates remain unmeasured.

## Proposed bounded experiment and stopping rule

An owner may compare the two allocations with fixed seeds, at most 240 total
candidate inputs, one reused Racket process, at most 120 seconds of execution,
and 30 minutes of author review. Stop at the first limit; retain failures and
partial denominators. Predeclare the grouping before drawing: deterministically
shuffle each family's slots independently of outputs, then use the first 35
slots for five disjoint three-demo/four-query lessons in each arm. Thus both
arms assess 15 candidate lessons. The remaining baseline slots (5/5/5) and
alternative slots (3/9/3, in strip/mirror/rectangle order) count toward coverage
and cost only, not the accepted-lesson numerator. Do not deliberately reuse an
input between lessons or resample a duplicate slot; reject a lesson if an exact
duplicate breaks its distinct demo/query contract, and separately report
duplicates across lessons. Record exact-grid duplicates, normalized-structure
duplicates, Racket milliseconds, rejected draws, and demo-only rival elimination
before inspecting query answers. Report accepted four-query lessons per review
minute and per reference second; do not substitute raw distinct grids for that
quality measure. Any mismatch or unresolved answer-divergent rival blocks the
affected lesson. If both arms saturate structural coverage, stop drawing that
family and report saturation rather than resampling indefinitely.

For parameter work, each sampled family still needs a separately named rule
variant with its own executable Racket and identifiable demonstrations. The
smoke labels here do not fill that gap. Preserve the present authoring priority,
10% evaluation focus, dataset weights, approval identities, and admission
boundaries while evaluating the proposal.

## Evidence and execution boundary

One targeted probe was executed, in 7.5016 seconds, with exit code 0:

```bash
# cwd: WORK
python3 run_with_racket.py python3 ../checks/tickets/ticket-3aa94d93c00948cd/allocation_probe.py
```

`probe_result.json` contains the exact command, seed and selection algorithm,
source/rule/evidence hashes, input/output hashes, measured timings and outcomes.
The script has a 115-second internal alarm under the 120-second ticket limit.
All other work was bounded inspection and arithmetic on those results. No
generator, prototype, policy, weight, approval, or shared source was changed.
