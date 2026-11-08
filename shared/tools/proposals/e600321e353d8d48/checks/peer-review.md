# Independent final code review — dc155169ea57

Review assignment `review-bde888379ee5fdae`. Read-only source review plus isolated executable probes. No solve private labels were opened. Historical passing receipts are not evidence for later edits.

**Final disposition: no unresolved Critical or Important code-review findings at generator `b0988612ae6038bbbddb6f8f30e787984c5d9c71a1e380f88cd13ada8655e3d6` (v3.4.0) and prototype `7c8d4db59e92cb2caa95310886d32076e86faa7d33317e83e883e342f35586bf`.** The two Important findings below retain their historical evidence and explicit resolutions. Final source-bound battery and teaching receipts were inspected after completion.

## Reviewed revisions

- Initial repaired generator: `e87aab78b168d29156d3b4e4b4222a81a5606e4858d4ab1b9c8c1c09cabe2567`, compared with pinned baseline `59f8d08137665234b6c7ce49c893393e30db7791b491f0184d0c6c829c5e9903`.
- Initial prototype: `79d559db2ff55a29c721d3e9e87d7f20db3977545d0dee9c786ccdd366f84908`, retained at `checks/parametric/prior/v1/sources/prototype.py`.
- Rechecked prototype: `7c8d4db59e92cb2caa95310886d32076e86faa7d33317e83e883e342f35586bf`.
- Exact canonical Racket SHA-256 remains `2def524a1836b8bbbbf304e452ba7cfadf72ac353419ed428326edfcc2b167e6`; catalog hash `c0f1818b0fb2`.

## Strengths

1. The canonical transformation is unchanged. The capacity prototype returns its exact bytes for capacity 1 and changes one checked threshold site for capacities 2/3. Exported labels are executed through the public Racket bridge.
2. Input controls are materially improved: exact integer validation rejects coercible scalars and Booleans; `thin_frac` is explicitly approximate; narrow width draws select a feasible count before recording it. A bounded independent probe of 750 joint cases returned 576 lawful exact grids and 174 explicitly marked count/width incompatibilities, with zero unexpected cases. Cases crossed all three bands, widths 7/8/9/11/30, counts 1/2/3/4/6, fractions 0/.01/.5/.99/1, and seeds 0/17 at height 7 and line row 3.
3. The projection witness is structurally sound: donors occupy isolated column bands; replacements stay in the wide donor band; the blank row preserves distinct components. Opposite orders address deduplication and query rotation for that rival.
4. Prototype public files contain only demonstration input/output pairs and query input grids. Parameter selection is once per episode, demo/query counts are independent, inputs are unique, and rival fitting occurs before query generation.
5. New tests use portable public helpers and meaningful hand-derived outputs. The initial official portable task-test receipt completed with 49 passed, zero failed/errors/skipped. This receipt predates subsequent review fixes.

## Critical

None found: no authority substitution, incorrect exported reference label, public query-label disclosure, or out-of-scope runtime edit was found in the inspected source.

## Important

### I1. Canonical lessons fail to teach three plausible support-row interpretations — historical defect, resolved in v3.4.0

Location at generator SHA `e87aab78...`: `generator.py:503–522` replaces the wide donor with a single horizontal row, so the scheduled witness teaches projection separation but cannot distinguish different support rows or a tail. `generator.py:568–572` declares only the projection competitor. `tests/test_teaching_contract.py:42–54` therefore verifies only that finite inventory.

Using the existing Racket-labelled `checks/lesson-census.json`, the following independent interpretations fit every demonstration but change a query:

| Rival | Easy production / rotations | Medium production / rotations | Hard production / rotations | Total |
| --- | ---: | ---: | ---: | ---: |
| Stop wide shapes at lowest cell | 10 / 40 | 12 / 40 | 6 / 28 | 28/300 production; 108/1200 rotations |
| Stop at highest supporting row | 7 / 15 | 13 / 44 | 2 / 11 | 22/300 production; 70/1200 rotations |
| Stop at lowest maximally wide row | 0 / 0 | 7 / 27 | 14 / 42 | 21/300 production; 69/1200 rotations |

Counts are separate rivals and must not be added as distinct failing lessons. Each first example was confirmed by executing its exact rival Racket program, with matches `[true, true, true, false]` against the three demonstrations and one query:

| Rival | Census band / index / seed / start | Instance SHA-256 | Rival Racket SHA-256 |
| --- | --- | --- | --- |
| Lowest cell | easy / 0 / 14290206 / 0 | `1d58a9a603551d876dc58d95e8a367bf9b93b9db84befe20a9031beeac1c1ca8` | `3f55124500de539af84e8fdb15b140374d6348533b11436984c21c285413e304` |
| Highest support | easy / 32 / 1772946884 / 32 | `36e771e62114a1688b0da48b496669a44e4e6aed71fd45c098637e507d3ff591` | `1c844821d59f795ef789f0938277779e14f0669bb91bc32f1e69e5cf951c9a91` |
| Lowest maximum width | medium / 11 / 1084611210 / 11 | `258d2c8729f756947e17ffbcdcf8f036b379d0df748ba187f459782e667736f1` | `be041ccf5acf8a4359e65e8f37e689efb7a0f2ee0202249963c11c839fa4b445` |

