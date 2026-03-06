#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p docs/graphs

python3 - <<'PY'
from pathlib import Path
import re, subprocess

md = Path('docs/DESIGN_GRAPH.md').read_text()
blocks = re.findall(r"```mermaid\n(.*?)\n```", md, flags=re.S)
names = ['architecture', 'compatibility', 'sequence', 'entities']

for i, code in enumerate(blocks):
    name = names[i] if i < len(names) else f'graph-{i+1}'
    mmd = Path(f'docs/graphs/{name}.mmd')
    svg = Path(f'docs/graphs/{name}.svg')
    mmd.write_text(code.strip() + "\n")
    subprocess.run([
        'npx', '-y', '@mermaid-js/mermaid-cli',
        '-p', 'scripts/puppeteer-config.json',
        '-i', str(mmd),
        '-o', str(svg)
    ], check=True)

print(f"Rendered {len(blocks)} graph(s) to docs/graphs/")
PY
