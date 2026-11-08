## 0ab5dc1f5386

**Finding A1 — ordinary lessons can leave source scan order ambiguous (unresolved, medium).**

Audited version: `4.1.0`. Source SHA-256:
`a4b6e6fe9ddca55ec8349902dc6ae62d3b0a81b757c9bcb7e4ce401b083ad897`.
The current `evidence/review_index.json` identifies the same source, records a
reviewer-reported acceptance, and has no retained audits. No generator,
authority, shared-runtime, approval, or contract file was modified in this audit.

### Reproduction and observed result

Public production call:

```python
Catalog(repo).generate(
    "0ab5dc1f5386", count=1, seed=4, difficulty="medium",
    sample_index=1, n_train=4, n_test=1, timeout=180,
)
```

The runner accepts demonstration sample indices `[1, 2, 3, 4]` and query sample
index `5`, with **zero rejections**. This is a direct production episode; no
post-generation query rotation or withheld example is involved. All four
scheduled textures appear in the demonstrations. The declared-rival gate returns
`passed_declared_rivals`.

The concrete rival preserves frame detection, exact orientation-sensitive size
matching, source retention, multicolor copying, and value-based one-use. It
changes only candidate source order: scan loose source bounding boxes
**left-to-right, then top-to-bottom**, instead of canonical row-major component
order. `probe.py` implements this rival independently of the generator's
transformation helpers.

This rival agrees with **all five supplied canonical pairs** and **all four
Racket-labeled demonstrations**, but disagrees with the Racket query label in
five cells. In the decisive demonstration, the first matching source (color 2)
is both above and left of the alternative (color 7), so both source-order rules
choose it. In the query, the two orders conflict:

| Matching source | Top-left of source bbox, zero-based | Crop |
|---|---|---|
| Canonical first source | `(1, 14)` | `[[4,4,4],[0,0,4]]` |
| Rival first source | `(11, 4)` | `[[7,7,7],[7,0,0]]` |

The resulting differing output cells, zero-based, are:

| Cell | Racket | Rival |
|---|---:|---:|
| `(8,13)` | 4 | 7 |
| `(8,14)` | 4 | 7 |
| `(8,15)` | 4 | 7 |
| `(9,13)` | 0 | 7 |
| `(9,15)` | 4 | 0 |

Query input SHA-256:
`65b32aa56a634593d2df98f132fdb9da0509788ff69f090378fd44faab6888b1`.
Racket query output SHA-256:
`811b771678fc9719820d417eb47d1f04e74b2332e55d4876af38b9db842eb553`.

The same query failure also occurs with the default starting sample index `0`,
four demonstrations, and four queries: seed `4`, difficulty `medium`, accepted
indices `0..7`, no rejections, divergent query index `1` / sample index `5`.
This second episode establishes the multi-query impact without changing the
default starting index.

### Why the existing witness misses this

`scan_order` supplies two different equal-size sources and refutes `last_match`,
but does not require their horizontal and vertical orders to conflict. The other
three scheduled profiles do not distinguish this candidate-order rival. Thus a
full four-texture curriculum can teach the declared competitors while leaving
this simple canonical-fitting alternative viable on its query. The production
gate's status accurately describes its declared rival set; it does not clear
this newly reproduced ambiguity.

A targeted repair should add the left-to-right rival and construct a decisive
source-order witness in every relevant demonstration window, retaining the
canonical Racket semantics. This audit is findings-only; no repair is included.

### Source-bound execution evidence

`evidence/single_query_episode.json` contains the minimal production episode and
its sampling/provenance records. `evidence/episode.json` contains the four-query
episode. `evidence/apply_receipt.json` independently applies canonical Racket to
all eight generated inputs through public `Catalog.apply`, with generator-domain
checking requested: all eight outputs are present, all errors are null, and
all outputs equal the independent Python row-major oracle. The receipt binds:

