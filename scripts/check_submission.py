#!/usr/bin/env python3
"""Offline submission inventory, obvious-secret checks and local Markdown links.

Uses Git's candidate list when this directory is a repository; otherwise excludes
the documented local-only directories. Prints locations/types, never secret values.
This bounded check is not a guarantee that arbitrary new content is secret-free.
"""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'build', 'dist', 'artifacts'}
TOKEN_NAME = re.compile(r'^(?:csrf[-_]?token|authenticity_token|access_token|refresh_token|api_key|x-api-key)$', re.I)
SECRET_FORMATS = re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|'
                            r'\b(?:gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{24,}|'
                            r'sk-[A-Za-z0-9_-]{24,}|AKIA[A-Z0-9]{16}|AIza[0-9A-Za-z_-]{35}|'
                            r'xox[baprs]-[A-Za-z0-9-]{12,})')


def placeholder(value):
    return any(part in value for part in ('[REDACTED]', '${', '<%', 'fixture-', 'example-'))


class FormValues(HTMLParser):
    def __init__(self):
        super().__init__()
        self.count = 0

    def handle_starttag(self, tag, attrs):
        if tag not in ('meta', 'input'):
            return
        attrs = dict(attrs)
        if not any(TOKEN_NAME.fullmatch(attrs.get(key) or '') for key in ('name', 'id')):
            return
        for key in ('content', 'value'):
            value = attrs.get(key) or ''
            if value and not placeholder(value):
                self.count += 1


def candidates(include_research=False):
    try:
        check = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
        is_repo = check.returncode == 0 and Path(check.stdout.strip()).resolve() == ROOT
    except FileNotFoundError:
        is_repo = False
    if is_repo and not include_research:
        result = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                                capture_output=True, check=True)
        return sorted({ROOT / os.fsdecode(p) for p in result.stdout.split(b'\0') if p}), 'git_candidates'
    paths = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in LOCAL_DIRS and not d.endswith('.egg-info')
                   and (include_research or not (Path(base) == ROOT and d == 'research'))]
        for name in names:
            if name == '.DS_Store' or name.endswith(('.pyc', '.log')) or name == '.env' or name.startswith('.env.'):
                continue
            paths.append(Path(base) / name)
    return sorted(paths), 'local_tree_with_research' if include_research else 'local_submission_tree'


def inspect_file(path):
    rel = path.relative_to(ROOT).as_posix()
    issues = []
    if path.is_symlink():
        return [{'file': rel, 'kind': 'symlink_requires_review'}]
    if not path.is_file():
        return [{'file': rel, 'kind': 'missing_or_special_file'}]
    try:
        body = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return [{'file': rel, 'kind': 'binary_requires_review'}]
    for kind, pattern in (
        ('private_key_or_service_token', SECRET_FORMATS),
        ('authorization_header', re.compile(r'(?im)^\s*(?:Authorization|Proxy-Authorization|Cookie|Set-Cookie)\s*:\s*\S+')),
    ):
        if pattern.search(body):
            issues.append({'file': rel, 'kind': kind})
    # Public website routes such as https://owner.tabelog.com/home/registration/
    # are URL paths, not local operating-system home directories.
    outside_urls = re.sub(r'https?://[^\s"<>\\]+', '', body)
    if re.search(r'/(?:Users|home)/[A-Za-z][A-Za-z0-9_.-]+/', outside_urls):
        issues.append({'file': rel, 'kind': 'personal_absolute_path'})
    credential_urls = re.findall(r'https?://[^/\s"<>]+:[^/@\s"<>]+@', body)
    if any(value != 'https://user:pass@' for value in credential_urls):
        issues.append({'file': rel, 'kind': 'url_credentials'})
    form_count = 0
    structured_count = 0

    def inspect(value):
        nonlocal form_count, structured_count
        if isinstance(value, dict):
            for key, item in value.items():
                if TOKEN_NAME.fullmatch(key) and isinstance(item, str) and item and not placeholder(item):
                    structured_count += 1
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
        elif isinstance(value, str) and re.search(r'<(?:meta|input)\b', value, re.I):
            parser = FormValues()
            parser.feed(value)
            form_count += parser.count
    if path.suffix == '.json':
        try:
            inspect(json.loads(body))
        except ValueError:
            issues.append({'file': rel, 'kind': 'invalid_json'})
    else:
        inspect(body)
    if form_count or structured_count:
        issues.append({'file': rel, 'kind': 'unredacted_verification_value', 'count': form_count + structured_count})
    if path.suffix == '.md':
        for target in re.findall(r'\]\(([^)]+)\)', body):
            if '://' in target or target.startswith('#'):
                continue
            local = target.strip('<>').split('#')[0]
            if not (path.parent / local).exists():
                issues.append({'file': rel, 'kind': 'broken_local_link', 'target': target})
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-research', action='store_true', help='Also inspect ignored local captures, without printing their contents.')
    args = parser.parse_args()
    paths, scope = candidates(args.include_research)
    issues = []
    for path in paths:
        rel = path.relative_to(ROOT)
        if scope == 'git_candidates' and (rel.parts[0] == 'research' or any(p in LOCAL_DIRS or p.endswith('.egg-info') for p in rel.parts)):
            issues.append({'file': rel.as_posix(), 'kind': 'local_only_file_tracked'})
        issues.extend(inspect_file(path))
    root_lock = (ROOT/'requirements.lock').read_text(encoding='utf-8')
    locks = {'tabelog': root_lock, 'tablecheck': '\n'.join(line for line in root_lock.splitlines() if not line.startswith('jpholiday=='))+'\n'}
    for platform in ('tabelog', 'tablecheck'):
        skill_lock = ROOT/'skills'/platform/'scripts/requirements.txt'
        if not skill_lock.is_file() or skill_lock.read_text(encoding='utf-8') != locks[platform]:
            issues.append({'kind': 'standalone_skill_lock_mismatch', 'platform': platform})
        skill_license = ROOT/'skills'/platform/'LICENSE'
        if not skill_license.is_file() or skill_license.read_bytes() != (ROOT/'LICENSE').read_bytes():
            issues.append({'kind': 'standalone_skill_license_mismatch', 'platform': platform})
    for name in ('tabelog-cli.txt', 'tabelog-cli.provenance.json'):
        if not (ROOT/'skills/tabelog/scripts/client/licenses'/name).is_file():
            issues.append({'kind': 'missing_upstream_attribution', 'name': name})
    print(json.dumps({'status': 'error' if issues else 'ok', 'scope': scope, 'files_checked': len(paths),
                      'bytes_checked': sum(p.stat().st_size for p in paths if p.is_file()),
                      'issue_counts': dict(Counter(i['kind'] for i in issues)), 'issues': issues,
                      'limits': 'Offline pattern/structure checks, not a comprehensive secret detector. Review new file content and the actual staged diff before committing.'},
                     ensure_ascii=False, indent=2))
    return int(bool(issues))


if __name__ == '__main__':
    raise SystemExit(main())
