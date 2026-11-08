from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repo"
HOME = ROOT / "generators" / "0be8ff9b4144" / "workspace" / "parametric"
OUT = Path(__file__).resolve().parent / "public"

spec = importlib.util.spec_from_file_location("public_export_prototype", HOME / "prototype.py")
if spec is None or spec.loader is None:
    raise ImportError("prototype")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("*.json"):
    old.unlink()
rows = []
for index, policy in enumerate(module.POLICIES):
    episode = module.generate_episode(1701 + index, intersection_policy=policy, demos=3, queries=4)
    raw = module.public_challenge_bytes(episode)
    digest = module.public_challenge_id(episode)
    path = OUT / f"challenge-{digest}.json"
    path.write_bytes(raw)
    rows.append({"policy": policy, "path": str(path), "sha256": digest, "bytes": len(raw)})
print(json.dumps({"status": "written", "files": rows}, indent=2, sort_keys=True))
