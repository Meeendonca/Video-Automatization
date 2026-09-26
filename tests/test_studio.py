import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import studio


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = studio.read(studio.ROOT / 'examples/demo.json')
        self.data['ai_disclosure'] = 'no'
        self.base = studio.ROOT / 'examples'

    def test_fact_requires_source(self):
        self.data['scenes'][0]['claim_type'] = 'fact'
        with self.assertRaisesRegex(ValueError, 'precisam de fontes'):
            studio.validate(self.data, self.base)

    def test_stale_review_rejected(self):
        self.data['review'] = {'fingerprint': studio.fingerprint(self.data)}
        studio.validate(self.data, self.base, approved=True)
        self.data['scenes'][0]['narration'] += ' Changed.'
        with self.assertRaisesRegex(ValueError, 'desatualizada'):
            studio.validate(self.data, self.base, approved=True)

    def test_material_path_cannot_escape(self):
        with self.assertRaisesRegex(ValueError, 'dentro da pasta'):
            studio.local_asset(self.base, '../studio.py')

    def test_asset_change_invalidates_review(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            asset = base / 'image.png'
            asset.write_bytes(b'first')
            scene = self.data['scenes'][0]
            scene.update(visual='image.png', asset_origin='test', asset_rights='own')
            project = base / 'project.json'
            studio.write(project, self.data)
            studio.review_project(project, 'tester')
            asset.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Material mudou'):
                studio.validate(studio.read(project), base, approved=True)

    def test_unknown_source_rejected(self):
        self.data['scenes'][0]['source_ids'] = ['missing']
        with self.assertRaisesRegex(ValueError, 'referência inexistente'):
            studio.validate(self.data, self.base)

    def test_timestamp_carry_and_caption_text(self):
        self.assertEqual(studio.stamp(59.9999), '00:01:00,000')
        text = 'One sentence. ' + 'This is another sentence with several words. ' * 8
        self.assertEqual(' '.join(studio.phrases(text)), ' '.join(text.split()))

    def test_invalid_generated_draft_does_not_replace_project(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'project.json'
            self.data['sources'] = [{'id': 's1', 'url': 'https://example.com',
                                     'notes': 'A verified note.', 'accessed_at': '2026-09-05'}]
            studio.write(path, self.data)
            before = path.read_bytes()
            generated = {'response': json.dumps({'title': 'Test', 'description': 'Test',
                'scenes': [{'heading': 'Test', 'narration': 'Test', 'claim_type': 'fact', 'source_ids': ['fake'], 'visual_query': 'camera'}]})}
            import io
            with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(generated).encode())):
                with self.assertRaises(ValueError):
                    studio.draft(path, 'Test', 'test', 1)
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(path.with_name('project-draft.json').exists())

    def test_overlong_audio_fails_before_encoding(self):
        self.data['production_style'] = 'legacy'
        class LongVoice:
            def synthesize_wav(self, text, stream, **kwargs):
                stream.setparams((1, 2, 1, 0, 'NONE', 'not compressed'))
                stream.writeframes(b'\0\0' * 600)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'project.json'
            studio.write(path, self.data)
            with patch('piper.PiperVoice.load', return_value=LongVoice()), patch('studio.run') as runner:
                with self.assertRaisesRegex(ValueError, '599s'):
                    studio.render(path, studio.VOICE, preview=True)
                runner.assert_not_called()
            status = studio.read(next((path.parent / 'renders').glob('*/status.json')))
            self.assertEqual(status['status'], 'failed')
            self.assertFalse(list(path.parent.rglob('preview.mp4')))


if __name__ == '__main__':
    unittest.main()
