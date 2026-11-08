# dc59d4c62234

Grid with FULL-ROW SEPARATORS in some uniform non-bg color, partitioning the canvas into horizontal BANDS of equal height N. The border rows (top and bottom) are also separator-colored. Each band's height equals the SQUARE BLOCK SIZE N for that band. Inside each band, 2 SOLID N×N SQUARES are placed in two distinct colors against a noisy filler of other colors (any color except the separator color and the square colors). Rule: scan band-by-band top-to-bottom. For each band, DETECT the K solid N×N SQUARES inside (each in a distinct color) in left-to-right order. EMIT a 1-row sequence of those K square-colors. Output: BANDS rows × K cols, one cell per square's color. Net: the separator-bound bands get reduced to a compact (bands × K) lookup table of solid-square colors.

Kind: `per_puzzle`. Imported version: `2.1.2`.
Approval is derived by the catalog from current code and retained evidence.
