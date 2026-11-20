"""Publish public branch snapshots. Never run scripts from the source repository."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone

SOURCE = 'kmitsu1313/-Design_Archive'
PUBLIC = 'https://kmitsu1313.github.io/Design_Archive-preview/'
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'


def api(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Design-Archive-preview'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    with urllib.request.urlopen(urllib.request.Request('https://api.github.com/' + path, headers=headers), timeout=40) as response:
        return json.load(response)


def pages(path):
    result = []
    for page in range(1, 101):
        batch = api(path + ('&' if '?' in path else '?') + f'per_page=100&page={page}')
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise RuntimeError('Too many API pages')


def git(directory, *args):
    return subprocess.check_output(['git', '-C', str(directory), *args])


def output(changed):
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as file:
            file.write(f'changed={str(changed).lower()}\n')


def main():
    branches = pages(f'repos/{SOURCE}/branches')
    prs = pages(f'repos/{SOURCE}/pulls?state=open')
    main_sha = next(b['commit']['sha'] for b in branches if b['name'] == 'main')
    versions = []
    for branch in sorted(branches, key=lambda b: b['name']):
        name, sha = branch['name'], branch['commit']['sha']
        if sha == main_sha or api(
            f'repos/{SOURCE}/compare/{main_sha}...{sha}?per_page=1'
        )['ahead_by'] == 0:
            continue
        pr = next((p for p in prs if p['head']['ref'] == name and p['head']['repo'] and p['head']['repo']['full_name'] == SOURCE), None)
        key = f"pr-{pr['number']}" if pr else 'branch-' + hashlib.sha256(name.encode()).hexdigest()[:12]
        versions.append({'id': key, 'branch': name, 'sha': sha, 'path': key + '/', 'pr': pr['html_url'] if pr else None, 'title': pr['title'] if pr else name})
    fingerprint = hashlib.sha256(json.dumps(versions, sort_keys=True).encode()).hexdigest()
    if os.environ.get('FORCE_BUILD') == 'false':
        try:
            with urllib.request.urlopen(PUBLIC + 'versions.json', timeout=20) as response:
                if json.load(response).get('fingerprint') == fingerprint:
                    output(False)
                    print('No source changes; existing preview retained.')
                    return
        except (OSError, ValueError):
            pass
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    total = 0
    with tempfile.TemporaryDirectory() as temporary:
        checkout = Path(temporary)
        git(checkout, 'init', '-q')
        git(checkout, 'remote', 'add', 'origin', 'https://github.com/' + SOURCE + '.git')
        if versions:
            commits = dict.fromkeys(version['sha'] for version in versions)
            git(checkout, 'fetch', '-q', '--no-tags', '--depth=1', 'origin', *commits)
        for version in versions:
            git(checkout, 'checkout', '-q', '--detach', '--force', version['sha'])
            version['updated'] = git(checkout, 'show', '-s', '--format=%cI', version['sha']).decode().strip()
            files = git(checkout, 'ls-files', '-z').decode().split('\0')
            legacy_font = 'library/assets/fonts/SourceHanSansSC-VF.otf'
            if legacy_font in files:
                references = subprocess.run([
                    'git', '-C', str(checkout), 'grep', '-I', '-i', '-q', '-F',
                    'SourceHanSansSC-VF', '--', '.', ':(exclude)' + legacy_font,
                ])
                if references.returncode == 1:
                    files.remove(legacy_font)
                else:
                    references.check_returncode()
            target = OUT / version['id']
            for name in filter(None, files):
                path = Path(name)
                if any(part.startswith('.') for part in path.parts) or path.suffix.lower() in {'.md', '.pdf'} or name == 'CNAME':
                    continue
                source = checkout / path
                if source.is_symlink() or not source.is_file():
                    continue
                total += source.stat().st_size
                if total > 900_000_000:
                    raise RuntimeError('Preview exceeds 900 MB. Remove stale source branches or reduce assets; previous deployed site is retained.')
                dest = target / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
            if not (target / 'index.html').exists():
                raise RuntimeError('Missing site entry: ' + version['branch'])
            version['wendao'] = (target / 'library/wendao/index.html').exists()
            print(version['branch'], version['sha'][:7], 'copied')
    for path in (ROOT / 'web').iterdir():
        shutil.copyfile(path, OUT / path.name)
    (OUT / '.nojekyll').touch()
    (OUT / 'versions.json').write_text(json.dumps({'source': SOURCE, 'generated': datetime.now(timezone.utc).isoformat(), 'fingerprint': fingerprint, 'versions': versions}, ensure_ascii=False, indent=2), encoding='utf-8')
    output(True)
    print(f'{len(versions)} versions; {total / 1_000_000:.1f} MB')


if __name__ == '__main__':
    main()
