"""Create a personal preset without overwriting existing card metadata."""
import argparse
import json
from pathlib import Path

def prepare(project, title, layout='full'):
    root = Path(project).resolve()
    preset = json.loads((Path(__file__).resolve().parents[1] / 'assets/ruoyu-classic.json').read_text())
    root.mkdir(parents=True, exist_ok=True)
    config = {'title': title, 'subtitle': '', 'technique': '', 'tagline': '',
              'collection': '个人全息典藏', 'edition': '001 / 001',
              'description': '', 'preset': preset['preset'],
              'parameters': preset['parameters'], 'visual': preset['visual'],
              'safeArea': preset['layouts'][layout]}
    with (root / 'card-config.json').open('x') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    (root / 'assets').mkdir(exist_ok=True)
    return config

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--project', required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--layout', choices=['full', 'portrait'], default='full')
    a = p.parse_args()
    prepare(a.project, a.title, a.layout)
