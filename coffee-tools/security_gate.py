"""Retain all CodeQL findings; block HIGH/CRITICAL before automatic publication."""
import json
from pathlib import Path


def blocking(report):
    count = 0
    for run in report.get('runs', []):
        rules = {rule['id']: rule for rule in run['tool']['driver'].get('rules', [])}
        for result in run.get('results', []):
            rule = rules.get(result.get('ruleId'), {})
            score = rule.get('properties', {}).get('security-severity')
            if score is not None and float(score) >= 7:
                count += 1
    return count


if __name__ == '__main__':
    reports = list(Path('work/codeql').glob('*.sarif'))
    if not reports:
        raise SystemExit('CodeQL produced no reports; refusing release')
    total = sum(blocking(json.loads(path.read_text())) for path in reports)
    print(f'CodeQL security gate: {total} HIGH/CRITICAL findings; all reports retained')
    raise SystemExit(1 if total else 0)
