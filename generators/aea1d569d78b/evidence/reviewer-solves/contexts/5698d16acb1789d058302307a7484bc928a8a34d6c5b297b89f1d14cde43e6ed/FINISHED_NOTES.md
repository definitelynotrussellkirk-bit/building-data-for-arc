# Solve notes — aea1d569d78b

This is a human work log from the visible examples. I had already seen and repaired this task's generator and authority before this required post-repair episode, so this is **not blind**; I did not reopen the generator, Racket source, reference labels, or private query answers during the episode.

## Visible evidence

- Train 0: the blue cells at column 5, rows 1 and 7 are joined vertically by green because every interior cell is zero. The two blue cells on row 6 are also joined horizontally. The apparent row-0/row-3 blue pair at column 9 is blocked by color 6 at row 1, so it is not joined.
- Train 1: column 2 is joined between rows 2 and 5; row 3 is joined only between its two blue cells at columns 7 and 9. The row-9 blue endpoints are not joined because color 4 lies between them.
- Train 2: row 4 and column 7 are joined. Row 5 is blocked by color 9 between its blue endpoints.

## Hypothesis

For each row and each column independently, find lines containing exactly two blue (1) cells. If every cell strictly between the endpoints is background 0 in the original input, recolor those interior cells green (3). Keep endpoints and distractor colors unchanged. Use the original input for both directional tests so newly written green cells do not block another valid segment.

## Query expectations

- Query 0: join row 4, columns 0–4; join column 3, rows 2–7; do not join row 6 because color 4 blocks its two blue endpoints.
- Query 1: join row 2, columns 3–6; join column 5, rows 0–8; do not join row 3 because color 2 blocks its two blue endpoints.
