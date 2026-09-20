"""
Run the full gambits data pipeline end to end:

    1. build-gambits.py          Lichess TSV + is_gambit() filter -> gambits.csv (fully automated)
    2. build-transpositions.py   BFS over the Explorer API -> transpositions.json
    3. generate-gambits-json.py  gambits.csv + gambits-delta.csv + transpositions.json -> gambits.json
    4. cache:update --all        only if step 3 changed gambits.json or transpositions.json changed

All manual curation lives in scripts/gambits-delta.csv; nothing else in this
pipeline requires a human to touch it. Run from the project root.

Usage:
    python scripts/pipeline.py                       # full run, fetch fresh stats everywhere
    python scripts/pipeline.py --no-stats             # reuse cached stats (fast, for delta-only changes)
    python scripts/pipeline.py --skip-transpositions  # skip the slow BFS step, reuse existing transpositions.json
    python scripts/pipeline.py --skip-cache-update     # stop after generating gambits.json
    python scripts/pipeline.py --lichess-token <token>
"""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMBITS_JSON = ROOT / 'public' / 'data' / 'gambits.json'
TRANSPOSITIONS_JSON = ROOT / 'scripts' / 'transpositions.json'


def sha256_of(path: Path) -> str:
    if not path.exists():
        return ''
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], step: str) -> None:
    print(f'\n=== {step} ===')
    print(f'$ {" ".join(cmd)}')
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f'\n{step} failed (exit {result.returncode}); stopping pipeline.', file=sys.stderr)
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--no-stats', action='store_true', help='Reuse cached stats in gambits.csv instead of calling the Lichess API')
    parser.add_argument('--skip-transpositions', action='store_true', help='Skip the BFS transposition rebuild and reuse the existing transpositions.json')
    parser.add_argument('--skip-cache-update', action='store_true', help='Stop after generating gambits.json; do not refresh player caches')
    parser.add_argument('--lichess-token', default='', metavar='TOKEN', help='Lichess API token, forwarded to every step that calls the Explorer API')
    args = parser.parse_args()

    python = sys.executable
    token_args = ['--lichess-token', args.lichess_token] if args.lichess_token else []

    before = {
        'gambits.json': sha256_of(GAMBITS_JSON),
        'transpositions.json': sha256_of(TRANSPOSITIONS_JSON),
    }

    build_cmd = [python, 'scripts/build-gambits.py', *token_args]
    if args.no_stats:
        build_cmd.append('--no-stats')
    run(build_cmd, 'Step 1/3: build-gambits.py (fetch + filter -> gambits.csv)')

    if args.skip_transpositions:
        print('\n=== Step 2/3: build-transpositions.py === (skipped, reusing existing transpositions.json)')
    else:
        run([python, 'scripts/build-transpositions.py', *token_args], 'Step 2/3: build-transpositions.py (BFS -> transpositions.json)')

    run(
        [python, 'scripts/generate-gambits-json.py', '--fetch-stats', *token_args],
        'Step 3/3: generate-gambits-json.py (apply delta -> gambits.json)',
    )

    after = {
        'gambits.json': sha256_of(GAMBITS_JSON),
        'transpositions.json': sha256_of(TRANSPOSITIONS_JSON),
    }

    changed = [name for name in before if before[name] != after[name]]

    if args.skip_cache_update:
        print(f'\nPipeline complete. Changed: {", ".join(changed) or "nothing"}. Cache update skipped (--skip-cache-update).')
        return

    if not changed:
        print('\nPipeline complete. gambits.json and transpositions.json are unchanged; skipping cache update.')
        return

    print(f'\n{", ".join(changed)} changed -- refreshing player caches.')
    run(['npx', 'tsx', 'scripts/update-cache.ts', '--all'], 'Step 4/4: cache:update --all')
    print('\nPipeline complete.')


if __name__ == '__main__':
    main()
