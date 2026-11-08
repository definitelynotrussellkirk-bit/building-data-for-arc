# Native parametric family for `bf9e0959b8ce`

The finite episode parameter is `rule_mode`:

| Value | Meaning |
|---|---|
| `canonical` | Exact selected Racket rule, byte-for-byte. Matching source dots route near the separator; mismatches route to the far edge. |
| `near_count_relay` | First perform the canonical routing. Count the routed dots on the near edge. Use that count (1, 2, or 3) to select the corresponding far-edge routed dot in aligned-coordinate order, then move that selected dot one cell inward. |

The second mode has an explicit sequential dependency:

1. **A:** canonical separator/key routing creates near-edge and far-edge results.
2. **Intermediate:** the number of occupied near-edge result cells.
3. **B:** the intermediate indexes the ordered far-edge result candidates; the selected candidate is relayed inward.

The input sampler is shared between settings and produces six stable demonstration
profiles plus four stable query profiles. Requesting fewer items takes a prefix,
so query one is identical whether one or four queries are requested. The first two
demonstrations cover row and column orientations and different intermediate
values. The fourth query is a 30×30 boundary case with candidates on both aligned
extremes.

Private settings, programs, future queries, query answers, and total-query hints
are not included by `public_challenge`.

Focused authoring audit:

```bash
python3 review.py run python3 \
  generators/bf9e0959b8ce/workspace/parametric/verify.py \
  --out generators/bf9e0959b8ce/workspace/parametric/evidence/current/audit.json
```

Native qualification:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify bf9e0959b8ce \
  --out ../checks/bf9e0959b8ce/qualification --summary
```

The returned artifacts are reviewer-prepared only. Owner-side exact-source
qualification and acceptance remain required; no training admission is implied.

## Public artifact note

`public/episode-a.json` and `public/episode-b.json` are unchanged baseline artifacts from the superseded swap-only proposal. The no-deletion review format requires retaining them, but they are **not** current exports. The current public challenges are the two 64-hex SHA-256 filenames listed in `evidence/current/audit.json`; `evidence/current/public-export-check.json` validates those files explicitly.
