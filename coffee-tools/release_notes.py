"""Use the exact app changelog entry for GitHub releases as well as Supervisor."""
from pathlib import Path
import re


def format_notes(body):
    """Group real changelog content without inventing versions or attribution."""
    if body.lstrip().startswith(('## What’s changed', "## What's changed")):
        return body.strip() + '\n'
    groups = {'Changes': [], '⬆️ Dependency updates': [], '🛡️ Security updates': [], '🔧 Maintenance': []}
    body = re.sub(r'^\* ', '- ', body, flags=re.M)
    blocks = re.split(r'(?=^- )', body.strip(), flags=re.M)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if 'Automatic dependency/base refresh and OS security rebuild.' in block:
            block = block.replace('Automatic dependency/base refresh and OS security rebuild.',
                                  'Rebuild runtime OS packages to pick up available security fixes.')
        lower = block.lower()
        if 'rebuild runtime os packages' in lower or 'daily precautionary' in lower:
            group = '🔧 Maintenance'
        elif re.search(r'\b(security|vulnerab\w*|fixable|high/critical|cve-\d|go-\d{4}|openpgp)\b', lower):
            group = '🛡️ Security updates'
        elif re.search(r'\b(documentation|wording|option labels|help text|readme)\b', lower):
            group = 'Changes'
        elif re.search(r'\b(updat\w*|upgrad\w*|dependenc\w*|base image|compiler)\b', lower):
            group = '⬆️ Dependency updates'
        else:
            group = 'Changes'
        if group == '⬆️ Dependency updates' and block.startswith('- ') and not block.startswith('- ⬆️ '):
            block = '- ⬆️ ' + block[2:]
        groups[group].append(block)
    result = '## What’s changed\n'
    for title, entries in groups.items():
        if entries:
            result += '\n## ' + title + '\n\n' + '\n'.join(entries) + '\n'
    return result

