#!/usr/bin/env python3
"""Racket-free DATA-OUTPUT quality report over the training pool.

WHY THIS EXISTS
---------------
Reviewers (and CI) need to look at the ACTUAL grids the model trains on and catch
SYSTEMATIC, recurring-across-many-rows output defects — not just read code. The
pool rows already carry the materialized (input, output) pairs (outputs were
derived through each puzzle's Racket rule at generation time), so inspecting and
measuring DATA OUTPUT needs no Racket binary and no GPU. This tool is pure stdlib.

It does two things:
  1. RENDER a handful of episodes readably so you can eyeball pedagogy
     (do the demos identify a unique rule? is the output a degenerate texture?).
  2. SCAN every (input, output) pair for four systematic OUTPUT-REGULARITY error
     classes, bucketed and broken down per stream, with example offenders:

       (A) degenerate / trivial output  — output == input (no-op), output is
           a single constant color, output is a 1x1 scalar-label answer (tracked
           separately because ConceptARC label tasks are legitimate concept data
           but a distribution mismatch for ARC-AGI-2 eval), or a task's outputs
           collapse to one distinct grid across all sampled instances.
       (B) background / palette irregularity — all-black (bg=0) field when eval uses
           a nonzero background ~66% of the time; palette size far from eval.
       (C) malformed / irregular structure — ragged rows (not a rectangle), values
           outside 0-9, or an empty grid. These are hard generator bugs.
       (D) size / density off the eval distribution — input area far below eval's
           median 361 / p90 900, or density far from eval's ~0.29 non-modal fill.

When ``--render-dir`` is supplied, the same deterministic sample is also
written as review-ready PNGs, a contact sheet, and a JSON manifest. Pillow is
loaded only for that optional physical-render path.

Usage (runs out of the box against the bundled sample):
  python3 scripts/data_quality_report.py
  python3 scripts/data_quality_report.py --pool 'data/pool_sample/*.jsonl' --render 6
  python3 scripts/data_quality_report.py --pool '/mnt/ai/scratch/qwen_run/pool/gen_*/*.jsonl' \
      --max-rows 4000 --json out/data_quality.json
  python3 scripts/data_quality_report.py --task-filter generic_dense_field_gen1 --render 5
"""
import argparse
import glob
import importlib
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_POOL = str(REPO / "data" / "pool_sample" / "*.jsonl")

# Eval-target reference points (from distribution_audit, modal-bg + test-inclusive):
EVAL_IN_AREA_MED = 361      # eval input-area median (full target)
EVAL_IN_AREA_P90 = 900
EVAL_DENSITY_NONMODAL = 0.29
EVAL_NONZERO_BG_FRAC = 0.66  # fraction of eval pairs whose modal bg is nonzero
COLLAPSE_MIN_OUTPUTS = 3  # avoid flagging a one-row/one-query task as collapsed
EVAL_SOLUTIONS = REPO / "data" / "raw" / "arc-agi_evaluation_solutions.json"
CANONICAL_PUZZLES = REPO / "data" / "canonical" / "puzzles.jsonl"


def _eval_output_profile(path=EVAL_SOLUTIONS):
    """Return scalar/constant-output rates for the bundled real eval target."""
    try:
        sols = json.loads(Path(path).read_text())
    except Exception:
        return {"n": 0, "scalar_frac": None, "const_frac": None}
    n = scalar = const = 0
    for outs in sols.values():
        for g in outs:
            if not g or not g[0]:
                continue
            n += 1
            if len(g) == 1 and len(g[0]) == 1:
                scalar += 1
            if len({v for row in g for v in row}) == 1:
                const += 1
    return {"n": n,
            "scalar_frac": (scalar / n if n else None),
            "const_frac": (const / n if n else None)}


EVAL_OUTPUT_PROFILE = _eval_output_profile()


def _canonical_identity_tasks(path=CANONICAL_PUZZLES):
    """Tasks whose public training data explicitly includes output == input."""
    tasks = set()
    try:
        handle = Path(path).open(encoding="utf-8")
    except OSError:
        return tasks
    with handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            task_id = row.get("task_id")
            if not task_id:
                continue
            for pair in row.get("train") or []:
                if (
                    isinstance(pair, dict)
                    and pair.get("input") == pair.get("output")
                ):
                    tasks.add(str(task_id))
                    break
    return tasks


CANONICAL_IDENTITY_TASKS = _canonical_identity_tasks()


def parse_grid(text):
    """digit-rows joined by newlines -> list[list[int]]; None if unparseable."""
    rows = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if not all(ch.isdigit() for ch in line):
            return None
        rows.append([int(ch) for ch in line])
    return rows or None




