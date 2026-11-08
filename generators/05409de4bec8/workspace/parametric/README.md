# Proposed `rectangle_policy` extension for `05409de4bec8`

**Status: proposed, unapproved prototype.** It is isolated from the selected
production generator and does not change the canonical Racket authority.

| Parameter | Values | Canonical/default |
|---|---|---|
| `rectangle_policy` | `longer`, `both` | `longer` |

Both settings locate the unique structured four-cell target, erase the two dense
distractor colors, and draw full lines through exact target pairs. The canonical
`longer` setting keeps only the longer rectangle axis. The nearby `both` setting
draws both pair rows and both pair columns. Non-rectangle behavior is unchanged.
The setting is chosen once from the episode seed and held fixed for all pairs.

The default evidence command creates **five demonstrations and four distinct
rectangle queries**. At least two demo rectangles distinguish the settings, and
every query changes under the alternative. Every retained label and every rival
prediction is executed through the bundled offline Racket bridge; the Python
mirror is only a parity oracle.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/05409de4bec8/workspace/parametric/verify.py \
  --out ../checks/parametric/rectangle-policy-public-writer-v4 \
  --demo-count 5 --query-count 4
```

The output contains complete private episodes, byte-exact rule programs, a
same-input disagreement witness, Racket/runtime/source hashes, and opaque public
challenges. The writer uses the portable `reviewer_support` helpers to serialize
the exact visible bytes, names each file with the full SHA-256 of those bytes,
rejects duplicate visible payloads, preflights every destination before creating
any public file, and writes the complete batch in public-ID order. Hidden setting
enumeration therefore cannot determine public creation order, and a late filename
collision cannot leave a partial public batch. The setting-to-path map remains only in the private report; public files
omit settings, seeds, programs, private metadata, and query answers.

Retained correction evidence is in
`WORK/checks/parametric/rectangle-policy-public-writer-v4/`; the adjacent
`rectangle-policy-public-writer-v4-independent.json` checks exact file hashes,
visible-only payloads, the sorted public write plan, independent 5+4 counts, and
four distinct Racket-labelled queries per setting. The focused writer regressions
separately exercise actual call order, duplicate rejection, and all-path overwrite
preflight.

Limits: this is bounded evidence for two settings and two retained seeds, not a
production API, catalog approval, training admission, or proof against every
possible rival. The selected production generator and canonical Racket rule are
unchanged.