The highest-support and lowest-maximum-width rivals also match all four canonical pairs (Racket verified). They belong in `CANONICAL_SHORTCUTS` as well as lesson rivals. Lowest-cell does not match the canonical tail example but still creates genuine generated-lesson ambiguity.

Recommended fix: retain the same rule but schedule multiple separating demonstrations for each rival. A wide component with an upper width-3 row, a lower width-2 row and a one-cell tail separates all three; keep a disconnected projection-overlapping singleton. Packing must reserve its width and five vertical rows, and still preserve canonical linked profiles. Re-run source-bound teaching evidence after the sampler change. Until repaired, zero-ambiguity claims must be explicitly limited to the original declared projection rival and cannot satisfy the general teaching criterion.

### I2. Capacity 2/3 prototype did not teach row-count versus bounding-box width — resolved in rechecked prototype

Original location: retained v1 `prototype.py:175–188` rival inventory and `:229–239` sampler. The first two demos contained no staircase; odd queries did. Rival rule: allow floor passage when the component bounding-box width is at most capacity; otherwise retain canonical alignment at the lowest row containing more than one cell. This interpretation is equivalent to the canonical rule at capacity 1 for four-connected components.

At seed 17, two demos and four queries, original capacities 2 and 3 both yielded demo matches `[true, true]` and query matches `[true, false, true, false]`. The old episodes and source remain in `checks/parametric/prior/v1/`; the new regression's red result is `checks/parametric/tests-bbox-red.log`.

The corrected source makes demo 0 a staircase and declares this Racket rival at capacities 2 and 3. Independent re-execution at source `7c8d4db5...` confirmed demo 0 refutes it in both settings; rival inventories are 6/7/7 with no survivors, and every episode still has two demos and four distinct query inputs. Default exact Racket is unchanged. Current evidence is `checks/parametric/episodes-s17-v2/`. This finding is resolved for the reported example and structurally addressed for the sampler's fixed first demonstration.

## Minor

Both items below were corrected and rechecked at final generator SHA `b0988612...`.

At initial generator SHA `e87aab78...`:

- `generator.py:70–71` still describes default dimensions as 7..24 although `_band_params` now uses hard 15..30. Documentation mismatch only; declared valid bounds are correct.
- `generator.py:493–494` calls `math.isfinite` before the range check. `generate(0, 0, thin_frac=10**1000)` rejects the invalid value with `OverflowError: int too large to convert to float` rather than the intended `ValueError`. Check `0 <= fraction <= 1` before `isfinite`, or avoid converting arbitrary-size integers. This does not accept an unlawful draw.

## Exact Racket reproduction

Run from the outer packet directory (review execution used `/dev/shm/arcpuzzles-1dd86c403428`). This reads only retained generator/prototype lesson evidence and canonical authoring authority, not solve labels. The complete reproduction block below was executed verbatim and exited 0.

For the compact return, first follow `EVIDENCE_RETENTION.md`: extract the official `EVIDENCE-BUNDLE.tar.gz`, then restore historical `checks/lesson-census.json` from `checks/retained/lesson-census-v1.json.gz`. The final `checks/lesson-census-v2.json` remains raw inside the official evidence bundle. The retention map records original paths, sizes and hashes. These storage changes do not alter the source-bound observations below.

```bash
python3 review.py run python3 - <<'PY'
import importlib.util, json
from pathlib import Path
path = Path('generators/dc155169ea57/workspace/parametric/prototype.py')
spec = importlib.util.spec_from_file_location('peer_capacity', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
base = m.canonical_program()
programs = {
    'lowest_cell': m.replace_once(base, '(- (- red-row 1) (max-list wide-rows))', '(- (- red-row 1) rmax)'),
    'highest_support': m.replace_once(base, '(max-list wide-rows)', '(min-list wide-rows)'),
    'lowest_maximum_width': m.replace_once(base, '(max-list wide-rows)', '(max-list (filter (lambda (rr) (= (row-count rr) (max-list (map row-count wide-rows)))) wide-rows))'),
}
locations = {'lowest_cell': ('easy', 0), 'highest_support': ('easy', 32), 'lowest_maximum_width': ('medium', 11)}
census = json.loads(Path('../checks/lesson-census.json').read_text())
assert census['generator_sha256'] == 'e87aab78b168d29156d3b4e4b4222a81a5606e4858d4ab1b9c8c1c09cabe2567'
with m.RuleOracle() as oracle:
    for name, program in programs.items():
        lesson = next(row for row in census['lessons'] if (row['band'], row['index']) == locations[name])
        pairs = lesson['instance']['train'] + lesson['instance']['test']
        print(name, m.sha256_text(program), [oracle.apply(program, pair['input']) == pair['output'] for pair in pairs])
    for capacity in (1, 2, 3):
        prefix = Path('../checks/parametric/prior/v1/episodes-s17') / ('episode-%02d' % capacity)
        public = json.loads(Path(str(prefix) + '-challenge.json').read_text())
        private = json.loads(Path(str(prefix) + '-private.json').read_text())
        rival = m.replace_once(m.materialize_rule(capacity), '(> (row-count rr) %d)' % capacity, '(> (row-count rr) 1)')
        rival = m.replace_once(rival, '(null? wide-rows)', '(<= (+ (- cmax cmin) 1) %d)' % capacity)
        print('bbox', capacity,
              [oracle.apply(rival, pair['input']) == pair['output'] for pair in public['train']],
              [oracle.apply(rival, pair['input']) == answer for pair, answer in zip(public['test'], private['query_outputs'])])
PY
```