def normalize_stream_label(value):
    """Canonicalize optional row-provenance stream labels.

    Live rows have used small spelling variants (`re_arc`, `re-arc`, `generic`,
    `arc_heavy`). Reports and provenance gates should aggregate those under the
    same four stream buckets used by the trainer.
    """
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    key = raw.lower().replace("-", "_")
    aliases = {
        "per_puzzle": "per_puzzle", "qwen_sft": "per_puzzle",
        "rearc": "rearc", "re_arc": "rearc",
        "concepts": "concepts", "generic": "concepts",
        "pairbank": "pairbank", "arc_heavy": "pairbank",
        "archeavy": "pairbank", "conceptarc": "pairbank",
    }
    return aliases.get(key, key)


def classify_stream(path, task_id):
    """Best-effort stream label from task_id first, then filename.

    Task ids are the most reliable signal: RE-ARC rows are often stored in
    generic ``shard_*.jsonl`` files, and treating any filename containing
    ``shard`` as per_puzzle hides the rearc stream in this report. ConceptARC
    pair-bank ids begin with ``concept_`` while generic concept generators begin
    with ``generic_``, so do not classify all ``concept`` ids as concepts.
    """
    name = Path(path).name.lower()
    tid = (task_id or "").lower()

    # Strong task-id prefixes. Prefer these over filename fallbacks because some
    # integrators emit neutral file names such as shard_000.jsonl.
    if tid.startswith(("rearc_", "re_arc_", "re-arc_")):
        return "rearc"
    if tid.startswith("generic_"):
        return "concepts"
    if tid.startswith(("archeavy_", "arc_heavy_", "pairbank_", "concept_")):
        return "pairbank"

    # Filename fallbacks for legacy rows without task_id metadata. Keep the
    # generic shard fallback last; it is ambiguous and should only mean
    # per_puzzle when task_id could not decide.
    for key, label in (
        ("pairbank", "pairbank"), ("archeavy", "pairbank"), ("arc_heavy", "pairbank"),
        ("rearc", "rearc"), ("re_arc", "rearc"), ("re-arc", "rearc"),
        ("concepts", "concepts"), ("generic", "concepts"),
        ("qwen_sft", "per_puzzle"), ("shard", "per_puzzle"),
    ):
        if key in name:
            return label
    return "per_puzzle"


def needs_generator_version(stream: str) -> bool:
    """Streams whose rows should identify the exact generator/rule version.

    Pairbank rows are derived from fixed external corpora and often have no
    meaningful generator module version. Per-puzzle, generic concepts, and
    RE-ARC rows are generated/augmented code paths, so missing versions make a
    stale-shard audit impossible.
    """
    return normalize_stream_label(stream) in {"per_puzzle", "concepts", "rearc"}


def _present(row, *keys) -> bool:
    """True if any key is present and non-empty; accepts 0 as meaningful."""
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return True
    return False


def _module_version(mod_name: str) -> str | None:
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None
    version = getattr(mod, "VERSION", None)
    return str(version) if version not in (None, "") else None


def current_generator_version(task_id: str, stream: str | None = None) -> str | None:
    """Return the current generator VERSION when it is locally knowable.

    Generic concept rows AND per-puzzle rows both point at bundled Python modules,
    so a stale materialized row is detected by comparing its row-level
    ``generator_version`` with the module's current ``VERSION``. RE-ARC rows come
    from an external checkout, so the source hash is not knowable here; those are
    checked separately for a deterministic ``rearc:<key>:<hash>`` prefix shape.
    """
    tid = str(task_id or "")
    m = re.match(r"^generic_(.+)_gen(\d+)$", tid)
    if m:
        family, gen_n = m.groups()
        return _module_version(f"puzzle_generators.generic.concepts.{family}.gen{gen_n}")
    if normalize_stream_label(stream) == "per_puzzle" or re.match(r"^[0-9a-f]{12}$", tid):
        return _module_version(f"puzzle_generators.per_puzzle.{tid}.generator")
    return None


def expected_rearc_version_prefix(task_id: str, row: dict) -> str | None:
    """Expected prefix for RE-ARC source-hash fingerprints.

    integrate_re_arc.stable_rearc_version() writes ``rearc:<key>:<sha16>``. We
    cannot recompute the sha without the external re-arc checkout, but we can
    still reject missing/malformed/wrong-key versions.
    """
    key = row.get("source_key")
    if not key and str(task_id or "").startswith("rearc_"):
        key = str(task_id)[len("rearc_"):]
    return f"rearc:{key}:" if key else None


def modal_bg(g):
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def grid_area(g):
    return len(g) * len(g[0])


def is_scalar_grid(g):
    return bool(g) and len(g) == 1 and len(g[0]) == 1


def is_const_grid(g):
    return bool(g) and len({v for row in g for v in row}) == 1


def is_rectangular(g):
    return len(set(len(r) for r in g)) == 1


def values_ok(g):
    return all(0 <= v <= 9 for row in g for v in row)


