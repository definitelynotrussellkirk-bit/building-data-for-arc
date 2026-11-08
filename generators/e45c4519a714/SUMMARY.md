# e45c4519a714

Grid h × (3*pw + 2) (h~4-5, pw~4-5) with: (a) two full-height color-8 (cyan) DIVIDER columns at col pw and col 2*pw+1, splitting grid into 3 equal panels (A, B, C). Panels A and B share the SAME 3-4 cell shape (but in different colors); panel C uses a different shape (and color). Rule: extract the 3 panels by subgrid; binarize each (non-bg → 1). Output is a 3×3 PAIRWISE MASK-EQUAL MATRIX where out[i][j] = 1 if panels[i].binary == panels[j].binary (under normalization). With the generator's A==B, A!=C, B!=C structure, output is always [[1,1,0],[1,1,0],[0,0,1]].

Kind: `per_puzzle`. Imported version: `2.3.0`.
Approval is derived by the catalog from current code and retained evidence.