## Declined to judge

- Blind or post-repair solve correctness; private solve labels were not inspected.
- Human difficulty calibration, training admission, and universal rule identifiability. Finite rival checks do not establish those claims.
- Final archive/patch replay, fresh-checkout test receipt, overall audit completeness, or final report consistency; these are being handled separately by the parent reviewer.
- Source modifications after the hashes stated here until explicitly rechecked below.

## Initial assessment before final repair

The initial canonical repair successfully refutes projection grouping and improves override handling, but its general teaching adequacy is blocked by I1. The capacity-prototype I2 defect has been repaired and independently rechecked. Preserve historical findings and failed materialized lessons; after the canonical repair, bind new checks to the new source and append the final disposition here.


## Final assessment after v3.4.0 repair

**I1 resolved for the four declared rival interpretations and the tested sampler policies.** The replacement witness has a >=3-cell upper row, a 2-cell lower support row, a 1-cell tail, and a detached projection-overlapping singleton. Both vertical orders are scheduled. Packing reserves at least three columns for scheduled wide donors and five rows above the barrier before drawing sizes/counts; existing canonical linked forms fit these budgets. Explicit diagnostic overrides retain their independent paths. A different singleton/tail column prevents the passage hole from erasing the tail evidence. The input geometry therefore separates projection grouping and all three support-row alternatives in each witness slot.

Independent final probes, executed through `python3 review.py run python3 -` from `/dev/shm/arcpuzzles-1dd86c403428`, both exited 0:

- Repeated the exact 750-case override domain described above: 576 lawful exact returns, 174 marked count/width incompatibilities, zero unexpected results. Huge integer, NaN and infinity fractions all reject with `ValueError`.
- Replayed the three previously failing lesson coordinates plus hard seed 14/start 0, on the final generator. The resulting four groups of four distinct inputs each contain at least two refutations of every declared rival. Executed 64 Racket grid calls: 16 canonical labels and the same inputs under the three exact support-row rivals. Python mirrors and all support-rival implementations agree with those Racket outputs. The actual grid coordinates were easy seed 14290206/start 0, easy seed 1772946884/start 32, medium seed 1084611210/start 11, and hard seed 14/start 0.

The completed parent-run receipts were independently opened and their source bindings checked:

| Evidence | Verified result |
| --- | --- |
| `checks/final-v2/result.json` | completed, exit 0, passed; 12/12 green, zero advisory/failed/interrupted/pending stages; generator SHA `b0988612...` |
| `checks/task-tests-final/result.json` and `RUNTIME_MANIFEST.json` | completed, exit 0; stdout reports 22 tests and 86 subtests passed (receipt counts 108 cases); zero failures/errors/skips; generator and prototype hashes match final reviewed sources |
| `checks/lesson-census-v2.json` | 300/300 materialized production lessons, 1,200 query rotations; zero ambiguities/errors/warnings against four unique declared rivals; 1,131 unique inputs; exact final generator hash |
| `checks/schedule-census-v2.json` | all four cyclic starts in each of three bands: 12 lessons and 48 rotations; zero ambiguity or execution errors against four unique rivals; exact final generator hash |
| `checks/four-query-v2/summary.json` | pass for easy/medium/hard; each has 3 demonstrations, 4 queries, 7 distinct inputs, and all labels agree with Racket; no rival ambiguity; exact final generator hash |
| `checks/parametric/episodes-s17-v2/` | independently rebuilt 2-demo/4-query episodes; capacities 1/2/3 refute 6/7/7 rivals respectively; bbox competitor refuted by demonstration 0 at capacities 2/3; exact default authority preserved |

The canonical rule is unchanged, both Important findings are resolved in the reviewed code, and the two Minor findings are corrected. No further code repair is requested by this review. This is a bounded finite-rival and implementation assessment; final ZIP replay, report consistency, training admission, universal identifiability, and private solve scoring remain outside this independent review.