def density_nonmodal(g):
    bg = modal_bg(g)
    n = grid_area(g)
    nz = sum(1 for row in g for v in row if v != bg)
    return nz / n if n else 0.0


def iter_pairs(row):
    """Yield (index, kind, in_text, out_text) for each user->assistant pair.

    kind is 'demo' or 'query' using demo_count when present (the first demo_count
    pairs are demos, the rest queries)."""
    ms = row.get("messages") or []
    demo_count = row.get("demo_count")
    pair_i = 0
    for k in range(0, len(ms) - 1, 2):
        if ms[k].get("role") != "user" or ms[k + 1].get("role") != "assistant":
            continue
        kind = "demo"
        if isinstance(demo_count, int):
            kind = "demo" if pair_i < demo_count else "query"
        yield pair_i, kind, ms[k]["content"], ms[k + 1]["content"]
        pair_i += 1


def render_episode(row, max_grid=14):
    """Readable digit-grid rendering of one episode (demos + queries)."""
    out = []
    tid = row.get("task_id", "?")
    out.append(f"task_id={tid}  demos={row.get('demo_count')}  queries={row.get('query_count')}")
    for i, kind, itxt, otxt in iter_pairs(row):
        ig, og = parse_grid(itxt), parse_grid(otxt)
        tag = f"  [{kind} {i}]"
        if not ig or not og:
            out.append(tag + "  <unparseable>")
            continue
        ih, iw = len(ig), len(ig[0])
        oh, ow = len(og), len(og[0])
        note = []
        if ig == og:
            note.append("OUTPUT==INPUT (no-op)")
        if is_const_grid(og):
            note.append("OUTPUT scalar-label" if is_scalar_grid(og) else "OUTPUT single-color")
        out.append(f"{tag}  in {ih}x{iw} -> out {oh}x{ow}" + ("   <<< " + ", ".join(note) if note else ""))
        if ih <= max_grid and iw <= max_grid and oh <= max_grid and ow <= max_grid:
            irows = ["".join(str(v) for v in r) for r in ig]
            orows = ["".join(str(v) for v in r) for r in og]
            for a, b in zip(irows + [""] * (len(orows) - len(irows)),
                            orows + [""] * (len(irows) - len(orows))):
                out.append(f"      {a:<{iw}}    |    {b}")
    return "\n".join(out)


def _sample_rows(paths, max_rows, seed, task_filter=None):
    """Reservoir-sample rows across all matched shards.

    The first version scanned sorted(glob) and stopped after max_rows. On a live
    pool, filenames encode stream/generator, so that recreates the same prefix
    sampling bias that previously distorted distribution_audit. Reservoir
    sampling keeps the report cheap while making inspected rows representative
    of the matched row distribution.
    """
    shards = sorted(glob.glob(paths))
    if not shards:
        print(f"no shards matched {paths!r}", file=sys.stderr)
        return None, shards, 0
    rng = random.Random(seed)
    sample = []
    seen = 0
    limit = int(max_rows)
    keep_all = limit <= 0
    for sh in shards:
        try:
            fh = open(sh)
        except OSError:
            continue
        with fh:
            for ln in fh:
                try:
                    row = json.loads(ln)
                except Exception:
                    continue
                tid = row.get("task_id", "?")
                if task_filter and task_filter not in tid:
                    continue
                seen += 1
                if keep_all or len(sample) < limit:
                    sample.append((sh, row))
                    continue
                j = rng.randrange(seen)
                if j < limit:
                    sample[j] = (sh, row)
    return sample, shards, seen


