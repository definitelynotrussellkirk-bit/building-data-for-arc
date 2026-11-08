# Working notes: 42f19ef6d600

## 2026-10-23 — proposed `branch_map` extension

- Production `generator.py` remains unchanged at SHA-256 `5ae59775e9c62462d8eb9ac741dd310246be3e5a6e9496fc88eca8bd1c649477`; the canonical normalized rule hash remains `07ef8e3cc031`.
- Added a task-local, episode-fixed `branch_map` prototype: `canonical` maps solid square-bbox objects to exterior side strips and non-solid objects to corner-adjacent marks; `swapped` exchanges those two branches while preserving segmentation, square detection, color, clipping, and blocked-cell behavior.
- Canonical Racket stays byte-identical to the ledger (`dc177e343a8ee842c8429c04d04ee9a33786f6724242c978984fa856d5f2d029`). The proposed swapped Racket is `581e2a427a20650e56c4e33532028240e1f64aa2bbef2f4ebf4e9531afd606a6` / normalized `c560f66f174a`.
- The staged canonical test loader now uses `reviewer_support.find_root/canonical_path`; base-vs-canonical authority comparison is whitespace-normalized because the two retained programs differ only in formatting.
- Public challenges now use exactly `reviewer_support.public_challenge_bytes` and the full `public_challenge_id`; hidden setting/seed/profile metadata and query answers are absent. The private verifier replays deterministic sampler provenance before protected-Racket parity checks.
- Retained seed `1701` episodes have four demos and four distinct queries each, eight Racket labels each, Python parity on all pairs, and demonstration rejection of both `always_side_strips` and `always_corner_marks` shortcuts.
- The 2×2 solid profile is intentionally excluded from parameter queries: side strips and corner marks collapse to the same eight cells there, so it cannot supervise this hidden setting. Production coverage of that boundary is unchanged.
- This is proposed prototype evidence only: no catalog approval, production parametric API, canonical relabeling, or training admission. A useful next action is maintainer review followed by a broader seed sweep only if promotion is desired.
