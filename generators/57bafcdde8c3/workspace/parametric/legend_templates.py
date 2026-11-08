#!/usr/bin/env python3
"""Proposed edb79dae-inspired template/legend family; no production admission.

The executable parameter is mapping_policy=once|terminal. Both policies fit the
two public demonstrations; the hidden public answer is unknown. New lessons
deliberately contain chains and disconnected templates to teach the distinction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import sys

from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
POLICIES = ("once", "terminal")
RIVALS = (*POLICIES, "two_hops", "three_hops", "no_recolor", "full_blocks",
          "first_template", "destination_template", "largest_component")
SOURCE_ID = "edb79dae"
SOURCE_CHALLENGE_SHA256 = "c9190b5e5bdd993afe9b9048180eebf462a222b6597f33d4d8da0ac950544a85"
SOURCE_FILE = "shared/data/raw/arc-agi_evaluation_challenges.json"
OFFSETS = ((1, 0), (-1, 0), (0, 1), (0, -1))
ARROW_SOURCE_CELLS = {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")


def groups(cells):
    unseen = set(cells)
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        found, queue = {start}, [start]
        while queue:
            r, c = queue.pop()
            for dr, dc in OFFSETS:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    found.add(point)
                    queue.append(point)
        result.append(found)
    return sorted(result, key=lambda points: (-len(points), sorted(points)))


def bounds(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def parse_grid(grid):
    """Admit an explicit input grammar; never use seed/settings to parse roles."""
    validate_grid(grid)
    h, w = len(grid), len(grid[0])
    counts = Counter(v for row in grid for v in row)
    ordered = counts.most_common()
    if len(ordered) < 4 or ordered[0][1] == ordered[1][1]:
        raise ValueError("need unique modal background and role colors")
    bg = ordered[0][0]
    objects = []
    for color in sorted(set(counts) - {bg}):
        objects.extend((color, part) for part in groups({(r, c) for r in range(h)
                       for c in range(w) if grid[r][c] == color}))
    frames = []
    for color, points in objects:
        r0, c0, r1, c1 = bounds(points)
        fh, fw = r1 - r0 + 1, c1 - c0 + 1
        if (fh >= 5 and fw >= 5 and len(points) == 2 * (fh + fw) - 4
                and all(r in (r0, r1) or c in (c0, c1) for r, c in points)):
            frames.append((color, (r0, c0, r1, c1)))
    if len(frames) != 1:
        raise ValueError("need exactly one hollow rectangular frame")
    frame_color, frame = frames[0]
    r0, c0, r1, c1 = frame

    def inside(r, c):
        return r0 <= r <= r1 and c0 <= c <= c1

    arrows, arrow_cells, mapping = [], set(), {}
    for r in range(h - 2):
        for c in range(w - 3):
            source, target = grid[r][c], grid[r][c + 2]
            if source == target or {source, target} & {bg, frame_color}:
                continue
            points = {(r + dr, c + dc) for dr in range(3) for dc in range(4)}
            if any(inside(*p) for p in points):
                continue
            if any(grid[r + dr][c + dc] != (source if (dr, dc) in ARROW_SOURCE_CELLS else target)
                   for dr in range(3) for dc in range(4)):
                continue
            if points & arrow_cells or source in mapping:
                raise ValueError("overlapping or duplicate-source legend tiles")
            arrows.append((r, c, source, target))
            arrow_cells.update(points)
            mapping[source] = target
    if not 2 <= len(mapping) <= 5:
        raise ValueError("need two to five unambiguous directed legend tiles")
    for start in mapping:
        seen, node = set(), start
        while node in mapping:
            if node in seen:
                raise ValueError("legend cycle is outside the shared once/terminal grammar")
            seen.add(node)
            node = mapping[node]

    raw_templates = {}
    for r in range(h):
        for c in range(w):
            if not inside(r, c) and (r, c) not in arrow_cells and grid[r][c] != bg:
                raw_templates.setdefault(grid[r][c], set()).add((r, c))
    if set(raw_templates) != set(mapping):
        raise ValueError("one complete exterior template is required for every legend source")
    blocks = []
    for color, points in objects:
        if not all(r0 < r < r1 and c0 < c < c1 for r, c in points):
            continue
        br0, bc0, br1, bc1 = bounds(points)
        n = br1 - br0 + 1
        if color not in mapping or n != bc1 - bc0 + 1 or len(points) != n * n:
            raise ValueError("frame content must be solid source-colored square blocks")
        blocks.append({"color": color, "bbox": (br0, bc0, br1, bc1), "size": n})
    if not blocks or len({block["size"] for block in blocks}) != 1:
        raise ValueError("occupied blocks must have one common square size")
    n = blocks[0]["size"]
    if not 3 <= n <= 5 or set(block["color"] for block in blocks) != set(mapping):
        raise ValueError("square size must be3..5 and every source must occur inside frame")
    templates = {}
    for color, points in raw_templates.items():
        tr0, tc0, tr1, tc1 = bounds(points)
        if tr1 - tr0 + 1 != n or tc1 - tc0 + 1 != n or len(points) >= n * n:
            raise ValueError("each template must span one non-solid square bounding box")
        templates[color] = {(r - tr0, c - tc0) for r, c in points}
    if any(grid[r][c] == frame_color for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
        raise ValueError("frame color cannot occur in its interior")
    return {"background": bg, "frame_color": frame_color, "frame": frame,
            "arrows": arrows, "mapping": mapping, "templates": templates,
            "blocks": sorted(blocks, key=lambda b: b["bbox"]), "tile_size": n}


def predict(grid, policy="once"):
    """Python mirror and declared finite rivals; retained labels come from Racket."""
    if type(policy) is not str or policy not in RIVALS:
        raise ValueError("unknown mapping policy or rival")
    p = parse_grid(grid)
    r0, c0, r1, c1 = p["frame"]
    out = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    for block in p["blocks"]:
        source = block["color"]
        color = source
        hops = {"terminal": 9, "two_hops": 2, "three_hops": 3, "no_recolor": 0}.get(policy, 1)
        for _ in range(hops):
            color = p["mapping"].get(color, color)
        template_color = source
        if policy == "first_template":
            template_color = min(p["templates"])
        elif policy == "destination_template" and color in p["templates"]:
            template_color = color
        mask = p["templates"][template_color]
        if policy == "largest_component":
            mask = groups(mask)[0]
        if policy == "full_blocks":
            mask = {(r, c) for r in range(block["size"]) for c in range(block["size"])}
        br, bc, _, _ = block["bbox"]
        for dr in range(block["size"]):
            for dc in range(block["size"]):
                out[br - r0 + dr][bc - c0 + dc] = color if (dr, dc) in mask else p["background"]
    return out


def fit_rivals(demos):
    """Only demonstrations determine survival; no query inputs or answers here."""
    if type(demos) is not list or not demos:
        raise ValueError("need nonempty demonstrations")
    return [name for name in RIVALS if all(predict(pair["input"], name) == pair["output"] for pair in demos)]


def sample_input(seed, index):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 1000000, "index")
    rng = random.Random(int(digest(f"legend-template-v1:{seed}:{index}".encode()), 16))
    n = 3 + index % 3
    k = 4 if index == 0 else 2 + index % 3
    palette = rng.sample(range(10), k + 3)
    bg, frame_color = palette[:2]
    sources, terminal = palette[2:-1], palette[-1]
    mapping = dict(zip(sources, sources[1:] + [terminal]))
    fh = fw = 3 * (n + 1) + 3
    left = bool(index % 2)
    if left:
        fr, fc = 8, 0
        template_slots = [(i * (n + 1), fw + 2) for i in range(k)]
        arrow_slots = [(4 * (i // 2), 5 * (i % 2)) for i in range(k)]
        height, width = max(fr + fh, k * (n + 1) - 1), fw + n + 2
    else:
        fr, fc = n + 2, 6
        template_slots = [(0, 6 + i * (n + 1)) for i in range(k)]
        arrow_slots = [(4 * i, 0) for i in range(k)]
        height, width = max(fr + fh, 4 * k - 1), max(fc + fw, 6 + k * (n + 1) - 1)
    shift_r, shift_c = rng.randrange(2), rng.randrange(2)
    height, width = height + shift_r, width + shift_c
    if height > 30 or width > 30:
        raise AssertionError("internal layout exceeded ARC size limit")
    grid = [[bg] * width for _ in range(height)]

    def put(r, c, color):
        grid[r + shift_r][c + shift_c] = color

    for r in range(fh):
        for c in range(fw):
            if r in (0, fh - 1) or c in (0, fw - 1):
                put(fr + r, fc + c, frame_color)
    order = list(sources)
    rng.shuffle(order)
    for color, (r, c) in zip(order, arrow_slots):
        for dr in range(3):
            for dc in range(4):
                put(r + dr, c + dc, color if (dr, dc) in ARROW_SOURCE_CELLS else mapping[color])
    masks, used = {}, set()
    for i, color in enumerate(sources):
        for attempt in range(64):
            if i == 0:
                # Full bbox, one detached piece: test the grouping rule directly.
                mask = {(r, 0) for r in range(n)} | {(0, n - 1)}
            else:
                mask = {(r, c) for r in range(n) for c in range(n) if rng.random() < 0.55}
                mask |= {(0, rng.randrange(n)), (n - 1, rng.randrange(n)),
                         (rng.randrange(n), 0), (rng.randrange(n), n - 1)}
            key = tuple(sorted(mask))
            if len(mask) < n * n and key not in used:
                used.add(key)
                masks[color] = mask
                break
        else:
            raise ValueError("template sampling budget exhausted")
    order = list(sources)
    rng.shuffle(order)
    for color, (r, c) in zip(order, template_slots):
        for dr, dc in masks[color]:
            put(r + dr, c + dc, color)
    slots = [(r, c) for r in range(3) for c in range(3)]
    rng.shuffle(slots)
    labels = list(sources) + [rng.choice(sources) for _ in range(rng.randint(k + 1, 8) - k)]
    rng.shuffle(labels)
    for (sr, sc), color in zip(slots, labels):
        for dr in range(n):
            for dc in range(n):
                put(fr + 2 + sr * (n + 1) + dr, fc + 2 + sc * (n + 1) + dc, color)
    parse_grid(grid)
    return grid


def program(policy):
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("mapping_policy must be once or terminal")
    text = (HERE / "legend_templates.rkt").read_text()
    if text.count("@HOPS@") != 1:
        raise ValueError("unexpected Racket parameter template")
    return text.replace("@HOPS@", "1" if policy == "once" else "9")


def apply_program(bridge, code, grid):
    from puzzle_generators.rule_wrap import wrap_rule
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    result = bridge.eval_text(f"({wrap_rule(code)} {literal})")
    validate_grid(result)
    return result


def source_hashes():
    return {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in
            (Path(__file__), HERE / "legend_templates.rkt")}


def certify(episode):
    """Recompute a finite-rival certificate; refuse altered labels or input reuse."""
    if not isinstance(episode, dict) or not isinstance(episode.get("settings"), dict):
        raise ValueError("episode settings are required")
    if set(episode["settings"]) != {"mapping_policy"}:
        raise ValueError("episode must name only mapping_policy")
    policy = episode["settings"]["mapping_policy"]
    if policy not in POLICIES or type(policy) is not str:
        raise ValueError("invalid policy")
    demos, queries = episode.get("train"), episode.get("test")
    if type(demos) is not list or type(queries) is not list or not demos or not queries:
        raise ValueError("nonempty demo/query lists required")
    integer(episode.get("demo_count"), 1, 8, "demo_count")
    integer(episode.get("query_count"), 1, 8, "query_count")
    integer(episode.get("seed"), 0, 2**63 - 1, "seed")
    if episode["demo_count"] != len(demos) or episode["query_count"] != len(queries):
        raise ValueError("count metadata differs from the supplied pairs")
    code = program(policy)
    if (episode.get("program_solution") != code or
            episode.get("program_sha256") != digest(code.encode())):
        raise ValueError("program identity disagrees with the episode setting")
    keys = [digest(canonical(pair["input"])) for pair in demos + queries]
    if len(keys) != len(set(keys)):
        raise ValueError("all demonstration and query inputs must be distinct")
    for pair in demos + queries:
        validate_grid(pair["output"])
        if predict(pair["input"], policy) != pair["output"]:
            raise ValueError("episode label disagrees with declared rule")
    survivors = fit_rivals(demos)
    if policy not in survivors:
        raise ValueError("chosen rule does not fit demonstrations")
    per_query = []
    for i, pair in enumerate(queries):
        disagree = [rival for rival in survivors if predict(pair["input"], rival) != pair["output"]]
        if disagree:
            raise ValueError(f"query {i} is ambiguous under surviving rivals: {disagree}")
        per_query.append({"input_sha256": digest(canonical(pair["input"])),
                          "all_demo_survivors_agree": True})
    return {"fit_uses": "demonstrations_only", "rivals": list(RIVALS),
            "survivors": survivors, "queries": per_query,
            "limit": "finite declared rivals; not universal rule identifiability"}


def generate_episode(seed, policy, demos=2, queries=4, *, bridge, max_attempts=32):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 1, 8, "demos")
    integer(queries, 1, 8, "queries")
    integer(max_attempts, 1, 256, "max_attempts")
    code = program(policy)
    pairs, seen, index = [], set(), 0
    for _ in range(demos + queries):
        for _attempt in range(max_attempts):
            grid = sample_input(seed, index)
            index += 1
            key = digest(canonical(grid))
            if key not in seen:
                seen.add(key)
                break
        else:
            raise ValueError("distinct-input sampling budget exhausted")
        label = apply_program(bridge, code, grid)
        if label != predict(grid, policy):
            raise ValueError("Racket/Python mismatch")
        pairs.append({"input": grid, "output": label})
    episode = {"schema": "edb79dae-inspired-episode-v1", "status": "proposed",
               "settings": {"mapping_policy": policy}, "seed": seed,
               "train": pairs[:demos], "test": pairs[demos:],
               "demo_count": demos, "query_count": queries,
               "program_solution": code, "program_sha256": digest(code.encode()),
               "source_sha256": source_hashes(), "racket_runtime": bridge.runtime_identity,
               "public_parent": {"task_id": SOURCE_ID, "split": "evaluation",
                                 "challenge_sha256": SOURCE_CHALLENGE_SHA256,
                                 "relationship": "inspired_extension", "training_admitted": False}}
    episode["certificate"] = certify(episode)
    return episode


def source_probe(bridge):
    source = json.loads((ROOT / SOURCE_FILE).read_text())[SOURCE_ID]
    if digest(canonical(source)) != SOURCE_CHALLENGE_SHA256:
        raise ValueError("public source challenge drift")
    result = {"source_task_id": SOURCE_ID, "challenge_sha256": SOURCE_CHALLENGE_SHA256,
              "source_file_sha256": digest((ROOT / SOURCE_FILE).read_bytes()),
              "hidden_query_answer_accessed": False,
              "claim": "demonstration parity and a visible-query disagreement; no hidden-answer accuracy claim",
              "demo_results": [], "query_predictions": {}}
    for policy in POLICIES:
        code = program(policy)
        for i, pair in enumerate(source["train"]):
            observed = apply_program(bridge, code, pair["input"])
            if observed != pair["output"] or observed != predict(pair["input"], policy):
                raise ValueError(f"source demonstration {i} does not match {policy}")
            result["demo_results"].append({"policy": policy, "index": i, "matches": True})
        query = source["test"][0]["input"]
        result["query_predictions"][policy] = apply_program(bridge, code, query)
        if result["query_predictions"][policy] != predict(query, policy):
            raise ValueError("query parser/Racket mismatch")
    a, b = (result["query_predictions"][policy] for policy in POLICIES)
    result["differing_query_cells"] = sum(x != y for ar, br in zip(a, b) for x, y in zip(ar, br))
    result["public_demo_survivors"] = fit_rivals(source["train"])
    parsed = parse_grid(query)
    result["disconnected_template"] = {"color": 8, "total_cells": len(parsed["templates"][8]),
                                       "component_sizes": [len(p) for p in groups(parsed["templates"][8])]}
    return result


def export_batch(episodes, destination, *, source_evidence=None):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("output directory already exists")
    rows = []
    for episode in episodes:
        if canonical(certify(episode)) != canonical(episode.get("certificate")):
            raise ValueError("certificate missing or stale")
        raw = public_challenge_bytes(episode)
        rows.append((digest(raw), raw, episode))
    ids = [row[0] for row in rows]
    if not rows or len(ids) != len(set(ids)):
        raise ValueError("batch must contain distinct visible payloads")
    rows.sort(key=lambda row: row[0])
    (destination / "public").mkdir(parents=True)
    hashes, private = {}, []
    for public_id, raw, episode in rows:
        relative = f"public/{public_id}.json"
        (destination / relative).write_bytes(raw)
        hashes[relative] = digest(raw)
        private.append(dict(episode, public_id=public_id))
    private_raw = b"".join(canonical(row) + b"\n" for row in private)
    (destination / "private.jsonl").write_bytes(private_raw)
    hashes["private.jsonl"] = digest(private_raw)
    if source_evidence is not None:
        raw = canonical(source_evidence) + b"\n"
        (destination / "source_probe.json").write_bytes(raw)
        hashes["source_probe.json"] = digest(raw)
    manifest = {"schema": "edb79dae-inspired-export-v1", "status": "proposed",
                "episode_count": len(rows), "public_ids": ids if ids == sorted(ids) else sorted(ids),
                "files_sha256": hashes, "source_sha256": source_hashes(),
                "warning": "Give models only public/. Private records include answers and settings."}
    (destination / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    return manifest


def verify_export(destination, *, bridge):
    destination = Path(destination)
    manifest = json.loads((destination / "manifest.json").read_text())
    if (not isinstance(manifest, dict) or manifest.get("schema") != "edb79dae-inspired-export-v1"
            or manifest.get("status") != "proposed"):
        raise ValueError("unknown export manifest")
    if type(manifest.get("episode_count")) is not int or manifest["episode_count"] < 1:
        raise ValueError("export must contain a nonempty episode collection")
    public_ids = manifest.get("public_ids")
    if (type(public_ids) is not list or not public_ids or
            any(type(value) is not str or len(value) != 64 or
                any(char not in "0123456789abcdef" for char in value) for value in public_ids)
            or public_ids != sorted(set(public_ids)) or len(public_ids) != manifest["episode_count"]):
        raise ValueError("invalid public identity inventory")
    expected_files = {"private.jsonl"} | {f"public/{value}.json" for value in public_ids}
    if (destination / "source_probe.json").exists():
        expected_files.add("source_probe.json")
    hashes = manifest.get("files_sha256")
    if not isinstance(hashes, dict) or set(hashes) != expected_files:
        raise ValueError("manifest must hash the exact private/public file inventory")
    if manifest.get("source_sha256") != source_hashes():
        raise ValueError("prototype source drift")
    for relative, expected in manifest["files_sha256"].items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or (destination / path).is_symlink():
            raise ValueError("unsafe export path")
        if digest((destination / path).read_bytes()) != expected:
            raise ValueError("export content hash mismatch")
    episodes = [json.loads(line) for line in (destination / "private.jsonl").read_text().splitlines()]
    if not episodes:
        raise ValueError("export has no episodes")
    ids, labels = [], 0
    for episode in episodes:
        policy = episode["settings"]["mapping_policy"]
        code = program(policy)
        if (episode["program_solution"] != code or episode["program_sha256"] != digest(code.encode())
                or episode["source_sha256"] != source_hashes()):
            raise ValueError("episode source/program drift")
        if (episode["demo_count"] != len(episode["train"]) or episode["query_count"] != len(episode["test"])
                or canonical(certify(episode)) != canonical(episode["certificate"])):
            raise ValueError("counts or lesson certificate changed")
        public_id = public_challenge_id(episode)
        ids.append(public_id)
        if (episode["public_id"] != public_id or
                (destination / "public" / f"{public_id}.json").read_bytes() != public_challenge_bytes(episode)):
            raise ValueError("public projection or identity mismatch")
        for pair in episode["train"] + episode["test"]:
            if apply_program(bridge, code, pair["input"]) != pair["output"]:
                raise ValueError("Racket label replay failed")
            labels += 1
    if (ids != sorted(set(ids)) or ids != manifest["public_ids"] or len(episodes) != manifest["episode_count"]
            or {p.name for p in (destination / "public").iterdir()} != {f"{i}.json" for i in ids}):
        raise ValueError("batch identity/count mismatch")
    return {"status": "pass", "episodes": len(episodes), "racket_labels_replayed": labels,
            "query_count": sum(len(e["test"]) for e in episodes),
            "scope": "exact current source, bytes, labels, finite-rival certificates and public projection"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "verify"])
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args(argv)
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=20.0) as bridge:
        if options.command == "verify":
            result = verify_export(options.out, bridge=bridge)
        else:
            seeds = options.seed or [17, 29]
            episodes = [generate_episode(seed, policy, options.demos, options.queries, bridge=bridge)
                        for seed in seeds for policy in POLICIES]
            source_evidence = source_probe(bridge)
            export_batch(episodes, options.out, source_evidence=source_evidence)
            result = verify_export(options.out, bridge=bridge)
            result["source_demo_matches"] = len(source_evidence["demo_results"])
            result["source_query_policy_disagreement_cells"] = source_evidence["differing_query_cells"]
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
