# Working notes: fd588326c845

## 2026-10-24 native parametric review

- Source remains `VERSION=3.0.0`, generator SHA-256 `50abfbe525d58670a719575286237fb09e7f7faaacbe99aec89e21e35bf0fb4f`, canonical rule hash `857ce489e943`; the production generator and canonical Racket rule were not changed.
- The native adapter preserves the exact canonical `clockwise` program as its default and adds one episode-fixed `anchor_directed` setting.
- `anchor_directed` first finds the unique singleton key color and classifies its cell as top- or bottom-half; that intermediate selects clockwise or counterclockwise; the selected direction then determines which key coordinate supplies every expanded-tile color.
- Inputs are setting-neutral. Occupancy is 180-degree symmetric so the two directions have the same silhouette, while asymmetric key colors force different labels. The first two demonstrations exercise opposite anchor halves.
- Contract: 2–6 demonstrations, exactly four distinct queries, deterministic local RNG, exact integer grids, and a substantive final 30x30 query touching all four boundaries.
- Native qualification passed for both settings at seeds 0 and 17 with protected-Racket labels. The causal witness replays a bottom-anchor query and shows that forcing the wrong clockwise intermediate changes the final grid.
- Bounded self-audit covered minimum/maximum demo counts, declared finite rivals, public/private projection invariance, deliberate query-label leakage rejection, and 32 additional protected-Racket evaluations.
- Limits: finite seeds and declared rivals do not prove universal identifiability or training gain. Reviewer status is `ready`, not accepted or training-admitted.
- Next action: after integrating these exact bytes, the owner must rerun native qualification and fresh acceptance on the live source before admission.
