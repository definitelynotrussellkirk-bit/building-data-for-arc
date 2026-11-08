from pathlib import Path
import ast

ROOT = Path(__file__).parent
SCRIPTS = [
    ROOT / 'invoke_arc_packet_builder.py',
    ROOT / 'finalize_arc_review.py',
    ROOT / 'select_arc_ready_delivery.py',
]
for path in SCRIPTS:
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
print(f'parsed {len(SCRIPTS)} release scripts')
