#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
TASK = ROOT / "generators/23a0c42b8a1c"
MANIFEST = TASK / "workspace/parametric/evidence/manifest.json"
PINNED_GENERATOR = "4b188d05f3c1b39b65cc288a07b39bef527b623df6a759f6facde2cda9cab75b"
PINNED_MANIFEST = "61ef18854f8b94daa2a59ffc925b4de5f2fb1cf34e6382556b1f296175c59752"
FORBIDDEN_PUBLIC_KEYS = {"parameters", "seed", "racket_source", "racket_path", "answers", "output_colour"}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def forbidden_keys(value):
    found=[]
    def walk(x, where="$"):
        if isinstance(x, dict):
            for k,v in x.items():
                if k in FORBIDDEN_PUBLIC_KEYS: found.append(f"{where}.{k}")
                walk(v, f"{where}.{k}")
        elif isinstance(x, list):
            for i,v in enumerate(x): walk(v, f"{where}[{i}]")
    walk(value)
    return found

started=time.perf_counter()
manifest=json.loads(MANIFEST.read_text())
file_checks=[]
for item in manifest.get("files", []):
    path=ROOT/item["path"]
    file_checks.append({"path":item["path"],"exists":path.is_file(),
                        "sha256_expected":item["sha256"],
                        "sha256_actual":sha(path) if path.is_file() else None,
                        "matches":path.is_file() and sha(path)==item["sha256"]})
base=TASK/"workspace/parametric/evidence/episodes"
public_paths=sorted((base/"public").glob("episode-*.json"))
private_paths=sorted((base/"private").glob("episode-*.json"))
episodes=[]
settings=[]
for pub_path, priv_path in zip(public_paths, private_paths, strict=True):
    pub=json.loads(pub_path.read_text()); priv=json.loads(priv_path.read_text())
    setting=(priv.get("parameters") or {}).get("output_colour")
    settings.append(setting)
    public_matches_private=(
        pub.get("train") == [{"input":p["input"],"output":p["output"]} for p in priv.get("train",[])]
        and pub.get("test") == [{"input":p["input"]} for p in priv.get("test",[])]
    )
    episodes.append({
        "public":str(pub_path.relative_to(ROOT)), "private":str(priv_path.relative_to(ROOT)),
        "setting":setting, "demo_count":len(pub.get("train",[])),
        "query_count":len(pub.get("test",[])),
        "public_top_level_keys":sorted(pub),
        "query_outputs_exposed":any("output" in q for q in pub.get("test",[])),
        "forbidden_public_key_paths":forbidden_keys(pub),
        "public_matches_private_allowlist":public_matches_private,
    })
report={
    "schema":"parameter-query-ticket-probe-v1", "ticket_id":"ticket-8d220547d8048f66",
    "task_id":"23a0c42b8a1c", "probe_scope":"pinned hashes, retained setting/count/privacy boundary",
    "pinned_identity":{
        "generator_sha256_expected":PINNED_GENERATOR,
        "generator_sha256_actual":sha(TASK/"generator.py"),
        "manifest_sha256_expected":PINNED_MANIFEST,
        "manifest_sha256_actual":sha(MANIFEST),
    },
    "manifest_status":{
        "verification_status":manifest.get("verification_status"),
        "production_parametric_api":manifest.get("production_parametric_api"),
        "variant_approved":manifest.get("variant_approved"),
        "all_manifest_files_present_and_hash_matched":all(x["matches"] for x in file_checks),
        "manifest_file_count":len(file_checks),
    },
    "episodes":episodes, "settings_observed":sorted(set(settings)),
    "support_boundary":{
        "all_public_views_private_allowlists":all(e["public_matches_private_allowlist"] for e in episodes),
        "any_query_answer_exposed":any(e["query_outputs_exposed"] for e in episodes),
        "any_forbidden_public_metadata":any(e["forbidden_public_key_paths"] for e in episodes),
        "demo_counts":sorted({e["demo_count"] for e in episodes}),
        "query_counts":sorted({e["query_count"] for e in episodes}),
        "four_query_supported_by_retained_evidence":all(e["query_count"]==4 for e in episodes),
    },
    "conclusion":"Pinned evidence is source-current and privacy-clean for both settings, but retained episodes support exactly one query, not four; production API and variant approval remain false.",
    "elapsed_seconds":round(time.perf_counter()-started,6),
}
assert report["pinned_identity"]["generator_sha256_actual"]==PINNED_GENERATOR
assert report["pinned_identity"]["manifest_sha256_actual"]==PINNED_MANIFEST
assert report["manifest_status"]["all_manifest_files_present_and_hash_matched"]
assert report["settings_observed"]==[2,8]
assert report["support_boundary"]["all_public_views_private_allowlists"]
assert not report["support_boundary"]["any_query_answer_exposed"]
assert not report["support_boundary"]["any_forbidden_public_metadata"]
OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":"completed","query_counts":report["support_boundary"]["query_counts"],
                  "settings":report["settings_observed"],"privacy_clean":True,
                  "variant_approved":manifest.get("variant_approved")},sort_keys=True))