def scan(paths, max_rows, seed=0, task_filter=None):
    sampled, shards, seen_rows = _sample_rows(paths, max_rows, seed, task_filter=task_filter)
    if sampled is None:
        return None
    stats = defaultdict(lambda: {
        "rows": 0, "pairs": 0,
        "A_noop": 0, "A_canonical_noop": 0,
        "A_const_out": 0, "A_scalar_out": 0, "A_episode_collapse": 0,
        "B_black_bg_out": 0,
        "C_ragged": 0, "C_bad_vals": 0, "C_empty": 0,
        "in_area": [], "out_area": [], "dens": [], "nonzero_bg_out": 0,
        "missing_source_stream": 0, "missing_generator_version": 0,
        "missing_source_seed": 0, "missing_instance_seed": 0,
        "missing_episode_index": 0, "stale_generator_version": 0,
    })
    examples = defaultdict(list)              # class -> [(stream, task_id, detail)]
    task_outputs = defaultdict(set)           # task_id -> set of distinct output strings
    task_output_counts = defaultdict(int)     # task_id -> number of observed outputs
    task_stream = {}

    for sh, row in sampled:
        tid = row.get("task_id", "?")
        explicit_stream = normalize_stream_label(row.get("source_stream"))
        stream = explicit_stream or classify_stream(sh, tid)
        task_stream[tid] = stream
        s = stats[stream]
        s["rows"] += 1
        # Provenance: a row carrying no explicit source_stream had its stream
        # INFERRED (filename/task_id) — fine for the report, but worth surfacing
        # so we know how much of the audit ran on inferred provenance. Generated
        # streams should also carry generator_version + seed/index fields; without
        # them, a live pool can contain stale rows after a generator bugfix and the
        # row itself gives no way to tell. (Completes the 4-dim provenance gate.)
        if not explicit_stream:
            s["missing_source_stream"] += 1
        row_version = row.get("generator_version")
        if not _present(row, "generator_version") and needs_generator_version(stream):
            s["missing_generator_version"] += 1
        else:
            cur_version = current_generator_version(tid, stream)
            if cur_version is not None and str(row_version) not in ("", cur_version):
                s["stale_generator_version"] += 1
                if len(examples["P_stale_generator_version"]) < 6:
                    examples["P_stale_generator_version"].append(
                        (stream, tid, f"row generator_version={row_version!r}, current VERSION={cur_version!r}"))
            rearc_prefix = expected_rearc_version_prefix(tid, row) if stream == "rearc" else None
            if rearc_prefix and not str(row_version or "").startswith(rearc_prefix):
                s["stale_generator_version"] += 1
                if len(examples["P_stale_generator_version"]) < 6:
                    examples["P_stale_generator_version"].append(
                        (stream, tid, f"row generator_version={row_version!r}, expected prefix={rearc_prefix!r}"))
        if not _present(row, "source_seed", "seed"):
            s["missing_source_seed"] += 1
        if not _present(row, "instance_seed", "sample_seed") and stream in {"per_puzzle", "concepts"}:
            s["missing_instance_seed"] += 1
        if not _present(row, "episode_index", "sample_index"):
            s["missing_episode_index"] += 1
        episode_outputs = []
        for i, kind, itxt, otxt in iter_pairs(row):
            episode_outputs.append(otxt.strip())
            ig, og = parse_grid(itxt), parse_grid(otxt)
            s["pairs"] += 1
            # (C) malformed structure
            if og is None or not og:
                s["C_empty"] += 1
                if len(examples["C_empty"]) < 6:
                    examples["C_empty"].append((stream, tid, f"pair{i} empty/unparseable output"))
                continue
            if not is_rectangular(og):
                s["C_ragged"] += 1
                if len(examples["C_ragged"]) < 6:
                    examples["C_ragged"].append((stream, tid, f"pair{i} ragged output rows"))
            if not values_ok(og):
                s["C_bad_vals"] += 1
                if len(examples["C_bad_vals"]) < 6:
                    examples["C_bad_vals"].append((stream, tid, f"pair{i} out-of-range value"))
            if ig is None:
                continue
            # (A) degenerate / trivial output
            if ig == og:
                if (
                    stream == "per_puzzle"
                    and tid in CANONICAL_IDENTITY_TASKS
                ):
                    s["A_canonical_noop"] += 1
                else:
                    s["A_noop"] += 1
                    if len(examples["A_noop"]) < 6:
                        examples["A_noop"].append(
                            (stream, tid, f"pair{i} output==input")
                        )
            if is_const_grid(og):
                if is_scalar_grid(og):
                    s["A_scalar_out"] += 1
                    if len(examples["A_scalar_out"]) < 6:
                        examples["A_scalar_out"].append((stream, tid, f"pair{i} 1x1 scalar-label output"))
                else:
                    s["A_const_out"] += 1
                    if len(examples["A_const_out"]) < 6:
                        examples["A_const_out"].append((stream, tid, f"pair{i} single-color output area={grid_area(og)}"))
            task_outputs[tid].add(otxt.strip())
            task_output_counts[tid] += 1
            # (B) background / palette
            obg = modal_bg(og)
            if obg == 0:
                s["B_black_bg_out"] += 1
            else:
                s["nonzero_bg_out"] += 1
            # (D) size / density
            s["in_area"].append(grid_area(ig))
            s["out_area"].append(grid_area(og))
            s["dens"].append(density_nonmodal(og))
        if (len(episode_outputs) >= COLLAPSE_MIN_OUTPUTS
                and len(set(episode_outputs)) == 1):
            s["A_episode_collapse"] += 1
            if len(examples["A_episode_collapse"]) < 6:
                examples["A_episode_collapse"].append(
                    (stream, tid, "all outputs in this sampled episode are identical"))

    # (A) cross-instance output collapse: a task whose every sampled output is identical
    collapsed = [(task_stream[t], t) for t, outs in task_outputs.items()
                 if task_output_counts[t] >= COLLAPSE_MIN_OUTPUTS and len(outs) == 1]
    return {"stats": stats, "examples": examples, "collapsed": collapsed,
            "n_tasks": len(task_outputs), "collapse_min_outputs": COLLAPSE_MIN_OUTPUTS,
            "sampled_rows": sampled, "seen_rows": seen_rows, "sampled_n": len(sampled),
            "n_shards": len(shards), "seed": seed, "task_filter": task_filter}


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


