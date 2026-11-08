"""Bounded projections using the locally copied historical data serializers.

This file runs inside a prepared library runtime, never in an actor workspace.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
from pathlib import Path
import random
import sys


def render(request: dict) -> dict:
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "scripts"))
    style = request["style"]
    rows, diagnostics = [], {}
    if style == "synthpipe":
        from coder_synth_verify import ProgramVerifier
        from dsl_v2 import build_core_vocab
        from gen_synthpipe_data import synthpipe_rows

        verifier = ProgramVerifier()
        try:
            rows, executed = synthpipe_rows(build_core_vocab(0)[1], verifier,
                                            random.Random(request["seed"]), request["stages"])
        finally:
            verifier.close()
        diagnostics = {"requested_stages": request["stages"], "executed_stages": executed,
                       "truncated_stages": request["stages"] - executed}
        if executed < request["stages"]:
            diagnostics["reason"] = "Inherited chain stopped at an execution, output-validation or tokenization failure"
        for row in rows:
            row["derivation"] = {"kind": "synthetic_program_prefix", "seed": request["seed"],
                                 "reviewed_safe": False}
        return {"rows": rows, "diagnostics": diagnostics}

    episode, canonical = request["episode"], request["canonical"]
    if style == "challenges":
        return {"rows": [], "diagnostics": {}}
    if style == "native":
        from arcpuzzles_native_export import native_rows

        rows = native_rows(episode, root / "scripts/build_arc_native_dataset.py",
                           grouped=request["group_queries"])
    elif style in {"grids", "code", "episodes"}:
        from qwen9b.instance_rows import make_instance_row
        from teammate.make_data import chat_row, style_row

        # The executed authority wins over any archival presentation source.
        canonical = dict(canonical, program_solution=episode["program"])
        raw = make_instance_row(episode["task_id"], canonical, episode)
        if request["render"] == "raw":
            rows = [style_row(style, raw)]
        elif style == "grids":
            # The historical chat renderer handles one query; preserve every
            # requested query by projecting each independently.
            for query_index, pair in enumerate(raw["test"]):
                item = chat_row(request["render"], style, dict(raw, test=[pair]),
                                system_prompt=request["system_prompt"], fence=request["fence"])
                item["query_index"] = query_index
                rows.append(item)
        else:
            rows = [chat_row(request["render"], style, raw,
                             system_prompt=request["system_prompt"], fence=request["fence"])]
    else:
        from dsl_v2 import build_core_vocab, to_tokens
        import gen_dsl_stream as stream

        stream._RNG.seed(request["seed"])
        core = build_core_vocab(0)[1]
        if style == "dsl":
            weights = {mode: float(mode[1:-1] in request["modes"])
                       for mode in stream.DEFAULT_MODE_WEIGHTS}
            rows = stream.instance_rows(episode["task_id"], to_tokens(episode["program"], core),
                                        episode, core, weights=weights)
            diagnostics["requested_modes"] = request["modes"]
        elif style == "hindsight":
            from coder_synth_verify import ProgramVerifier
            from gen_hindsight_data import hindsight_rows

            verifier = ProgramVerifier()
            try:
                rows, tried, kept = hindsight_rows(episode["task_id"], episode["program"],
                                                   episode, core, verifier, request["mutations"])
            finally:
                verifier.close()
            diagnostics = {"mutation_slots": request["mutations"], "mutations_tried": tried,
                           "mutations_kept": kept, "mutations_rejected": tried - kept,
                           "unused_slots": request["mutations"] - tried,
                           "rejection_detail": "Inherited helper reports counts; it does not return per-mutation rejection reasons"}
            for row in rows:
                row["derivation"] = {"kind": "executed_program_mutation", "reviewed_safe": False}
        else:
            raise ValueError(f"Unknown export style: {style}")
    episode_id = request.get('episode_id') or hashlib.sha256(json.dumps(
        episode, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    for row in rows:
        row["episode_id"] = episode_id
        row["source_provenance"] = episode["provenance"]
    artifacts = {}
    if style == "native" and request["tensors"] != "none":
        from arcpuzzles_native_export import tensorize_rows
        import torch
        import safetensors

        artifacts = tensorize_rows(rows, root, kind=request["tensors"], canvas_size=request["canvas_size"],
                                  n_train=request["n_train"], n_test=request["n_test"],
                                  grouped=request["group_queries"])
        diagnostics["tensor_runtime"] = {"torch": torch.__version__, "safetensors": safetensors.__version__,
                                          "device": "cpu", "augmentation": "none"}
    return {"rows": rows, "diagnostics": diagnostics, "artifacts": artifacts}


if __name__ == "__main__":
    with contextlib.redirect_stdout(sys.stderr):
        root = Path(__file__).resolve().parent
        request = json.loads((root / "export_request.json").read_text())
        result = render(request)
        (root / "export_result.json").write_text(json.dumps(result, allow_nan=False) + "\n")
