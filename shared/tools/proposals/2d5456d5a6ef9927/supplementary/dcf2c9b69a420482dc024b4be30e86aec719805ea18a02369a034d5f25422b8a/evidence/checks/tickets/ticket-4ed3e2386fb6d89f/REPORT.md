# Allocation-quality ticket — bounded source-bound sample

**Outcome: completed.** No draw policy, catalog weight, approval, generator, or training mixture was changed.

## Seeded sample and current allocation context

Ticket seed `a52a70b3b91a900a33f1da7f1c2b241ec982d8d8e0eec056f2e568a176d52523` retained the pinned primary `22304ccc509c` and selected peers `2d4e8c8fa10e` and `1e7a6ba0bb90` with Python `random.Random(int(seed,16)).sample` over the other 499 sorted packet generator IDs. `selection.json` records the universe hash and exact pins. All three actual source hashes match the packet and current approval-catalog hashes.

The packet main draw is uniform over 500 included generators selected from 3,941 owner generators. The independent public-evaluation authoring focus fires with probability 1/10 over 120 anchors but explicitly leaves the selected main target unchanged. The parametric-priority tier contains 151 approved originals needing parameters; `22304ccc509c` is not in that tier. These are authoring-selection policies, not dataset sampling weights. All three sampled `catalog/puzzles.jsonl` rows and `generator_weights.json` entries have weight `1.0`.

The older `shared/data/derived/generator_catalog.jsonl` snapshot is dated 2026-06-21 and describes pre-repair versions for all three records (including obsolete axes/lint warnings). It is useful historical metadata but is not fresh enough to grade current source quality; the packet pins, current catalog, source, notes and review indexes are the relevant identities.

## Quality and cost comparison

| Task | Current evidence and representation | Teaching / four-query support | Cost and remaining gap |
|---|---|---|---|
| `22304ccc509c` | Approved v3.0.0 order-preserving column gravity; four observable controls (`grid_h`, `grid_w`, populated columns, palette size), 6–18 sides, 2–6 columns and 1–9 foreground colors. Prior bottom-row and ignored-palette defects were repaired. | Existing notes report a 12-stage pass, 600/600 strict semantic draws, 300 lessons / 1,200 unique pairs and zero declared ambiguity. The new ticket probe materialized 3 demos + 4 queries: 7/7 distinct inputs, no rejections or validator errors, every Racket label matched the independent mirror, both declared rivals were refuted by every pair, and all four queries were identifiable from demonstrations alone. | Best demonstrated four-query efficiency here: 7 authoritative labels for 4 targets. Coverage remains down-only, column-local, and finite-rival; 7 unique inputs are not a corpus duplicate estimate. |
| `2d4e8c8fa10e` | Approved v3.1.0 exact-solid-2×2 filter; five controls and a deliberately narrow single-color shape grammar. A retained orientation shortcut was repaired by adding both horizontal and vertical tetromino controls. | Notes report 25 task tests, a 3,600-draw probe and 300 ordered lessons. The three-demo production schedule is identifiable, but 400/1,200 diagnostic arbitrary query rotations were ambiguous because withholding a control can remove its witness. Six rivals are declared. | Potentially 7 labels for a 3+4 episode, but four-query pooling is not currently demonstrated in the retained evidence. Narrow representation and rotation sensitivity justify a smaller pilot share until that exact assembly passes. No fresh duplicate-rate estimate was found. |
| `1e7a6ba0bb90` | Approved v2.0.0 transform-key + Boolean-operation composition; six controls, three transforms, three operations and structured two-object scenes. | Strongest semantic breadth: 35 declared rivals, nine demonstrations, a 12-stage pass, 27,000 accepted override draws, and 300 lessons / 3,000 distinct grids / 3,000 rotations with no declared ambiguity. | Highest review/Racket/token cost: a four-query episode needs 13 labels (9 demos + 4 targets), versus 7 for the other two. The generated domain remains structured (two separated monochrome objects, boxes up to 4×4); medium and hard share the same shape-pool bound. |

No ARC-GEN or RE-ARC record was selected by this three-record draw, so this ticket does not rank those sources or recommend changing their volume. The October 23 training snapshot is older r6 materialization context, not a measurement of this refreshed source set.

## Alternative allocation and bounded test

For a **12-episode source-quality pilot**, compare the equal 4/4/4 split implied by equal sampled weights with a proposed **5/4/3** split across `22304ccc509c` / `1e7a6ba0bb90` / `2d4e8c8fa10e`. This preserves four episodes of the highest-semantic-breadth task, adds one episode to the already demonstrated low-cost four-query task, and removes one from the source whose exact four-query assembly is still unverified. Assuming 3+4 labels for the two three-demo tasks and 9+4 for `1e7a6ba0bb90`, both splits cost an estimated 108 Racket labels; the proposal changes expected evidence quality, not label budget. This is an estimate, not a measured training optimum.

Run at most eight attempts per family to retain the requested accepted episode counts. Require current source/rule hashes, legal controls, four queries distinct from all demonstrations, authoritative labels, clean validation, and demonstration-only rejection of every declared rival that changes a query. Stop a family immediately on source drift or any Racket/mirror disagreement; stop volume expansion if fewer than 75% of attempts are accepted, if any retained query is ambiguous, or if within-family duplicate inputs exceed 10% in this small pilot. For `2d4e8c8fa10e`, the first failed four-query lesson ends its pilot and routes the exact assembly to repair rather than adding volume. Model training and mixture effects remain unmeasured.

## New targeted probe

From `WORK/`:

```sh
python3 run_with_racket.py python3 -m arcpuzzles generate 22304ccc509c \
  --count 1 --seed 8279138532683228451 --sample-index 934 --difficulty medium \
  --train 3 --test 4 --out ../checks/tickets/ticket-4ed3e2386fb6d89f/episode.jsonl
PYTHONPATH=repo/shared/runtime:repo python3 \
  checks/tickets/ticket-4ed3e2386fb6d89f/analyze_episode.py
```

The wrapper took 4.63 seconds. `probe_result.json` contains pair-level dimensions, observed controls, witness/rival results, self-checks and mirror/Racket agreement. This is exactly one targeted executable probe and one local analysis pass.
