"""Keep one actionable maintenance issue; close it after the next successful run."""
import json
import os
import subprocess

def gh(*args):return subprocess.check_output(['gh',*args],text=True).strip()
repo=os.environ['GITHUB_REPOSITORY']
title=os.environ.get('ISSUE_TITLE','Coffee Local automatic maintenance needs attention')
issues=json.loads(gh('issue','list','--repo',repo,'--state','open','--search',title+' in:title','--json','number,title'))
issues=[i for i in issues if i['title']==title]
failed=os.environ['FAILED']=='true'
url=os.environ.get('FAILED_RUN_URL') or 'https://github.com/'+repo+'/actions/runs/'+os.environ['GITHUB_RUN_ID']
if failed:
    body='An integration compatibility test, source-security check, automatic release or dependency update failed. The last stable HACS release remains available. The next scheduled run will retry.\n\nRun details: '+url
    if not issues:gh('issue','create','--repo',repo,'--title',title,'--body',body)
    else:gh('issue','edit',str(issues[0]['number']),'--repo',repo,'--body',body)
else:
    for issue in issues:gh('issue','close',str(issue['number']),'--repo',repo)
