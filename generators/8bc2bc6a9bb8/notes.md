# Working notes: 8bc2bc6a9bb8

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
<!-- review-f339646b581e5a8e:start -->
## 2026-10-24 — review-f339646b581e5a8e

### Canonical teaching repair

Version `2.1.0` keeps canonical `RULE_HASH = "45fdce305a90"` and the exact occupied-area Racket rule unchanged. The prior generated shape bank did not constructively distinguish occupied-cell area from bounding-box footprint. Profile 1 now places a five-cell line (area/footprint `5/5`) against a four-cell L (area/footprint `4/6`), so the canonical area ranking and the plausible footprint-first rival reverse their order. `footprint_order_conflict` is an observed semantic feature; `footprint_then_area` is an executable lesson rival; and the schedule requires the separating witness without adding demonstrations. The focused production suite is retained at `checks/8bc2bc6a9bb8-canonical-repair/green/` (`7 passed`).

### Proposed parametric family

The task-local prototype introduces one episode-fixed parameter, `sort_key = occupied_area | bbox_area`; `occupied_area` materializes the exact canonical program byte-for-byte, while `bbox_area` changes only the geometric ranking measure. Input draws are setting-independent. The sampler supports independent `2..6` demonstration and `1..8` query counts, retains three demonstrations and four distinct queries in ordinary evidence, and includes a real `30×30` query with top/bottom/left/right contacts and more than 30 occupied cells. Every label is executed through the bundled protected Racket bridge. The four public queries are stored privately and projected one at a time with no future inputs or total-count hint; public IDs hash only visible bytes.

Seed 37 retained two matched-input episodes with 6 demonstrations, 8 queries, 3 canonical pairs, and 33 Racket applications. The opposite declared sort key is refuted by demonstrations in both episodes. The focused task suite passes `23/23`, including native positional adapter compatibility and single-query/first-turn identity. The public exporter accepted both challenges. The bounded edge probe passed the minimum `2/1` and maximum `6/8` requests for both settings. Source-bound evidence is under `checks/parametric/`; the native inventory is `workspace/parametric/evidence/manifest.json`. The adapter and contract are `workspace/parametric/adapter.py` and `promotion.json`.

### Scope and next action

This is a **proposed, unapproved** prototype. The finite rival check does not prove unique induction against arbitrary programs, and no qualification, production acceptance, or training admission is claimed. The next concrete action is owner qualification on fresh seeds through `arcpuzzles parametric qualify`, followed by semantic review before any acceptance.
<!-- review-f339646b581e5a8e:end -->
