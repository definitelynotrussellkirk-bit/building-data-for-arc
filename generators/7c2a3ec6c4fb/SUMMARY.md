# 7c2a3ec6c4fb

Square 0-background scenes contain 5, 7, or 9 separated 8-connected colored objects. Exact bbox crops form 2–4 distinct duplicated pairs plus one singleton. The singleton may be monochrome or multicolor and is constructed to share palette, histogram, geometry, bbox, or size signatures with a repeated class, so low-complexity uniqueness shortcuts are insufficient. Sparse five-object scenes use free placement and may include canonical-style line crops of length 4 or 5. About one third of answers require diagonal (8-neighbor) connectivity; a repeated class has the same connectivity so this cannot identify the singleton by itself. Output the exact colored bbox crop whose complete pattern occurs once.

Kind: `per_puzzle`. Reviewed version: `3.2.0`. Canonical rule hash: `38ad2c645d79`.
