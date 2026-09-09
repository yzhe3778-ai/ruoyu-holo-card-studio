"""Hash-based stage cache and non-destructive template synchronization."""
import hashlib
import json
import shutil
import time
from pathlib import Path

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fingerprint(paths):
    return hashlib.sha256(json.dumps([(str(p), digest(p)) for p in sorted(paths)], sort_keys=True).encode()).hexdigest()

def save_json(path, data):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(path)

def read_state(path):
    return json.loads(Path(path).read_text()) if Path(path).exists() else {}

def cached(entry, key, root):
    return bool(entry and entry.get('key') == key and entry.get('outputs') and
                all((root / name).is_file() and digest(root / name) == value
                    for name, value in entry['outputs'].items()))

def backup(root, files):
    folder = root / '.holo-backups' / str(time.time_ns())
    for path in files:
        dest = folder / path.relative_to(root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    return folder

def protect(root, paths, previous, replace=False):
    old = previous.get('outputs', {})
    conflicts = [p for p in paths if p.exists() and old.get(str(p.relative_to(root))) != digest(p)]
    if conflicts and not replace:
        raise FileExistsError('Unmanaged or edited output; use --replace-output to back up first: ' + ', '.join(map(str, conflicts)))
    if conflicts:
        backup(root, conflicts)

def sync_template(source, target, replace=False, check=False):
    source, target = Path(source), Path(target)
    state_path = target / '.holo-template.json'
    previous = read_state(state_path)
    # Runtime configuration is generated separately, not a managed template.
    files = [p for p in source.rglob('*') if p.is_file() and p.relative_to(source).as_posix() != 'card-config.json']
    conflicts = []
    for p in files:
        rel = p.relative_to(source).as_posix()
        dest = target / rel
        if dest.exists() and digest(dest) not in [digest(p), previous.get(rel)]:
            conflicts.append(dest)
    if conflicts and not replace:
        raise FileExistsError('Customized web files; use --replace-web to back up first: ' + ', '.join(map(str, conflicts)))
    if check:
        return
    target.mkdir(parents=True, exist_ok=True)
    if conflicts:
        backup(target, conflicts)
    for p in files:
        dest = target / p.relative_to(source)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    save_json(state_path, {p.relative_to(source).as_posix(): digest(p) for p in files})
