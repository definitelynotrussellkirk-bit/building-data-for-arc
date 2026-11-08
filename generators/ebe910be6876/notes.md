# Working notes: ebe910be6876

## 2026-10-23 review-e2074fc131195d42

- **Production decision:** keep `generator.py`, canonical magnification `2`, rule hash `74026dfb3e5c`, and the intentional odd-coordinate marker support unchanged. The retained audit's snapped-lattice shortcut is therefore still an explicit limitation, not a repaired defect.
- **Proposed parameter:** task-local hidden integer `magnification ∈ {1,2,3}`, selected once per complete episode. Setting `m` maps an `h×w` input to `mh×mw`; each marker at `(r,c)` paints a clipped `2m×2m` tile from `(mr-m, mc-m)`. Default `m=2` is exactly the canonical rule.
- **Episode contract:** three demonstrations and four distinct queries by default; counts are exposed separately, total pairs are capped at 24, and input sides are restricted to 6..10 so `m=3` stays within 30×30. Every retained pair distinguishes all three settings.
- **Public/private contract:** exported challenges contain demonstration inputs/outputs and query inputs only. Filenames are opaque `challenge-<sha256>.json` IDs computed from exactly the visible bytes; hidden setting, program, metadata, and query answers do not affect the ID.
- **Retained evidence:** `workspace/parametric/evidence/retained/manifest.json` records one episode per setting, exact Python/Racket parity for 21 intended outputs and 42 rival outputs, all 42 rival refutations, four setting-sensitive queries per episode, source hashes, and replay command. Summary receipts are under `WORK/checks/parametric/`.
- **Portable-test repair:** `tests/test_generator_ebe910be6876.py` now resolves canonical data through `reviewer_support.find_root/canonical_pairs` instead of a fixed `__file__` parent depth, and uses the public `GenCtx` provenance API instead of deprecated private aliases. This changes no generator behavior and makes the copied-runtime task tests pass cleanly.
- **Unresolved:** evidence covers three retained episodes rather than every seed; the production odd-lattice support still admits the previously documented snapping shortcut.

## Current prototype public write-order follow-up

Public filenames match exact visible bytes, but physical writes precede report-row sorting. Preserve code/Racket evidence; precompute and sort the full batch before writing, with one focused regression. No variant or training approval. Static receipt: `generators/ebe910be6876/evidence/parametric-export-inspection-e2074fc131195d42/manifest.json`.

## 2026-10-25 review-ef69e363d8c5bcd4

- Replaced the retained scalar magnification proposal with a native two-setting
  family: exact canonical `finish=expand_only` and sequential
  `finish=mark_largest_cluster`.
- The alternative first builds the canonical doubled tile canvas, then
  recomputes four-connected nonzero components and recolors the unique largest
  result to 9. Component contacts and sizes are produced by the expansion, so
  the second decision cannot be made from the original isolated markers.
- Kept production `generator.py` and the selected canonical authority unchanged.
  `canonical.rkt` is byte-identical to the ledger program with SHA-256
  `2c453a5303bbcb8a448c51fdbb03f734d935eb44cfe39d85751094749132068c`.
- Repaired the inherited public-write-order defect at the filesystem boundary:
  all visible payloads/IDs are validated before writes, duplicate visible
  challenges reject, and 16 files are physically emitted in sorted public-ID
  order. The replacement correction record preserves the old finding and binds
  the new writer, regression, exact bytes, and protected-Racket replay.
- Finite teaching audit: two settings × seeds 0 and 17, 72 protected-Racket
  evaluations, four declared rivals, and no harmful survivor. Structural sweep:
  128 seeds, 1,280 inputs, 2,560 labeled pairs, and 1,024 public turns with no
  recorded failure.
- Native qualification passed four jobs with three demonstrations and four
  queries each (40 protected-Racket labels). Strict projection produced 16
  one-query public files. The wrong-intermediate causal witness was independently
  replayed and changed the final output.
- Current boundary: reviewer-ready only. Exact-source owner integration, fresh
  qualification/acceptance, and training admission remain pending.
