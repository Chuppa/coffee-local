"""Calendar-version and publish tested HACS releases without manual version edits."""
from datetime import datetime
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_notes import format_notes
from zoneinfo import ZoneInfo

MANIFEST = 'custom_components/coffee_local/manifest.json'
INPUTS = ('custom_components/coffee_local', 'README.md', 'hacs.json')


def key(version):
    if not re.fullmatch(r'20\d{2}\.(?:[1-9]|1[0-2])\.\d+', version):
        raise ValueError('Expected year.month.release version')
    return tuple(map(int, version.split('.')))


def next_version(version, today=None):
    old = key(version)
    today = today or datetime.now(ZoneInfo('Australia/Sydney')).date()
    month = (today.year, today.month)
    if month < old[:2]:
        raise ValueError('Release clock predates the current version')
    return f'{month[0]}.{month[1]}.{old[2] + 1 if month == old[:2] else 0}'


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def api(path, data=None, missing=False):
    args = ['gh', 'api', path]
    if data is not None:
        args += ['--method', 'POST', '--input', '-']
    result = subprocess.run(args, input=json.dumps(data) if data is not None else None,
                            text=True, capture_output=True)
    if result.returncode:
        if missing and 'HTTP 404' in result.stderr:
            return None
        raise RuntimeError('GitHub request failed: ' + result.stderr)
    return json.loads(result.stdout) if result.stdout else {}


def release_needed(latest):
    if latest is None:
        return True
    tag = latest['tag_name']
    if latest.get('draft') or latest.get('prerelease') or not tag.startswith('v'):
        raise ValueError('Expected a stable calendar release')
    key(tag[1:])
    return command('git', 'ls-tree', 'HEAD', '--', *INPUTS) != command('git', 'ls-tree', tag, '--', *INPUTS)


def prepare(today=None):
    repo = os.environ['GITHUB_REPOSITORY']
    latest = api(f'repos/{repo}/releases/latest', missing=True)
    manifest = json.loads(Path(MANIFEST).read_text())
    key(manifest['version'])
    needed = release_needed(latest)
    if needed:
        published = latest['tag_name'][1:] if latest else None
        tags = [tag for tag in command('git', 'tag', '--list', 'v20*').splitlines()
                if re.fullmatch(r'v20\d{2}\.(?:[1-9]|1[0-2])\.\d+', tag)]
        reserved = max(tags, key=lambda tag: key(tag[1:])) if tags else None
        previous = max([v for v in (published, reserved[1:] if reserved else None) if v],
                       key=key, default=None)
        same_reserved = reserved and command('git', 'ls-tree', 'HEAD', '--', *INPUTS) == command('git', 'ls-tree', reserved, '--', *INPUTS)
        if previous and key(manifest['version']) <= key(previous) and not same_reserved:
            manifest['version'] = next_version(previous, today)
        Path(MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n')
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write(f'publish={str(needed).lower()}\nversion={manifest["version"]}\n')
    print('HACS release ' + ('required: ' + manifest['version'] if needed else 'already current; no version bump'))


def scope(prefix, commit):
    tree = api(prefix + '/git/commits/' + commit)['tree']['sha']
    data = api(prefix + '/git/trees/' + tree + '?recursive=1')
    if data.get('truncated'):
        raise ValueError('Truncated release scope')
    result = {entry['path']: entry['sha'] for entry in data['tree'] if entry['path'] in INPUTS}
    if set(result) != set(INPUTS):
        raise ValueError('Missing release inputs')
    return result


def release_notes(prefix, tag, sha):
    latest = api(prefix + '/releases/latest', missing=True)
    previous = latest.get('tag_name') if latest else None
    data = {'tag_name': tag, 'target_commitish': sha}
    if previous and previous != tag:
        data['previous_tag_name'] = previous
    try:
        generated = api(prefix + '/releases/generate-notes', data).get('body', '')
    except RuntimeError:
        generated = ''
    if generated.strip():
        generated = re.sub(r"^## What[’']s [Cc]hanged\s*", '', generated)
        return format_notes(generated)
    # Keep publication working if GitHub's optional notes service is unavailable.
    url = 'https://github.com/' + os.environ['GITHUB_REPOSITORY']
    url += '/compare/' + previous + '...' + tag if previous and previous != tag else '/tree/' + sha
    return format_notes('- See the [tested source changes](' + url + ').')


def publish():
    repo = os.environ['GITHUB_REPOSITORY']
    base = os.environ['GITHUB_SHA']
    version = os.environ['RELEASE_VERSION']
    key(version)
    prefix = f'repos/{repo}'
    if api(prefix + '/git/ref/heads/main')['object']['sha'] != base:
        raise ValueError('Main changed after testing; next maintenance cycle will retry')
    manifest = json.loads(Path(MANIFEST).read_text())
    manifest['version'] = version
    content = json.dumps(manifest, indent=2) + '\n'
    sha = base
    if Path(MANIFEST).read_text() != content:
        tree = api(prefix + '/git/commits/' + base)['tree']['sha']
        tree = api(prefix + '/git/trees', {'base_tree': tree, 'tree': [
            {'path': MANIFEST, 'mode': '100644', 'type': 'blob', 'content': content}]})['sha']
        sha = api(prefix + '/git/commits', {'message': 'Release Coffee Local ' + version,
                  'tree': tree, 'parents': [base]})['sha']
        # A non-forced update rejects a competing main change.
        result = subprocess.run(['gh', 'api', '--method', 'PATCH', prefix + '/git/refs/heads/main',
                                '--input', '-'], input=json.dumps({'sha': sha, 'force': False}),
                                text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError('Cannot advance tested release version: ' + result.stderr)
    tag = 'v' + version
    existing = api(prefix + '/git/ref/tags/' + tag, missing=True)
    if existing and existing['object']['sha'] != sha:
        if existing['object']['type'] != 'commit' or scope(prefix, existing['object']['sha']) != scope(prefix, sha):
            raise ValueError('Refusing to replace an immutable release tag')
        sha = existing['object']['sha']
    if not existing:
        api(prefix + '/git/refs', {'ref': 'refs/tags/' + tag, 'sha': sha})
    release = api(prefix + '/releases/tags/' + tag, missing=True)
    if release is None:
        api(prefix + '/releases', {'tag_name': tag, 'name': 'Coffee Local ' + version,
            'body': release_notes(prefix, tag, sha),
            'draft': False, 'prerelease': False})
    print('Published ' + tag + ' from tested source ' + sha)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('prepare', 'publish'))
    operation = parser.parse_args().operation
    prepare() if operation == 'prepare' else publish()
