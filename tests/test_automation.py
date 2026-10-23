from datetime import date
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'coffee-tools' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


release = module('automatic_release')
security = module('security_gate')


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = os.getcwd()
        os.chdir(self.temp.name)
        Path(release.MANIFEST).parent.mkdir(parents=True)
        Path(release.MANIFEST).write_text(json.dumps({'version': '2026.10.1'}, indent=2) + '\n')
        Path('README.md').write_text('Guide\n')
        Path('hacs.json').write_text('{}\n')
        self.git('init', '-q')
        self.commit()
        self.git('tag', 'v2026.10.1')
        self.env = patch.dict(os.environ, {'GITHUB_REPOSITORY': 'Chuppa/coffee-local',
                              'GITHUB_OUTPUT': str(Path('output').resolve()),
                              'GITHUB_SHA': 'a' * 40, 'RELEASE_VERSION': '2026.10.1'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        os.chdir(self.previous)
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', *args], text=True).strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'Fixture')

    def prepare(self):
        with patch.object(release, 'api', return_value={'tag_name': 'v2026.10.1'}):
            release.prepare(date(2026, 10, 23))
        return dict(line.split('=', 1) for line in Path('output').read_text().splitlines())

    def test_unchanged_cycle_has_no_release_or_version_bump(self):
        self.assertEqual(self.prepare(), {'publish': 'false', 'version': '2026.10.1'})

    def test_documentation_change_gets_one_automatic_version(self):
        Path('README.md').write_text('Updated guide\n')
        self.commit()
        self.assertEqual(self.prepare(), {'publish': 'true', 'version': '2026.10.2'})

    def test_workflow_only_change_does_not_release_integration(self):
        Path('.github').mkdir()
        Path('.github/check.yml').write_text('name: Fixture\n')
        self.commit()
        self.assertEqual(self.prepare()['publish'], 'false')

    def test_explicit_new_version_is_preserved(self):
        Path(release.MANIFEST).write_text('{"version":"2026.10.4"}')
        self.commit()
        self.assertEqual(self.prepare()['version'], '2026.10.4')

    def test_interrupted_tagged_release_keeps_its_reserved_version(self):
        Path(release.MANIFEST).write_text('{"version":"2026.10.2"}')
        self.commit()
        self.git('tag', 'v2026.10.2')
        self.assertEqual(self.prepare()['version'], '2026.10.2')

    def test_changed_content_after_reserved_tag_gets_another_version(self):
        Path(release.MANIFEST).write_text('{"version":"2026.10.2"}')
        self.commit()
        self.git('tag', 'v2026.10.2')
        Path('README.md').write_text('Another change\n')
        self.commit()
        self.assertEqual(self.prepare()['version'], '2026.10.3')

    def test_calendar_rollover_and_clock_rollback(self):
        self.assertEqual(release.next_version('2026.10.9', date(2026, 11, 1)), '2026.11.0')
        with self.assertRaises(ValueError):
            release.next_version('2026.11.0', date(2026, 10, 23))
        with self.assertRaises(ValueError):
            release.key('latest')

    def test_concurrent_main_change_blocks_publication(self):
        with patch.object(release, 'api', return_value={'object': {'sha': 'b' * 40}}) as api:
            with self.assertRaisesRegex(ValueError, 'Main changed'):
                release.publish()
            self.assertEqual(api.call_count, 1)

    def test_existing_tag_without_release_is_recovered_without_replacing_tag(self):
        calls = []
        def api(path, data=None, **kwargs):
            calls.append((path, data))
            if path.endswith('/git/ref/heads/main') or '/git/ref/tags/' in path:
                return {'object': {'type': 'commit', 'sha': 'a' * 40}}
            if '/releases/tags/' in path:
                return None
            return {}
        with patch.object(release, 'api', side_effect=api):
            release.publish()
        self.assertEqual([path for path, data in calls if data is not None],
                         ['repos/Chuppa/coffee-local/releases/generate-notes', 'repos/Chuppa/coffee-local/releases'])

    def test_release_notes_keep_real_dependency_pr_versions_and_author(self):
        def api(path,data=None,**kwargs):
            if path.endswith('/latest'):return {'tag_name':'v2026.10.1'}
            self.assertEqual(data['previous_tag_name'],'v2026.10.1')
            return {'body':"## What's Changed\n* Update aiohttp to v3.14.2 by @bot in https://github.com/example/app/pull/42"}
        with patch.object(release,'api',side_effect=api):
            notes=release.release_notes('repos/example/app','v2026.10.2','a'*40)
        self.assertIn('## ⬆️ Dependency updates',notes)
        self.assertIn('v3.14.2 by @bot',notes)
        self.assertIn('/pull/42',notes)

    def test_notes_service_failure_does_not_block_release_or_invent_details(self):
        with patch.object(release,'api',side_effect=[None,RuntimeError('unavailable')]):
            notes=release.release_notes('repos/example/app','v2026.10.2','a'*40)
        self.assertIn('/tree/'+'a'*40,notes)
        self.assertNotIn('Dependency updates',notes)

    def test_current_notes_sync_only_patches_release_body(self):
        calls=[]
        def api(path,data=None,**kwargs):
            calls.append((path,data,kwargs))
            if path.endswith('/latest'):return {'id':42,'tag_name':'v2026.10.1','body':'Old'}
            if path.endswith('/generate-notes'):return {'body':"## What's Changed\n* Update dependency to v2.0 by @bot in https://github.com/example/app/pull/42"}
            return {}
        with patch.object(release,'api',side_effect=api):release.sync_notes()
        edits=[(path,data,kwargs) for path,data,kwargs in calls if kwargs.get('method')=='PATCH']
        self.assertEqual(len(edits),1)
        self.assertEqual(edits[0][0],'repos/Chuppa/coffee-local/releases/42')
        self.assertEqual(set(edits[0][1]),{'body'})
        self.assertIn('Dependency updates',edits[0][1]['body'])

    def test_notes_sync_preserves_existing_description_on_optional_service_failure(self):
        with patch.object(release,'api',side_effect=[{'id':42,'tag_name':'v2026.10.1'},
                          {'tag_name':'v2026.10.1'},RuntimeError('unavailable')]) as api:
            release.sync_notes()
        self.assertEqual(api.call_count,3)

    def test_same_version_different_content_cannot_replace_a_tag(self):
        def api(path, data=None, **kwargs):
            return {'object': {'type': 'commit', 'sha': ('a' if path.endswith('/main') else 'b') * 40}}
        with patch.object(release, 'api', side_effect=api), \
             patch.object(release, 'scope', side_effect=[{'fixture': 'old'}, {'fixture': 'new'}]):
            with self.assertRaisesRegex(ValueError, 'immutable'):
                release.publish()


class SecurityTests(unittest.TestCase):
    def report(self, severity):
        return {'runs': [{'tool': {'driver': {'rules': [
            {'id': 'fixture', 'properties': {'security-severity': severity}}]}},
            'results': [{'ruleId': 'fixture'}]}]}

    def test_high_and_critical_block_publication(self):
        self.assertEqual(security.blocking(self.report('7.0')), 1)
        self.assertEqual(security.blocking(self.report('9.8')), 1)

    def test_malformed_analysis_cannot_pass_as_zero_findings(self):
        with self.assertRaisesRegex(ValueError, 'Missing CodeQL'):
            security.blocking({})

    def test_medium_findings_stay_in_reports_without_bypassing_high_gate(self):
        self.assertEqual(security.blocking(self.report('6.9')), 0)


if __name__ == '__main__':
    unittest.main()
