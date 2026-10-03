#!/usr/bin/env python3
"""Run with python3 .github/scripts/test-toolchain-cache.py."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)

    def write(path, text, executable=False):
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)
        if executable:
            destination.chmod(0o755)

    def run(*args, **kwargs):
        return subprocess.run(args, cwd=root, check=True, capture_output=True, text=True, **kwargs).stdout.strip()

    packages = []
    for name, host, target, unpack in [
        ('toolchain', '', 'gcc:host', ''),
        ('gcc', 'gettext:host', '', ''),
        ('gettext', '', '', 'helper'),
        ('helper', '', '', 'nested'),
        ('nested', '', '', ''),
        ('baseos', '', 'toolchain', ''),
        ('image', '', 'baseos', ''),
    ]:
        packages.append(dict(name=name, hierarchy='global', section='', bootstrap='', init='', host=host, target=target, unpack=unpack))
        write(f'packages/{name}/package.mk', name + '\n')
    graph = ',\n'.join(json.dumps(p) for p in packages) + ',\n'
    write('scripts/pkgjson', '#!/bin/sh\ncat packages.json\n', True)
    write('packages.json', graph)
    write('scripts/genbuildplan.py', (repo / 'scripts/genbuildplan.py').read_text(), True)
    write('.github/scripts/toolchain-cache-key.sh', (repo / '.github/scripts/toolchain-cache-key.sh').read_text())
    write('.github/workflows/build-baseos-cache-benchmark.yml', 'benchmark workflow\n')
    write('projects/ROCKNIX/packages/baseos/package.mk', 'baseos recipe\n')
    write('projects/ROCKNIX/packages/baseos/scripts/baseos-launch', 'launcher v1\n')
    write('compiler', 'compiler v1\n')
    write('libraries', 'libc 1\n')
    write('bin/dpkg-query', '#!/bin/sh\ncat libraries\n', True)
    write('config/options', '''ROOT="$PWD"
PROJECT=ROCKNIX
DISTRO=ROCKNIX
DEVICE=RK3566
ARCH=aarch64
LOCAL_CC="$ROOT/compiler"
LOCAL_CXX="$ROOT/compiler"
PKG_NAME="${1%%:*}"
calculate_stamp() {
  find optional-patches -type f 2>/dev/null | sha256sum
  sha256sum "packages/$PKG_NAME/package.mk"
  if [ -f "projects/ROCKNIX/packages/$PKG_NAME/package.mk" ]; then
    sha256sum "projects/ROCKNIX/packages/$PKG_NAME/package.mk"
  fi
}
''')
    write('projects/ROCKNIX/devices/RK3566/options', 'device v1\n')
    write('distributions/ROCKNIX/options', 'distribution v1\n')
    (root / 'distributions/Other').mkdir()
    (root / 'distributions/Other/broken-link').symlink_to('missing')
    run('git', 'init', '-q')
    run('git', 'add', '.')
    env = {**os.environ, 'PATH': str(root / 'bin') + os.pathsep + os.environ['PATH'], 'BASEOS': 'yes', 'BASE_ONLY': 'true'}

    def key(**overrides):
        return run('bash', '.github/scripts/toolchain-cache-key.sh', 'toolchain', env={**env, **overrides})

    original = key()
    assert len(original) == 64 and all(c in '0123456789abcdef' for c in original)
    assert key() == original, 'unchanged inputs must reuse the toolchain'
    write('packages/baseos/package.mk', 'unrelated application edit\n')
    assert key() == original, 'application recipes must not invalidate the toolchain'
    for path in ['packages/gcc/package.mk', 'packages/nested/package.mk', 'compiler', 'libraries', 'projects/ROCKNIX/devices/RK3566/options', 'distributions/ROCKNIX/options', 'scripts/genbuildplan.py']:
        previous = (root / path).read_text()
        write(path, previous + ('\n# changed\n' if path.endswith('.py') else 'changed\n'), path.endswith('.py'))
        assert key() != original, f'{path} must invalidate the toolchain'
        write(path, previous, path.endswith('.py'))
    write('projects/ROCKNIX/packages/gcc/package.mk', 'override\n')
    assert key() != original, 'new overrides must invalidate the toolchain'
    (root / 'projects/ROCKNIX/packages/gcc/package.mk').unlink()
    assert key(SUSPEND='false') != original, 'suspend variants must remain separate'
    assert key(BASEOS='no') != original, 'build profiles must remain separate'
    other = root / 'relocated'
    shutil.copytree(root, other, symlinks=True, ignore=shutil.ignore_patterns('relocated'))
    moved = subprocess.run(['bash', '.github/scripts/toolchain-cache-key.sh', 'toolchain'], cwd=other, env=env, check=True, capture_output=True, text=True)
    assert moved.stdout.strip() != original, 'archives cannot move between absolute build paths'
    def image_key():
        return run('bash', '.github/scripts/toolchain-cache-key.sh', 'image', env={**env, 'CACHE_LAYER': 'baseos-packages'})

    image_original = image_key()
    write('projects/ROCKNIX/packages/baseos/scripts/baseos-launch', 'launcher v2\n')
    assert image_key() == image_original, 'always-rebuilt launcher must reuse dependencies'
    write('projects/ROCKNIX/packages/baseos/config/sway.config', 'updated config\n')
    run('git', 'add', 'projects/ROCKNIX/packages/baseos/config/sway.config')
    assert image_key() == image_original, 'always-rebuilt config must reuse dependencies'
    for path in ['packages/nested/package.mk', 'projects/ROCKNIX/packages/baseos/package.mk']:
        previous = (root / path).read_text()
        write(path, previous + 'changed\n')
        assert image_key() != image_original, f'{path} must invalidate package cache'
        write(path, previous)
    write('packages.json', 'invalid graph\n')
    failed = subprocess.run(['bash', '.github/scripts/toolchain-cache-key.sh', 'toolchain'], cwd=root, env=env, capture_output=True, text=True)
    assert failed.returncode != 0, 'invalid dependency plans must fail closed'
print('Toolchain cache checks passed.')
