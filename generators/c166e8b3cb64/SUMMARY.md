# c166e8b3cb64

0-bg grid (h, w varies by difficulty: 9×11 / 10×13 / 14×16) with: N_COMPS ∈ 2-4 SEPARATED 4-CONNECTED COMPONENTS, each painted in a DISTINCT color drawn from {1..9}, each as a solid rectangle filling a subset of size cells (rectangle dimensions chosen to approximately match each component's size). The LARGEST component has size LARGE_SIZE (6-14 by difficulty); other components have strictly smaller sizes (decreasing by 2 per component). Components placed with gap ≥2 between bboxes. Rule (FIND THE 4-CONNECTED COMPONENT (UNDER 'NON-ZERO' PREDICATE) WITH THE LARGEST CELL COUNT; TIE-BREAK BY EARLIEST BBOX TOP-LEFT (SMALLER R, THEN SMALLER C); CROP THE INPUT TO THAT COMPONENT'S BBOX; OUTPUT THE CROP — CELLS IN THE COMPONENT PRESERVE THEIR COLORS, BBOX HOLES ARE 0): EXTRACT every non-bg component. SORT by (-cell_count, min_r, min_c). PICK first. CROP input to its bbox. OUTPUT. Net: largest component extracted with its original colors in a tight bbox crop.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
