from pathlib import Path
import json
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_priority import build_parametric_priority

root = Path.cwd()
catalog = Catalog(root)
row = catalog.describe("576426a573af")
result = build_parametric_priority(catalog, rows=[row])
selected = result["related_generators"][row["id"]]
assert selected["prototype"]["status"] == "current", selected
assert selected["prototype"]["verification_status"] == "reviewer_reported"
assert selected["prototype"]["variant_approved"] is False
assert selected["training_admitted"] is False
receipt = {"task_id": row["id"], "selected": selected, "scope": "Selected-row public priority API verification only; no draw policy or approval was mutated."}
out = root.parent / "checks/parametric/current-manifest-verification.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, sort_keys=True))
