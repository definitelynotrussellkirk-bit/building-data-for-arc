# Working notes: 25e78410d5bb

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric design — review-f2960a0686ed5a88

Keep the production source and exact canonical default unchanged. The task-local
parameter `retention` has two settings: `all` executes the exact canonical rule;
`largest_filled_component` first fills every zero region from its local majority,
then finds same-color four-connected components in that completed grid and retains
only the largest components (all ties). Original nonzero cells are always preserved.
Thus a marker can join newly filled rooms; selecting on original marker sizes or
individual room areas can choose a different result. This is the required causal
dependency, to be retained with an executed wrong-intermediate witness.

The prior retained audit found side-only and row-copy shortcuts in general-lattice
draws. The new sampler uses independently randomized markers on shared walls and
selects short demonstrations against declared finite rivals for both settings.
Inputs use a separate deterministic stream, matched across settings. Support is
2–6 demonstrations and 1–4 independent queries; qualification uses 3 and 4.
Four-query requests include real 30×30 lattices and several 20–30-side cases.

Implementation order: (1) literal rule/parity tests and matching programs;
(2) bounded sampler, count/type contracts and distinguishing lessons;
(3) reusable protected replay/public export, finite self-audit and boundaries;
(4) native manifest, qualification and causal replay; (5) optional peer probes.
Files: `programs.py` owns rules/rivals, `sampler.py` owns matched input sampling,
`adapter.py` owns the native API, and `probe.py` owns retained replay/export evidence.
Tests remain task-local. This isolated extracted packet is the work environment;
the original archive is unchanged. Exact-source owner acceptance remains pending.

## Verified outcome

Native qualification passed for both settings at seeds 0 and 17, three demos and
four queries. The source inventory and qualification bind the final adapter,
sampler, programs and replay helper. A separate protected replay retained eight
episodes and 60 labels across demo counts 2/3/6; every episode rejects the
applicable finite rivals from demonstrations alone. Five vote rivals cover side
walls only, copying a row's first room, global marker majority, minority voting,
and one vote per connected marker object. The alternative also rejects original
room area, global color totals, original marker-blob sizes and bounding-box area.

The qualified 15×12 query in the causal witness joins four rooms into a 64-cell
component. Ranking completed components by their largest original marker blob
instead changes 29 output cells. Both programs were executed and independently
replayed through the protected witness helper; intermediate explanations remain
authored interpretation, not a universal depth proof.

Checks: 26 rule/sampler tests plus 6 replay/export tests passed; the rule suite
contains 112 protected parity executions on seven literal cases. A bounded
six-seed × three-demo-count × two-setting probe completed 36/36 requests and
retained a real retry-exhaustion case at max_attempts=1. Eight saved public
challenges passed the existing byte/identity checker. No universal uniqueness,
all-seed success, training gain or admission is claimed.

Evidence: `WORK/checks/25e78410d5bb/qualification/`, `causal/`, `replay/`,
`min-demos/`, `max-demos/`, `boundaries.json`, `tests.txt`, and `export-tests.txt`.
Current prototype source inventory: `workspace/parametric/evidence/manifest.json`.
Next action: owner integrates the delta and runs mandatory exact-source native
admission. The canonical generator remains on its prior 10–20-side support;
the 10–30-side extension belongs to the separate parametric sampler.
