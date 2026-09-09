"""Resume prepared-artwork builds while protecting customized outputs."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
from ensure_blender import ensure_blender
from validate_assets import validate
from generate_typography import create
from workflow import cached, digest, fingerprint, protect, read_state, save_json, sync_template

def run(a):
    root = Path(a.project).resolve()
    scripts = Path(__file__).resolve().parent
    template = scripts.parent / 'assets/web-template'
    config = root / 'card-config.json'
    cfg = json.loads(config.read_text(encoding='utf-8-sig'))
    safe = cfg.get('safeArea', {})
    scale = safe.get('scale', 1.12)
    values = scale if isinstance(scale, list) else [scale, scale]
    if len(values) != 2 or not all(isinstance(v, (int, float)) and 0 < v <= 3 for v in values):
        raise ValueError('safeArea.scale must be positive scalar or two numbers <= 3')
    offset = safe.get('offset', [-.06, -.06])
    if len(offset) != 2 or not all(isinstance(v, (int, float)) for v in offset):
        raise ValueError('safeArea.offset needs two numbers')
    state_path = root / '.holo-state.json'
    state = read_state(state_path)
    web = root / 'web'
    sync_template(template, web, a.replace_web, check=True)
    web_outputs = [web / 'card-config.json', *[web / 'assets' / (n + '.png') for n in ['subject', 'background', 'text', 'lineart']]]
    protect(root, web_outputs, state.get('web', {}), a.replace_output)
    text = root / 'assets/text.png'
    text_key = fingerprint([config, scripts / 'generate_typography.py'])
    old_text = state.get('typography', {})
    if not text.exists() or old_text and old_text.get('key') != text_key:
        protect(root, [text], old_text, a.replace_output)
        create(root)
        state['typography'] = {'key': text_key, 'outputs': {'assets/text.png': digest(text)}}
        save_json(state_path, state)
    validate(root)
    blender = ensure_blender(root, a.blender)
    inputs = [config, *sorted((root / 'assets').glob('*.png'))]
    key = fingerprint(inputs + [scripts / 'build_card.py']) + str(Path(blender).stat().st_mtime_ns)
    build_outputs = [root / 'card.blend', root / 'verification.json']
    if not a.skip_render:
        build_outputs.append(root / 'renders/hero.png')
        key += ':render'

    def stage(name, stage_key, outputs, action):
        previous = state.get(name, {})
        if a.resume and cached(previous, stage_key, root):
            print('CACHED', name, flush=True)
            return
        protect(root, outputs, previous, a.replace_output)
        state[name] = {**previous, 'status': 'running'}
        save_json(state_path, state)
        try:
            action()
            for p in outputs:
                if not p.is_file() or p.stat().st_size == 0:
                    raise RuntimeError('Missing output: ' + str(p))
        except (OSError, subprocess.CalledProcessError, RuntimeError) as e:
            state[name]['status'] = 'failed'
            state[name]['error'] = str(e)
            save_json(state_path, state)
            raise
        state[name] = {'status': 'built', 'key': stage_key,
                       'outputs': {str(p.relative_to(root)): digest(p) for p in outputs}}
        save_json(state_path, state)

    cmd = [str(blender), '--background', '--factory-startup', '--python', str(scripts / 'build_card.py'), '--', str(root)]
    if a.skip_render:
        cmd.append('--skip-render')
    stage('blender', key, build_outputs, lambda: subprocess.run(cmd, check=True))
    export_key = fingerprint([root / 'card.blend', scripts / 'export_web.py'])
    stage('export', export_key, [web / 'assets/card.glb'], lambda: subprocess.run(
        [str(blender), '--background', '--python', str(scripts / 'export_web.py'), '--', str(root)], check=True))
    sync_template(template, web, a.replace_web)
    cfg['assets'] = {n: './assets/' + n + '.png' for n in ['subject', 'background', 'text', 'lineart']}
    cfg['assets']['model'] = './assets/card.glb'
    save_json(web / 'card-config.json', cfg)
    for name in ['subject', 'background', 'text', 'lineart']:
        shutil.copy2(root / 'assets' / (name + '.png'), web / 'assets' / (name + '.png'))
    if not a.skip_npm:
        npm = shutil.which('npm.cmd') or shutil.which('npm')
        if not npm:
            raise RuntimeError('Node.js/npm is required for the web viewer')
        package_key = fingerprint([web / 'package.json', web / 'package-lock.json'])
        if not (a.resume and state.get('npm') == package_key and (web / 'node_modules/three/package.json').exists()):
            subprocess.run([npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], cwd=web, check=True)
            state['npm'] = package_key
    state['visual_review'] = 'required'
    state['web'] = {'outputs': {str(p.relative_to(root)): digest(p) for p in web_outputs}}
    save_json(state_path, state)
    print('BUILT; visual review still required:', root)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--project', required=True)
    p.add_argument('--blender')
    for flag in ['resume', 'skip-render', 'skip-npm', 'replace-web', 'replace-output']:
        p.add_argument('--' + flag, action='store_true')
    run(p.parse_args())