- Generator SHA-256: `a4b6e6fe9ddca55ec8349902dc6ae62d3b0a81b757c9bcb7e4ce401b083ad897`.
- Catalog and executed normalized rule hash: `1529a4ef373b`, with `rule_hash_matches_catalog=true`.
- Exact canonical program text SHA-256: `22d4daaeb8b666b7cd3e7e279c1ba1717eaa582fcbc4f0b0c825376ec7ab7090`.
- Executed callable text SHA-256: `99229fee9a54e7a0b1182f5f04d9663bbf8b5023c728f6f8292e54764735604a`.

The last two hashes name different text representations; runtime wrapping
accounts for that distinction. Inputs, rival outputs, exact changed cells,
search settings, boundary settings, and hashes are retained in `evidence/`.

### Exact verification commands and status

1. Initial bounded Python probe — **exit 0**. Examined seeds `0..4` at medium
   difficulty and stopped at the first ordinary four-query counterexample.
   Also checked the 80 exact size-corner/texture/difficulty combinations.

```bash
PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/290f070f7ae5/.venv/bin/python /workspace/scratch/290f070f7ae5/audit-0ab5dc1f5386/probe.py --repo /workspace/scratch/290f070f7ae5/packet/WORK/repo --out /workspace/scratch/290f070f7ae5/audit-0ab5dc1f5386/evidence
```

2. Attempted Racket replay from the scratch source subset — **exit 1 before
   generator execution**, because that subset lacks
   `shared/data/derived/dsl_vocab.json`. This is an environment preparation
   failure, not a generator failure.

```bash
PYTHONDONTWRITEBYTECODE=1 RACKET_PATH=/workspace/scratch/290f070f7ae5/packet/WORK/.review/racket-runtime/racket/bin/racket /workspace/scratch/290f070f7ae5/.venv/bin/python /workspace/scratch/290f070f7ae5/audit-0ab5dc1f5386/probe.py --repo /workspace/scratch/290f070f7ae5/packet/WORK/repo --out /workspace/scratch/290f070f7ae5/audit-0ab5dc1f5386/evidence --execute
```

3. Source-bound Racket replay from the immutable complete extraction — **exit
   0**. The command was run twice: first for the four-query episode plus apply
   receipt, then after adding the minimal one-query replay to the probe. Both
   executions succeeded. The second run produced the final retained evidence.
   Host shared-memory access used the environment's escalation mechanism; all
   output remained in the scratch audit folder.

```bash
PYTHONDONTWRITEBYTECODE=1 RACKET_PATH=/workspace/scratch/290f070f7ae5/packet/WORK/.review/racket-runtime/racket/bin/racket /workspace/scratch/290f070f7ae5/.venv/bin/python /workspace/scratch/290f070f7ae5/audit-0ab5dc1f5386/probe.py --repo /dev/shm/arcpuzzles-062359-290f070f7ae5/WORK/repo --out /workspace/scratch/290f070f7ae5/audit-0ab5dc1f5386/evidence --execute
```

Portable replay uses the same `probe.py --repo COMPLETE_REPO --out NEW_DIRECTORY
--execute` interface with Python dependencies and `RACKET_PATH` configured.

### Scope and limitations

The finding is a finite, concrete lesson-identifiability failure. It is not a
claim of label/reference mismatch or illegal generated grids. Fresh Racket
evidence covers eight unique generated inputs, two production episode layouts,
and the public apply receipt. Canonical rival agreement was compared with the
five supplied canonical labels, not a fresh canonical-pair Racket execution.
The 80 boundary checks cover seed `31`, sample index `7`, all five textures,
difficulty `None/easy/medium/hard`, and size corners `(12,16)`, `(12,22)`,
`(18,16)`, `(18,22)`; these are Python construction/self-check/oracle checks,
not 80 Racket executions. They found no failed or dishonest exact-size override.
No full battery or prevalence estimate was attempted. The default start-0,
one-query episode does not expose this particular rival because its query is
`orientation_decoy`; the verified failure uses the ordinary cyclic start-1
one-query episode or the start-0 four-query episode described above.
