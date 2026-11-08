# 1282792eaad1

Fixed 7-row × 5-col 0-bg grid with: (a) ROWS 0..4 containing a 5×5 PROTOTYPE SHAPE (4-5 cells) in some source_color, drawn from a curated shape bank; (b) ROW 5, COLS 0..2 holding 3 TRANSFORM CODES (values 0..5 from a code table — each code maps to a specific rotation/reflection: 0=id, 1=cw90, 2=180°, 3=ccw90, 4=flip-lr, 5=flip-ud); (c) ROW 6, COLS 0..2 holding 3 OUTPUT COLORS (distinct from source_color). Rule: construct a CROSS-PRODUCT GALLERY OUTPUT — a 3×3 grid of TRANSFORMED PROTOTYPES, where output panel (i, j) contains the PROTOTYPE shape with TRANSFORM j applied and painted in COLOR i (from row 6). Output dimensions: 3*panel_h × 3*panel_w (each panel cell holds a 5×5 transformed prototype). Net: input teaches one shape + 3 transforms + 3 colors; output is the 3×3 cross-product gallery.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
