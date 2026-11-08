# cc9cb1d8bea8

0-bg grid (h~11-13, w~12-14) with TOP-ROW anchor cells and 3-4 BODY COMPONENTS: (a) cell (0, 0) = k (1-indexed selector in [1..n]); (b) cell (0, w-2) = t1 (transform code 1-4); (c) cell (0, w-1) = t2 (second transform code 1-4); (d) remaining row 0 = 0; (e) BODY (rows 1..h-1) has n (3-4) isolated 4-conn components, each in a DISTINCT color from {2..9} with STRICTLY DISTINCT SIZES from {2, 3, 4, 5, 6, 7}. Rule (RANKED COMPONENT + COMPOSED TRANSFORM): SORT body components by (AREA DESC, COLOR ASC). PICK the k-th component in sorted order. CROP to its BBOX. APPLY transform t1 then t2 (transform codes: 1=rotate CW 90°, 2=rotate 180°, 3=flip-LR, 4=flip-UD). Output: the transformed crop. Net: k picks ranked blob, t1∘t2 applies composed geometric transform.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
