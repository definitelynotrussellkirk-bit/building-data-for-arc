"""
Grid-to-image renderer for multimodal REPL sessions.

Produces PIL Images of grids, diffs, and side-by-side comparisons.
Used in traces for vision-language model training and inference.
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ARC color palette (RGB)
ARC_PALETTE = {
    0: (0, 0, 0),        # black
    1: (0, 116, 217),    # blue
    2: (255, 65, 54),    # red
    3: (46, 204, 64),    # green
    4: (255, 220, 0),    # yellow
    5: (170, 170, 170),  # grey
    6: (240, 18, 190),   # magenta
    7: (255, 133, 27),   # orange
    8: (127, 219, 255),  # cyan
    9: (135, 12, 37),    # maroon
}

DIFF_WRONG = (255, 0, 0)      # red overlay for wrong cells
DIFF_CORRECT = (40, 40, 40)   # dim for correct cells
GRID_LINE = (60, 60, 60)      # grid lines
LABEL_BG = (30, 30, 30)       # label background
LABEL_FG = (200, 200, 200)    # label text


def grid_to_image(grid, cell_size=20, border=1, label=None):
    """Render a single grid as a PIL Image with colored cells.

    Args:
        grid: list-of-lists of ints (0-9)
        cell_size: pixel size of each cell
        border: grid line width
        label: optional text label above the grid

    Returns:
        PIL.Image
    """
    if isinstance(grid, np.ndarray):
        grid = grid.tolist()

    h = len(grid)
    w = len(grid[0]) if h > 0 else 0

    img_w = w * (cell_size + border) + border
    img_h = h * (cell_size + border) + border
    label_h = 20 if label else 0

    img = Image.new("RGB", (img_w, img_h + label_h), GRID_LINE)
    draw = ImageDraw.Draw(img)

    # Draw cells
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            color = ARC_PALETTE.get(v, (128, 128, 128))
            x1 = c * (cell_size + border) + border
            y1 = r * (cell_size + border) + border + label_h
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            draw.rectangle([x1, y1, x2, y2], fill=color)

    # Label
    if label:
        draw.rectangle([0, 0, img_w, label_h], fill=LABEL_BG)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
        except Exception:
            font = ImageFont.load_default()
        draw.text((4, 2), label, fill=LABEL_FG, font=font)

    return img


def diff_image(got_grid, expected_grid, cell_size=20, border=1):
    """Render a diff image: correct cells dimmed, wrong cells highlighted red.

    Returns PIL.Image showing the diff overlay.
    """
    # Unwrap Grid objects if needed
    if hasattr(got_grid, 'data'):
        got = np.array(got_grid.data)
    elif isinstance(got_grid, list):
        got = np.array(got_grid)
    else:
        got = np.array(got_grid)
    if hasattr(expected_grid, 'data'):
        exp = np.array(expected_grid.data)
    elif isinstance(expected_grid, list):
        exp = np.array(expected_grid)
    else:
        exp = np.array(expected_grid)

    if got.shape != exp.shape:
        # Shape mismatch — show both side by side
        return pair_image(got_grid, expected_grid, cell_size, border,
                         left_label="Got", right_label="Expected")

    h, w = got.shape
    img_w = w * (cell_size + border) + border
    img_h = h * (cell_size + border) + border + 20

    img = Image.new("RGB", (img_w, img_h), GRID_LINE)
    draw = ImageDraw.Draw(img)

    # Label
    draw.rectangle([0, 0, img_w, 20], fill=LABEL_BG)
    n_diff = int((got != exp).sum())
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
    draw.text((4, 2), f"Diff: {n_diff}/{got.size} wrong", fill=DIFF_WRONG if n_diff else (0, 255, 0), font=font)

    for r in range(h):
        for c in range(w):
            x1 = c * (cell_size + border) + border
            y1 = r * (cell_size + border) + border + 20
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            if got[r, c] == exp[r, c]:
                # Correct — show dimmed expected color
                base = ARC_PALETTE.get(int(exp[r, c]), (128, 128, 128))
                color = tuple(max(0, v // 3) for v in base)
            else:
                # Wrong — show got color with red border
                color = ARC_PALETTE.get(int(got[r, c]), (128, 128, 128))
                draw.rectangle([x1-1, y1-1, x2+1, y2+1], outline=DIFF_WRONG, width=2)

            draw.rectangle([x1, y1, x2, y2], fill=color)

    return img


def pair_image(input_grid, output_grid, cell_size=20, border=1,
               left_label="Input", right_label="Output", gap=10):
    """Render input → output side by side.

    Returns PIL.Image.
    """
    left = grid_to_image(input_grid, cell_size, border, left_label)
    right = grid_to_image(output_grid, cell_size, border, right_label)

    total_w = left.width + gap + right.width
    total_h = max(left.height, right.height)

    combined = Image.new("RGB", (total_w, total_h), (20, 20, 20))
    combined.paste(left, (0, 0))
    combined.paste(right, (left.width + gap, 0))

    # Arrow
    draw = ImageDraw.Draw(combined)
    arrow_x = left.width + gap // 2
    arrow_y = total_h // 2
    draw.text((arrow_x - 3, arrow_y - 6), "→", fill=LABEL_FG)

    return combined


def task_image(task, cell_size=16, border=1, max_pairs=4):
    """Render all training pairs for a task as one image.

    Shows: pair 0 input → output, pair 1 input → output, etc.
    Returns PIL.Image.
    """
    pairs = task["train"][:max_pairs]
    pair_images = []

    for i, pair in enumerate(pairs):
        img = pair_image(pair["input"], pair["output"], cell_size, border,
                        f"Train {i} In", f"Train {i} Out")
        pair_images.append(img)

    # Add test input
    for i, pair in enumerate(task["test"][:1]):
        img = grid_to_image(pair["input"], cell_size, border, f"Test {i} In")
        pair_images.append(img)

    if not pair_images:
        return Image.new("RGB", (100, 100), (0, 0, 0))

    # Stack vertically
    total_w = max(img.width for img in pair_images)
    gap = 8
    total_h = sum(img.height for img in pair_images) + gap * (len(pair_images) - 1)

    combined = Image.new("RGB", (total_w, total_h), (20, 20, 20))
    y = 0
    for img in pair_images:
        combined.paste(img, (0, y))
        y += img.height + gap

    return combined


def render_puzzle(puzzle, *, cell_px=24, border=1, gap=10,
                  show_test_output=False):
    """Canonical training-data renderer. ONE function, deterministic,
    cheap.

    Layout (top-to-bottom):
      ┌────────────┬────────────┐
      │ Train 0 In │ Train 0 Out│
      ├────────────┼────────────┤
      │ Train 1 In │ Train 1 Out│
      ├────────────┼────────────┤
      │   ...      │            │
      ├────────────┴────────────┤
      │ Test 0 In  ( | Test Out)│  ← test output only if show_test_output
      └─────────────────────────┘

    Args:
      puzzle: dict with "train": [{input, output}, ...] and
              "test": [{input[, output]}, ...]
      cell_px: pixel size of each grid cell (default 24).
      border: grid line width in pixels (default 1).
      gap: vertical pixel gap between rows (default 10).
      show_test_output: include the test pair's output. Default False
                       (the test output is what the model is asked to
                       produce; showing it would be cheating).

    Returns:
      PIL.Image, deterministic across runs and Python versions for
      the same inputs.

    Layout invariants (model can rely on these):
      - First N rows are training pairs, side-by-side input | output.
      - Last row is the test pair (input alone, or input | output if
        show_test_output=True).
      - All rows align to the maximum-width pair in the puzzle.
      - Background is dark gray (20,20,20). Grid lines GRID_LINE.
    """
    train = puzzle.get("train") or []
    test = puzzle.get("test") or []

    rows = []  # list of (image, label_str) tuples for vertical stacking

    for i, pair in enumerate(train):
        rows.append(pair_image(pair["input"], pair["output"],
                                cell_px, border,
                                f"Train {i} In", f"Train {i} Out"))

    for i, pair in enumerate(test):
        if show_test_output and pair.get("output"):
            rows.append(pair_image(pair["input"], pair["output"],
                                    cell_px, border,
                                    f"Test {i} In", f"Test {i} Out"))
        else:
            rows.append(grid_to_image(pair["input"], cell_px, border,
                                       f"Test {i} In"))

    if not rows:
        return Image.new("RGB", (100, 100), (20, 20, 20))

    total_w = max(img.width for img in rows)
    total_h = sum(img.height for img in rows) + gap * (len(rows) - 1)

    out = Image.new("RGB", (total_w, total_h), (20, 20, 20))
    y = 0
    for img in rows:
        # Center horizontally if narrower than total_w
        x = (total_w - img.width) // 2
        out.paste(img, (x, y))
        y += img.height + gap
    return out


def _pad_to_multiple(img, multiple=32, fill=(20, 20, 20)):
    """Pad image dimensions up to a multiple of `multiple`.

    Qwen3.5/Qwen3-VL image tokenization rounds dimensions to a patch
    multiple, so padding here makes the rendered artifact explicit and keeps
    interpolation out of the training path.
    """
    if multiple <= 1:
        return img
    w = ((img.width + multiple - 1) // multiple) * multiple
    h = ((img.height + multiple - 1) // multiple) * multiple
    if w == img.width and h == img.height:
        return img
    out = Image.new("RGB", (w, h), fill)
    out.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
    return out


def _grid_dims(grid):
    if isinstance(grid, np.ndarray):
        grid = grid.tolist()
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    return rows, cols


def _labeled_grid_image(grid, *, cell_px, border, label_prefix):
    rows, cols = _grid_dims(grid)
    return grid_to_image(
        grid,
        cell_size=cell_px,
        border=border,
        label=f"{label_prefix} {rows}x{cols}",
    )


def _render_puzzle_card_at_cell_size(
    puzzle,
    *,
    cell_px,
    border,
    gap,
    column_gap,
    arrow_w,
    show_test_output,
):
    """Render a two-column task card at one exact cell size.

    The input and output grids keep their true shapes. Rows share a stable
    input/arrow/output column grammar, but smaller grids are centered within
    their column instead of being stretched or padded with fake grid cells.
    """
    train = puzzle.get("train") or []
    test = puzzle.get("test") or []

    rendered_rows = []
    input_w = output_w = 0
    for i, pair in enumerate(train, start=1):
        left = _labeled_grid_image(
            pair["input"], cell_px=cell_px, border=border,
            label_prefix=f"EX {i} INPUT",
        )
        right = _labeled_grid_image(
            pair["output"], cell_px=cell_px, border=border,
            label_prefix=f"EX {i} OUTPUT",
        )
        rendered_rows.append(("train", left, right))
        input_w = max(input_w, left.width)
        output_w = max(output_w, right.width)

    for i, pair in enumerate(test, start=1):
        left = _labeled_grid_image(
            pair["input"], cell_px=cell_px, border=border,
            label_prefix=f"TEST {i} INPUT",
        )
        right = None
        if show_test_output and pair.get("output") is not None:
            right = _labeled_grid_image(
                pair["output"], cell_px=cell_px, border=border,
                label_prefix=f"TEST {i} OUTPUT",
            )
            output_w = max(output_w, right.width)
        rendered_rows.append(("test", left, right))
        input_w = max(input_w, left.width)

    if not rendered_rows:
        return Image.new("RGB", (100, 100), (20, 20, 20))

    total_w = input_w + column_gap + arrow_w + column_gap + max(1, output_w)
    row_heights = [
        max(left.height, right.height if right is not None else 0)
        for _, left, right in rendered_rows
    ]
    total_h = sum(row_heights) + gap * (len(row_heights) - 1)
    out = Image.new("RGB", (total_w, total_h), (20, 20, 20))
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
    except Exception:
        font = ImageFont.load_default()

    y = 0
    arrow_x = input_w + column_gap + (arrow_w // 2)
    output_x0 = input_w + column_gap + arrow_w + column_gap
    for kind, left, right in rendered_rows:
        row_h = max(left.height, right.height if right is not None else 0)
        left_x = (input_w - left.width) // 2
        out.paste(left, (left_x, y + (row_h - left.height) // 2))
        if right is not None:
            out.paste(right, (output_x0 + (output_w - right.width) // 2,
                              y + (row_h - right.height) // 2))
            arrow = "->"
        else:
            arrow = "?"
        color = LABEL_FG if kind == "train" else (240, 240, 240)
        draw.text((arrow_x - 8, y + row_h // 2 - 7), arrow, fill=color, font=font)
        y += row_h + gap
    return out


def render_puzzle_card(
    puzzle,
    *,
    max_pixels=786432,
    min_cell_px=7,
    max_cell_px=22,
    border=1,
    gap=10,
    column_gap=12,
    arrow_w=28,
    patch_multiple=32,
    show_test_output=False,
):
    """Render a canonical multimodal training card.

    Compared with `task_image`, this v2 renderer is stricter about the visual
    contract:

    - one global cell size per task image;
    - input/output columns are stable across examples;
    - unequal grid sizes are centered, never stretched;
    - test outputs are hidden by default;
    - final dimensions are padded to a patch multiple for Qwen-style VLMs.

    The cell size is chosen adaptively so the final card stays under
    `max_pixels` whenever possible.
    """
    chosen = None
    img = None
    for cell_px in range(max_cell_px, min_cell_px - 1, -1):
        candidate = _render_puzzle_card_at_cell_size(
            puzzle,
            cell_px=cell_px,
            border=border,
            gap=gap,
            column_gap=column_gap,
            arrow_w=arrow_w,
            show_test_output=show_test_output,
        )
        padded = _pad_to_multiple(candidate, patch_multiple)
        img = padded
        chosen = cell_px
        if padded.width * padded.height <= max_pixels:
            break
    # Store useful non-persistent metadata for callers that inspect the PIL
    # object directly. PNG writers ignore this unless they explicitly copy it.
    if img is not None:
        img.info["arc_cell_px"] = str(chosen)
        img.info["arc_renderer"] = "render_puzzle_card"
    return img


def puzzle_content_hash(puzzle) -> str:
    """Stable 12-char hash of (train+test) grids. Same puzzle → same
    hash, regardless of which dict ordering Python chose. Use for
    cache keys when rendering shards."""
    import hashlib
    import json
    canonical = {
        "train": [{"input": p["input"], "output": p.get("output")}
                  for p in (puzzle.get("train") or [])],
        "test": [{"input": p["input"], "output": p.get("output")}
                 for p in (puzzle.get("test") or [])],
    }
    blob = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def test_result_image(got_grid, expected_grid, pair_index, cell_size=16, border=1):
    """Render a test result: got | expected | diff.

    Shows three grids side by side for a train pair test result.
    """
    got_img = grid_to_image(got_grid, cell_size, border, f"Pair {pair_index} Got")
    exp_img = grid_to_image(expected_grid, cell_size, border, f"Pair {pair_index} Expected")
    diff_img = diff_image(got_grid, expected_grid, cell_size, border)

    gap = 6
    total_w = got_img.width + exp_img.width + diff_img.width + gap * 2
    total_h = max(got_img.height, exp_img.height, diff_img.height)

    combined = Image.new("RGB", (total_w, total_h), (20, 20, 20))
    combined.paste(got_img, (0, 0))
    combined.paste(exp_img, (got_img.width + gap, 0))
    combined.paste(diff_img, (got_img.width + exp_img.width + gap * 2, 0))

    return combined