def pct(xs, p):
    """Nearest-rank percentile: p90 of 10 values is item #9, not max.

    The old int(p*len(xs)) index selected the 91st item for len=100 and the
    maximum for len=10. That made small bundled/live samples look slightly more
    extreme on p90 size axes than the actual nearest-rank statistic.
    """
    xs = sorted(xs)
    if not xs:
        return 0
    idx = max(0, min(len(xs) - 1, math.ceil(p * len(xs)) - 1))
    return xs[idx]


def select_render_rows(sampled_rows, limit):
    """Pick render examples across streams instead of dumping the first file."""
    buckets = defaultdict(list)
    for sh, row in sampled_rows:
        stream = normalize_stream_label(row.get("source_stream")) or classify_stream(sh, row.get("task_id"))
        if len(buckets[stream]) < limit:
            buckets[stream].append(row)
    preferred = ["per_puzzle", "rearc", "concepts", "pairbank"]
    order = preferred + sorted(k for k in buckets if k not in preferred)
    chosen = []
    while len(chosen) < limit:
        progressed = False
        for stream in order:
            if buckets.get(stream):
                chosen.append((stream, buckets[stream].pop(0)))
                progressed = True
                if len(chosen) >= limit:
                    break
        if not progressed:
            break
    return chosen


ARC_RGB = {
    0: (0, 0, 0),
    1: (0, 116, 217),
    2: (255, 65, 54),
    3: (46, 204, 64),
    4: (255, 220, 0),
    5: (170, 170, 170),
    6: (240, 18, 190),
    7: (255, 133, 27),
    8: (127, 219, 255),
    9: (135, 12, 37),
}


def _grid_png(grid, *, cell_size=14):
    """Render one parsed ARC grid to a Pillow image."""
    from PIL import Image, ImageDraw

    height = len(grid)
    width = len(grid[0])
    image = Image.new(
        "RGB",
        (width * cell_size + 1, height * cell_size + 1),
        (255, 255, 255),
    )
    draw = ImageDraw.Draw(image)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            x0 = col * cell_size
            y0 = row * cell_size
            draw.rectangle(
                (x0, y0, x0 + cell_size, y0 + cell_size),
                fill=ARC_RGB.get(value, (255, 255, 255)),
                outline=(90, 90, 90),
            )
    return image


