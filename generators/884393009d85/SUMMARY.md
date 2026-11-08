# 884393009d85

0-bg grid (h ∈ 12-16, w ≥ 10+n) with: (a) TOP KEY STRIP — rows 0 and 1 BOTH show the SAME color sequence: g[0][start_c+i] = g[1][start_c+i] = colors[i] for i in 0..n-1, where n ∈ 3-4 is key_length and colors are n DISTINCT non-bg colors drawn from {1..9}, anchored at start_c=2; (b) ONE COLORED TEMPLATE SHAPE below the key strip — fixed L-tromino [(0,0),(0,1),(1,0)] painted in colors[0] (the FIRST KEY COLOR), placed at base_r = 4 + (sample_index % 2), base_c = 3 + ((seed + sample_index) % 2). Rule (FOR EACH KEY COLOR IN ORDER, STACK A COPY OF THE TEMPLATE VERTICALLY — EACH COPY RECOLORED TO THE KEY COLOR; FIRST COPY AT TEMPLATE'S ORIGINAL POSITION, SUBSEQUENT COPIES AT VERTICAL OFFSETS = KEY-INDEX × TEMPLATE_HEIGHT): READ the key row's color sequence. FOR i in 0..n-1: PASTE the template shape (in colors[i]) at position (base_r + i × template_h, base_c). The key rows are removed from the output. Net: key sequence becomes a vertical stack of n recolored template copies.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
