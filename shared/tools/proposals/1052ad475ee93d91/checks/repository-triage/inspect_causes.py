from pathlib import Path
import hashlib,json,os,zipfile
from arcpuzzles import Catalog
from arcpuzzles.datasets import _identity
from arcpuzzles import runtime
from reviewer_support import load_selected_generator
root=Path.cwd()
report={"process_table": {"syscall_pid":os.getpid(),"proc_self_pid":int(Path("/proc/self/stat").read_text().split("(",1)[0]),"supported":runtime._process_table_supported(),"identity":runtime._process_identity(os.getpid())}, "archival":{}, "original_zip_equality":{}}
cat=Catalog(root)
for tid in ("defba1ab4f90","d982cffd80f8"):
    row,=cat.generate(tid,seed=17,difficulty="medium",n_train=1,n_test=1,allow_unapproved=True,reference="archival")
    mod,source,source_hash=load_selected_generator(tid,root=root)
    grid=mod.generate(17,0,difficulty="medium")
    report["archival"][tid]={"generator_version":mod.VERSION,"generator_sha256":source_hash,"identity":_identity({"train":row["train"],"test":row["test"]}),"sample_indices":row["sample_indices"],"rejections":row["rejections"],"sample_zero_self_check":mod.self_check(grid,difficulty="medium"),"sample_zero_dimensions":[len(grid),len(grid[0])],"executed_rule_hash":row["executed_rule_hash"]}
archive=Path("/workspace/scratch/c02d3b6ff693/upload/SEND-THIS-ARCpuzzles-review(20261020-084231-1).zip")
files=("tests/test_archival_reference.py","tests/test_check_jobs.py","tests/test_check_signals.py","src/arcpuzzles/runtime.py","src/arcpuzzles/check_jobs.py","src/arcpuzzles/worker.py","generators/defba1ab4f90/generator.py","generators/defba1ab4f90/notes.md","generators/d982cffd80f8/generator.py","generators/d982cffd80f8/notes.md")
with zipfile.ZipFile(archive) as z:
    for rel in files:
        before=z.read("WORK/repo/"+rel); after=(root/rel).read_bytes()
        report["original_zip_equality"][rel]={"identical":before==after,"sha256":hashlib.sha256(after).hexdigest()}
print(json.dumps(report,indent=2))
