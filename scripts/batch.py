"""Run independent prepared card projects; report partial failure accurately."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from workflow import save_json

def projects(manifest):
    manifest = Path(manifest).resolve()
    entries = json.loads(manifest.read_text())['projects']
    if not entries or len(entries) != len(set(entries)):
        raise ValueError('projects must be nonempty and unique')
    result = [(manifest.parent / entry).resolve() for entry in entries]
    if any(not p.is_relative_to(manifest.parent) or p == manifest.parent for p in result):
        raise ValueError('Project paths must stay below the manifest directory')
    if len(result) != len(set(result)):
        raise ValueError('Duplicate resolved project paths')
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('manifest')
    p.add_argument('--blender')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--skip-render', action='store_true')
    p.add_argument('--skip-npm', action='store_true')
    a = p.parse_args()
    entries = projects(a.manifest)
    results = []
    for project in entries:
        cmd = [sys.executable, str(Path(__file__).with_name('run_pipeline.py')), '--project', str(project), '--resume']
        if a.blender:
            cmd += ['--blender', a.blender]
        if a.skip_render:
            cmd.append('--skip-render')
        if a.skip_npm:
            cmd.append('--skip-npm')
        if a.dry_run:
            print(json.dumps(cmd, ensure_ascii=False))
            continue
        result = subprocess.run(cmd)
        results.append({'project': str(project), 'status': 'built_needs_review' if result.returncode == 0 else 'failed', 'exit_code': result.returncode})
        save_json(Path(a.manifest).resolve().parent / 'batch-status.json', results)
    sys.exit(1 if any(r['exit_code'] for r in results) else 0)
