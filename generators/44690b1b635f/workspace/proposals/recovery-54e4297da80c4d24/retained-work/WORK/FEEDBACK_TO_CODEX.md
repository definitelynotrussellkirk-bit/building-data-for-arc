# Feedback to Codex

## F1: Add a normalized-topology/template-predictability gate (highest priority)

**Symptom:** exact-grid diversity and color coverage can look healthy while the
semantic geometry is a tiny lookup table. Task `44690b1b635f` v3.0.0 had only 42
normalized role masks, and a retained lookup reproduced 768 sampled outputs.

**Evidence:** `checks/recovery/diversity-census.json` shows the repair increases
a normal 800-draw band from the fixed-mask regime to 59 wall topologies, 47 of
them fresh procedural layouts, without reducing public-anchor frequency below
the previous test envelope.

**Suggested change:** sample 128–256 lessons per band, normalize colors into
roles, report unique topology ratio and held-out exact/nearest-template
accuracy, and block only the conjunction of tiny support and very high lookup
accuracy. Keep an explicit anchor-curriculum exception rather than disabling the
gate globally.

## F2: Support chunked rematerialization or resumable extraction for large packets

**Symptom:** after a runtime reset, the 350 MB uploaded ZIP remained visible to
the file service but could not be materialized because of a hard 100 MB limit;
the previously verified 2.2 GB extraction and official journals were lost.

**Suggested change:** expose chunked byte ranges, a mounted immutable upload
path, or a resumable extraction artifact. The supplied
`tools/replay_in_full_packet.py` demonstrates the required safety properties:
assignment check, preimage hashes, atomic writes, backups, and post-copy hashes.

## F3: Randomized allocation/data-quality audit — exact packet sample pending

Assignment seed:
`d29c972914db3fb8577bd8fa12b00f498c07884908f524cb4d21f015c50be87f`.
The exact three IDs cannot be honestly named without the packet's
`PACKET-MANIFEST.json`; no substitute IDs were guessed. Run:

```bash
python tools/sample_allocation_audit.py \
  --manifest WORK/PACKET-MANIFEST.json \
  --seed d29c972914db3fb8577bd8fa12b00f498c07884908f524cb4d21f015c50be87f \
  --out WORK/checks/recovery/allocation-sample.json
```

For the selected task alone, the observed allocation trade-off is concrete:
uniform 1/17 procedural sampling produced 47 unique new topologies in 800 draws
per band at no extra label API cost, while retaining 151 public-anchor draws.
A bounded alternative is to test a 20% procedural share against the current
5.9% share for 400 draws per band. Compare normalized-new-layouts per Racket
call, lesson-rival pass rate, dedup rejection, and review minutes. Stop if the
20% arm improves unique accepted layouts per cost by less than 10%, reduces any
canonical-profile floor, or increases ambiguity/rejection by more than 5%.
This is a proposal only; it changes no draw policy or admission status.