def _episode_png(row):
    """Render every valid input/output pair in one episode."""
    from PIL import Image, ImageDraw

    panels = []
    for pair_index, kind, input_text, output_text in iter_pairs(row):
        input_grid = parse_grid(input_text)
        output_grid = parse_grid(output_text)
        if not input_grid or not output_grid:
            continue
        largest_dim = max(
            len(input_grid),
            len(input_grid[0]),
            len(output_grid),
            len(output_grid[0]),
        )
        cell_size = max(5, min(16, 256 // max(1, largest_dim)))
        input_image = _grid_png(input_grid, cell_size=cell_size)
        output_image = _grid_png(output_grid, cell_size=cell_size)
        title_height = 20
        gap = 34
        panel = Image.new(
            "RGB",
            (
                input_image.width + gap + output_image.width,
                title_height + max(input_image.height, output_image.height),
            ),
            (248, 248, 248),
        )
        draw = ImageDraw.Draw(panel)
        draw.text((2, 3), f"{kind} {pair_index}: input -> output", fill=(20, 20, 20))
        panel.paste(input_image, (0, title_height))
        draw.text((input_image.width + 10, title_height + 4), "->", fill=(20, 20, 20))
        panel.paste(output_image, (input_image.width + gap, title_height))
        panels.append(panel)

    task_id = str(row.get("task_id") or "unknown")
    header_height = 28
    separator = 8
    if not panels:
        image = Image.new("RGB", (360, 70), (248, 248, 248))
        ImageDraw.Draw(image).text(
            (8, 8),
            f"task_id={task_id}: no parseable pairs",
            fill=(20, 20, 20),
        )
        return image
    width = max(panel.width for panel in panels) + 16
    height = header_height + sum(panel.height for panel in panels)
    height += separator * (len(panels) - 1) + 8
    image = Image.new("RGB", (width, height), (238, 238, 238))
    draw = ImageDraw.Draw(image)
    draw.text(
        (8, 7),
        f"task_id={task_id}  demos={row.get('demo_count')}  queries={row.get('query_count')}",
        fill=(10, 10, 10),
    )
    y = header_height
    for panel in panels:
        image.paste(panel, (8, y))
        y += panel.height + separator
    return image


def emit_render_artifacts(render_rows, render_dir, montage_out=None):
    """Write deterministic episode PNGs, contact sheet, and manifest."""
    from PIL import Image, ImageDraw

    render_dir = Path(render_dir)
    render_dir.mkdir(parents=True, exist_ok=True)
    records = []
    images = []
    for index, (stream, row) in enumerate(render_rows, 1):
        task_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(row.get("task_id") or "unknown"))
        filename = f"episode_{index:03d}__{task_id}.png"
        image = _episode_png(row)
        image.save(render_dir / filename, format="PNG", optimize=True)
        images.append((filename, image.copy()))
        records.append(
            {
                "index": index,
                "task_id": str(row.get("task_id") or "unknown"),
                "stream": stream,
                "file": filename,
                "pair_count": sum(1 for _ in iter_pairs(row)),
                "width": image.width,
                "height": image.height,
            }
        )

    montage_path = Path(montage_out) if montage_out else render_dir / "montage.png"
    montage_path.parent.mkdir(parents=True, exist_ok=True)
    columns = min(3, max(1, len(images)))
    tile_width = 460
    tile_height = 360
    rows = max(1, math.ceil(len(images) / columns))
    montage = Image.new(
        "RGB",
        (columns * tile_width, rows * tile_height),
        (225, 225, 225),
    )
    draw = ImageDraw.Draw(montage)
    for index, (filename, source) in enumerate(images):
        col = index % columns
        row = index // columns
        source.thumbnail((tile_width - 16, tile_height - 30))
        x = col * tile_width + 8
        y = row * tile_height + 22
        draw.text((x, row * tile_height + 5), filename, fill=(10, 10, 10))
        montage.paste(source, (x, y))
    if not images:
        draw.text((8, 8), "No rendered episodes", fill=(10, 10, 10))
    montage.save(montage_path, format="PNG", optimize=True)

    manifest = {
        "schema_version": 1,
        "episode_count": len(records),
        "render_dir": str(render_dir),
        "montage": str(montage_path),
        "episodes": records,
    }
    manifest_path = render_dir / "render_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def print_report(res):
    stats, examples = res["stats"], res["examples"]
    print("=" * 78)
    print("DATA-OUTPUT QUALITY REPORT  (racket-free; measures the materialized pool)")
    print("=" * 78)
    print(f"sampled_rows={res.get('sampled_n', '?')}/{res.get('seen_rows', '?')} "
          f"from shards={res.get('n_shards', '?')} seed={res.get('seed', '?')}"
          + (f" task_filter={res.get('task_filter')}" if res.get('task_filter') else ""))
    if res.get('task_filter') and not res.get('seen_rows'):
        print("WARNING: task_filter matched 0 rows; this audit did not inspect materialized data")
    tot = Counter()
    for stream, s in sorted(stats.items()):
        print(f"\n[{stream}]  rows={s['rows']}  pairs={s['pairs']}")
        if not s["pairs"]:
            continue
        nz = s["nonzero_bg_out"]
        eval_scalar = EVAL_OUTPUT_PROFILE.get("scalar_frac")
        eval_const = EVAL_OUTPUT_PROFILE.get("const_frac")
        ref = (f"eval scalar~{100*eval_scalar:.1f}% const~{100*eval_const:.1f}%"
               if eval_scalar is not None and eval_const is not None else "eval scalar/const n/a")
        print(f"  (A) degenerate : no-op out={s['A_noop']} ({100*s['A_noop']/s['pairs']:.1f}%)  "
              f"canonical-identity out={s.get('A_canonical_noop', 0)}  "
              f"scalar-label out={s['A_scalar_out']} ({100*s['A_scalar_out']/s['pairs']:.1f}%)  "
              f"const-color field out={s['A_const_out']} ({100*s['A_const_out']/s['pairs']:.1f}%)  "
              f"episode-collapse rows={s['A_episode_collapse']}  [{ref}]")
        print(f"  (B) bg/palette : nonzero-bg out={100*nz/s['pairs']:.0f}%  "
              f"(eval ~{100*EVAL_NONZERO_BG_FRAC:.0f}%)")
        print(f"  (C) malformed  : ragged={s['C_ragged']}  bad-vals={s['C_bad_vals']}  empty={s['C_empty']}")
        print(f"  (D) size/dens  : in-area med={med(s['in_area'])} p90={pct(s['in_area'],.9)} "
              f"(eval med {EVAL_IN_AREA_MED}/p90 {EVAL_IN_AREA_P90})  "
              f"dens={sum(s['dens'])/len(s['dens']):.2f} (eval {EVAL_DENSITY_NONMODAL:.2f})")
        print(f"  (P) provenance : missing source_stream rows={s['missing_source_stream']}  "
              f"missing generator_version rows={s['missing_generator_version']}  "
              f"missing source_seed rows={s['missing_source_seed']}  "
              f"missing instance_seed rows={s['missing_instance_seed']}  "
              f"missing episode_index rows={s['missing_episode_index']}  "
              f"stale generator_version rows={s['stale_generator_version']}")
        for k in ("A_noop", "A_scalar_out", "A_const_out", "A_episode_collapse",
                  "C_ragged", "C_bad_vals", "C_empty"):
            tot[k] += s[k]
    # cross-instance collapse
    coll = Counter(stream for stream, _ in res["collapsed"])
    print("\n--- (A) cross-instance output collapse (a task whose sampled outputs are all identical) ---")
    print(f"  collapsed tasks: {len(res['collapsed'])}/{res['n_tasks']}  "
          f"(min_outputs={res.get('collapse_min_outputs', COLLAPSE_MIN_OUTPUTS)})  "
          f"by stream: {dict(coll)}")
    for stream, t in res["collapsed"][:10]:
        print(f"    {stream}: {t}")
    print("\n--- example offenders (first few per class) ---")
    for cls in ("A_noop", "A_scalar_out", "A_const_out", "A_episode_collapse",
                "C_ragged", "C_bad_vals", "C_empty", "P_stale_generator_version"):
        if examples[cls]:
            print(f"  {cls}:")
            for stream, tid, detail in examples[cls]:
                print(f"    [{stream}] {tid}: {detail}")
    print("\n=== SYSTEMATIC-ERROR TOTALS (across sampled pool) ===")
    for k, v in tot.most_common():
        print(f"  {k}: {v}")
    print("\nA systematic error = a class that recurs across many rows/tasks/streams.")
    print("Output regularity goal: drive no-op/scalar-label/const/collapse -> target rates, nonzero-bg out up toward eval,")
    print("malformed -> 0, and in-area med toward eval's 361. Fix the GENERATOR, never batch-edit.")



def quality_error_reasons(res, *, fail_on_scalar_label_output=False,
                          fail_on_missing_provenance=False):
    """Return hard data-quality failures suitable for CI/bundle gates.

    Constant-color outputs can be legitimate ARC targets, so they remain a
    report-only warning. No-op outputs, malformed grids, and all-output episode
    collapse are almost always stale-shard or generator bugs in this pool. A
    task filter that matched zero rows is also a hard failure (typo/stale shard).

    1x1 scalar-label outputs (the contested ConceptARC label tasks) are CAPABILITY-
    gated: report-only by DEFAULT (no behavior change), and only counted as a hard
    failure when the operator opts in via `fail_on_scalar_label_output=True`.
    (Reviewer gpt55_pro_263-05 proposed failing them by default; per our contested-
    data-policy rule we harvest the capability but keep the live default unchanged.)
    """
    totals = Counter()
    for s in res["stats"].values():
        for k in ("A_noop", "A_scalar_out", "A_episode_collapse",
                  "C_ragged", "C_bad_vals", "C_empty",
                  "missing_source_stream", "missing_generator_version",
                  "missing_source_seed", "missing_instance_seed",
                  "missing_episode_index", "stale_generator_version"):
            totals[k] += int(s.get(k, 0))
    reasons = []
    if res.get("task_filter") and int(res.get("seen_rows", 0) or 0) == 0:
        reasons.append(f"task-filter {res.get('task_filter')!r} matched zero rows")
        totals["A_task_filter_empty"] = 1
    if totals["A_noop"]:
        reasons.append(f"no-op output pairs={totals['A_noop']}")
    if totals["A_scalar_out"] and fail_on_scalar_label_output:
        reasons.append(f"scalar-label output pairs={totals['A_scalar_out']}")
    if totals["A_episode_collapse"]:
        reasons.append(f"episode-collapse rows={totals['A_episode_collapse']}")
    malformed = totals["C_ragged"] + totals["C_bad_vals"] + totals["C_empty"]
    if malformed:
        reasons.append(f"malformed output pairs={malformed}")
    if fail_on_missing_provenance:
        missing = sum(totals[k] for k in ("missing_source_stream",
                                          "missing_generator_version",
                                          "missing_source_seed",
                                          "missing_instance_seed",
                                          "missing_episode_index",
                                          "stale_generator_version"))
        if missing:
            reasons.append(f"missing/stale provenance fields={missing}")
    return reasons, totals

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pool", default=DEFAULT_POOL,
                    help="JSONL glob (default: bundled data/pool_sample/*.jsonl)")
    ap.add_argument("--max-rows", type=int, default=5000)
    ap.add_argument("--render", type=int, default=3, help="render this many sample episodes")
    ap.add_argument(
        "--render-dir",
        help=(
            "write each selected episode as a PNG plus render_manifest.json; "
            "requires Pillow"
        ),
    )
    ap.add_argument(
        "--montage-out",
        help=(
            "contact-sheet PNG path (default: RENDER_DIR/montage.png; "
            "requires --render-dir)"
        ),
    )
    ap.add_argument(
        "--json",
        "--json-out",
        dest="json",
        default=None,
        help="also write the compact per-stream quality summary as JSON",
    )
    ap.add_argument("--seed", type=int, default=0,
                    help="seed for reservoir sampling and rendered examples")
    ap.add_argument("--task-filter", default=None,
                    help="only scan rows whose task_id contains this substring")
    ap.add_argument("--fail-on-quality-error", action="store_true",
                    help="exit nonzero if the sampled pool has no-op outputs, malformed outputs, "
                         "or all-output episode collapse. Useful for CI/bundle gates after "
                         "generator bugfixes; constant-color outputs remain report-only.")
    ap.add_argument("--allow-empty-filter", action="store_true",
                    help="allow --task-filter audits that match zero rows. By default, a targeted "
                         "audit with zero sampled rows exits 4 so typo/stale-shard checks fail closed.")
    ap.add_argument("--fail-on-scalar-label-output", action="store_true",
                    help="with --fail-on-quality-error, ALSO treat 1x1 scalar-label outputs as a hard "
                         "failure (contested ConceptARC label-task policy; OFF by default = report-only).")
    ap.add_argument("--fail-on-missing-provenance", action="store_true",
                    help="with --fail-on-quality-error, ALSO fail if generated rows lack source_stream, "
                         "generator_version, source_seed, instance_seed/sample_seed, or episode_index/sample_index "
                         "where applicable, and fail generic concept rows whose generator_version is older than "
                         "the current module VERSION. OFF by default for legacy bundled samples.")
    a = ap.parse_args()
    if a.montage_out and not a.render_dir:
        ap.error("--montage-out requires --render-dir")
    if a.render_dir and a.render <= 0:
        ap.error("--render-dir requires --render greater than zero")

    res = scan(a.pool, a.max_rows, seed=a.seed, task_filter=a.task_filter)
    if res is None:
        return 2
    print_report(res)

    # A targeted --task-filter audit that sampled zero rows almost always means a
    # typo or a stale/empty shard set; fail closed so it can't read as "clean".
    # (Reviewer oai_2_65 — supersedes the earlier gpt55_2_60 early-return: prints
    # the report first, has an explicit opt-out, and uses a distinct exit code.)
    empty_targeted_audit = bool(a.task_filter) and int(res.get("seen_rows", 0)) == 0

    render_rows = []
    if a.render:
        render_rows = select_render_rows(res.get("sampled_rows", []), a.render)
        print("\n" + "=" * 78)
        print(
            "RENDERED EPISODES "
            f"(stratified {len(render_rows)}; requested {a.render}) — eyeball the pedagogy"
        )
        print("=" * 78)
        for stream, row in render_rows:
            print(f"\n--- stream={stream} ---")
            print(render_episode(row))
    if a.render_dir:
        manifest = emit_render_artifacts(
            render_rows,
            a.render_dir,
            montage_out=a.montage_out,
        )
        print(
            f"\nwrote {manifest['episode_count']} episode PNG(s), montage, "
            f"and manifest under {a.render_dir}"
        )

    if a.json:
        out = {st: {k: (v if not isinstance(v, list) else
                        {"n": len(v), "med": med(v), "p90": pct(v, .9)})
                    for k, v in s.items()}
               for st, s in res["stats"].items()}
        out["_collapsed_tasks"] = len(res["collapsed"])
        out["_collapse_min_outputs"] = res.get("collapse_min_outputs", COLLAPSE_MIN_OUTPUTS)
        out["_sample"] = {"sampled_rows": res.get("sampled_n"),
                          "seen_rows": res.get("seen_rows"),
                          "n_shards": res.get("n_shards"),
                          "seed": res.get("seed"),
                          "task_filter": res.get("task_filter")}
        reasons, totals = quality_error_reasons(res, fail_on_scalar_label_output=a.fail_on_scalar_label_output,
                                          fail_on_missing_provenance=a.fail_on_missing_provenance)
        out["_quality_error_reasons"] = reasons
        out["_quality_error_totals"] = dict(totals)
        out["_examples"] = {k: v[:10] for k, v in res["examples"].items()}
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(out, indent=2))
        print(f"\nwrote {a.json}")
    if empty_targeted_audit and not a.allow_empty_filter:
        msg = (f"empty targeted audit: --task-filter {a.task_filter!r} matched 0 rows "
               "in the selected pool; pass --allow-empty-filter only when intentional")
        print("\nQUALITY GATE: FAIL — " + msg, file=sys.stderr)
        return 4
    if a.fail_on_quality_error:
        reasons, _ = quality_error_reasons(res, fail_on_scalar_label_output=a.fail_on_scalar_label_output,
                                          fail_on_missing_provenance=a.fail_on_missing_provenance)
        if reasons:
            print("\nQUALITY GATE: FAIL — " + "; ".join(reasons), file=sys.stderr)
            return 3
        print("\nQUALITY GATE: PASS", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
