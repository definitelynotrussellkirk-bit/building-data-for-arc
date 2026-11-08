# Allocation-quality assessment — ticket-17ad79dd651dc0ff

## Reproducible sample and current allocation facts

- Ticket seed: `8796f740db2426f56785e613407c9b1d62684c0e41e14d7fbed1e262e25014c9`.
- Sampling rule: `random.Random(int(seed, 16)).sample(sorted(all_ids), 3)`.
- Sampled current records: `f3076f3858b4`, `8eb9146172f8`, `5cff0d794bdf`.
- Packet pools: 300 total IDs, 164 main IDs, and 162 normal main-draw IDs. The normal pool is 162/162 `reviewed_safe`, split 81 `improved` and 81 `accepted_repair`; every normal record has catalog `mix_weight=1.0`.
- The authoring draw reserves 10% for public-evaluation focus. Its 120 anchors contain one direct-related anchor and 119 inspired-extension anchors. This authoring probability is distinct from catalog mix weights used downstream.
- Supplementary ticket weights are explicitly heuristic, not measured optimal allocation: adversarial 35, audit replay 20, API 15, and parameter/tool/allocation 10 each.

Exact metadata and all 18 generated/Racket-labeled pairs are in `checks/tickets/ticket-17ad79dd651dc0ff/probe.json`.

## What the three records show

| Task | Representation / provenance | Existing quality evidence | Parameter and four-query support | Bounded live probe | Immediate authoring interpretation |
|---|---|---|---|---|---|
| `f3076f3858b4` | bank source; whitelist catalog health but unverified training safety; outside the normal main pool | One unresolved source-bound audit: 3/4 canonical pairs use clipping rejected by `self_check`, 0/300 production draws clip, production scale misses canonical scale, declared controls were inert; no task-local tests | Six declared axes, no retained parametric manifest, no episode-level four-query evidence | 6/6 generated inputs passed `self_check`; 4/4 query inputs and outputs were distinct; 6 Racket calls took 0.063 s after bridge startup | Repair-first. Raw diversity is cheap, but current distribution/validator mismatch makes new lesson volume low-confidence until the retained defect is repaired. |
| `8eb9146172f8` | augmented + training; reviewed-safe, accepted repair, normal main pool | Task-local 9-test suite plus lint, destructive mutation, semantic contract, exact override, and Racket smoke passed in a bounded independent audit; two orientation shortcuts were refuted | Six declared axes, no retained parametric manifest; no setting-fixed parameter/four-query artifact | 6/6 valid; 4/4 distinct query inputs and outputs; 6 Racket calls took 0.105 s | Best extension candidate in this sample: existing semantic and API evidence lowers repair risk, while parametric/four-query support remains genuinely missing. |
| `5cff0d794bdf` | bank source; historical graylist, unverified, outside normal main pool | Three retained audits: ignored controls, advertised legal ranges rejected, unknown/invalid controls accepted, and a same-color-guard shortcut survives all ordinary generated scenes; no task-local tests | Nine declared axes, no parametric manifest, no episode-level four-query evidence | 6/6 ordinary draws valid; 4/4 distinct query inputs and outputs; 6 Racket calls took 0.041 s | Repair-first. Four distinct labels are easy to produce, but that does not fix collapsed controls or the unteachable equality guard. |

The complete probe used one persistent protected Racket process and finished in 2.426 seconds including startup. There were no duplicate query inputs or outputs in these 12 queries. This only establishes finite raw diversity and labelability. It does **not** establish that demonstrations identify a hidden parameter, that four queries cover a parameter space, or that a plausible rival is eliminated by each assembled lesson.

No sampled record came from ARC-GEN or RE-ARC, so this sample provides no source-specific grammar, rejection, or repair evidence for either. No quality conclusion about those sources is warranted. The two bank records also show why provenance alone is not a quality signal: both generated diverse Racket-labelable scenes while retaining important unresolved defects.

## Cost and expected-quality comparison

In this sample, Racket execution and hash-based deduplication were negligible relative to review cost: 18 labels took 2.426 seconds including startup, while two of three records require nontrivial source-bound repair before additional data is trustworthy. Under a naive uniform sample of all current records, the observed immediate extension-ready rate was 1/3. That is a small-sample estimate, not a corpus rate.

A concrete alternative **authoring** allocation, preserving the current 10% evaluation focus and leaving all catalog mix weights and training boundaries unchanged, is:

- 50% of the remaining 90%: **extension-ready gap** — reviewed-safe source, focused tests or clean bounded semantic/API evidence, no unresolved source-bound defect, and no retained parameter/four-query artifact.
- 30%: **repair-first** — a concrete unresolved source-bound generator, validator, override, or teaching finding with a bounded reproducer.
- 20%: **uniform exploration** across the existing normal pool to avoid starving under-instrumented families.

On the three sampled records, this classifier puts `8eb9146172f8` in extension-ready and the two bank records in repair-first. Relative to the observed 1/3 immediate extension-ready yield, a 50% extension-ready stratum targets at least a 1.5× increase in immediately buildable parameter/four-query assignments **if** the classifier is accurate. That multiplier is an estimate from only three records; it is not a measured corpus improvement. The 30% repair stratum preserves deliberate defect reduction rather than simply excluding difficult generators.

## Bounded experiment and stopping rule

Run 20 authoring assignments under the existing per-assignment budget, randomly pairing 10 baseline uniform-normal draws with 10 draws from the proposed 50/30/20 strata. Keep the 10% public-evaluation focus outside this comparison and do not change catalog mix weights.

Primary metric: verified useful deliverables per authoring hour, where a deliverable is either (a) a source-bound repair with focused green tests and matching Racket evidence, or (b) a setting-fixed prototype with at least two demonstrations, four distinct queries, exact Racket labels, rival checks, and visible-content deduplication. Secondary metrics: unresolved findings closed or sharpened, failed/blocked assignment rate, duplicate public IDs, and Racket calls per verified deliverable.

Stop after 10 assignments per arm, or early after 6 per arm if one arm leads by at least 3 verified deliverables and has no higher failed-verification count. Adopt the alternative only if it improves verified deliverables per hour by at least 20% without increasing unresolved safety/semantic findings per 10 assignments. Otherwise retain uniform normal drawing and use the collected records to revise the classifier. This experiment estimates authoring efficiency only; it does not approve generators or admit data to training.

## Coverage limits

This assessment sampled three of 300 current records, executed six finite draws per record, and reused retained reviewer evidence. It did not run a corpus census, peer batteries, model training, lesson-rotation search, or external-source benchmark. Two sampled tasks are outside the normal main pool, so their defects inform the wider catalog and ticket pool more directly than the current 162-ID normal authoring pool.
