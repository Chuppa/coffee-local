# MIT-licensed helper; copyright and permission notice in LICENSE-MIT.txt.
"""Merge only tested Dependabot action-pin changes; never execute the PR's code here."""
from collections import Counter
import json
import os
import re
import subprocess

def gh(*args):return subprocess.check_output(['gh',*args],text=True).strip()
repo=os.environ['GITHUB_REPOSITORY']
event=json.load(open(os.environ['GITHUB_EVENT_PATH']))
run=event['workflow_run']
if run['conclusion']!='success' or run['head_repository']['full_name']!=repo:
    raise SystemExit('Not a successful same-repository check')
prs=json.loads(gh('api',f'repos/{repo}/pulls?state=open&head='+repo.split('/')[0]+':'+run['head_branch']))
for pr in prs:
    if pr['user']['login']!='dependabot[bot]' or pr['head']['sha']!=run['head_sha'] or pr['base']['ref']!='main':continue
    files=json.loads(gh('api',f'repos/{repo}/pulls/{pr["number"]}/files'))
    if not files or len(files)>=100:raise ValueError('Unexpected or truncated action update')
    for file in files:
        if file['status']!='modified' or not re.fullmatch(r'\.github/workflows/[\w-]+\.yml',file['filename']):
            raise ValueError('Action update contains non-workflow edits')
        added=[];removed=[]
        for line in file.get('patch','').splitlines():
            if line[:1] not in ('+','-'):continue
            match=re.fullmatch(r'\s*(?:-\s+)?uses:\s+([\w.-]+/[\w./-]+)@[a-f0-9]{40}(?:\s+#.*)?\s*',line[1:])
            if not match:raise ValueError('Only action SHA pin changes may auto-merge')
            (added if line[0]=='+' else removed).append(match[1])
        if not added or Counter(added)!=Counter(removed):raise ValueError('Action repositories must stay unchanged')
    base=gh('api',f'repos/{repo}/git/ref/heads/main','--jq','.object.sha')
    comparison=json.loads(gh('api',f'repos/{repo}/compare/{base}...{pr["head"]["sha"]}'))
    if comparison['merge_base_commit']['sha']!=base:
        print('Awaiting Dependabot automatic rebase and fresh full tests')
        continue
    merged=gh('api','--method','PUT',f'repos/{repo}/pulls/{pr["number"]}/merge','-f','sha='+pr['head']['sha'],'-f','merge_method=merge','--jq','.merged')
    if merged!='true':raise ValueError('Action update was not merged')
    print('Merged tested action pins:',pr['number'])

# GITHUB_TOKEN merges do not recursively start the check/release workflow.
gh('workflow','run','checks.yml','--repo',repo,'--ref','main')
