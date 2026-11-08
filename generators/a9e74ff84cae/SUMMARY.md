# a9e74ff84cae

0-bg grid (h~11-14, w~12-16) with: (a) ONE FRAME of border_color drawn as a full rectangle outline at (r0, c0)..(r1, c1) of size frame_h × frame_w (6-8 × 5-7), placed by POSITION_BIAS (centered/corner/near_edge/anywhere); (b) NOISE CELLS in palette colors (warm/cool/broad/primary) at density 0.3-0.55, EXCLUDING the border. The border color uniquely forms a ≥80%-complete rectangular border ≥8 cells. Rule (FIND FRAME COLOR + CROP INTERIOR): SCAN colors 1..9 in order. For each color, COMPUTE its cells' bbox. CHECK if the cells form ≥80% of the bbox perimeter (border match count * 5 > 4 * perimeter) AND have ≥8 cells. The FIRST color satisfying this is the FRAME COLOR. CROP to the INTERIOR of the frame's bbox (excluding border cells). Output: the cropped interior of the frame's bbox. Net: locate the boundary color, crop out its interior.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
