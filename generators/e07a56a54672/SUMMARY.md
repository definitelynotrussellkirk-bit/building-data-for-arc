# e07a56a54672

0-bg grid (h ∈ 9-14, w ∈ 11-16, by difficulty) with: EXACTLY TWO COLOR-3 (GREEN) CONNECTED MOTIFS of STRICTLY DIFFERENT SIZES — drawn from SIZE_PAIR (e.g., (2, 4) for easy/medium, (3, 6) for hard) shuffled, each motif built via _build_motif random adjacent-step walk, placed at non-overlapping positions via _free check (1-cell padding). Both motifs painted in COLOR 3 only. Retries up to 40 outer × 120 inner attempts. Rule (FIND THE SMALLER OF THE 2 COLOR-3 MOTIFS, SCALE IT 2× (EACH CELL → 2×2 BLOCK), RECOLOR THE SCALED COPY TO COLOR 8 (CYAN); LARGER MOTIF DISCARDED): EXTRACT both COLOR-3 components and compute their cell counts. SELECT the SMALLER one (with fewer cells). UPSCALE its cells by factor 2: each (r, c) in the original becomes a 2×2 BLOCK at (2r..2r+1, 2c..2c+1). PAINT every cell of the upscaled shape with COLOR 8 (cyan). OUTPUT the scaled cyan crop (on a fresh canvas sized to the scaled bbox). Net: smaller motif is enlarged and recolored cyan; larger motif is gone.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
