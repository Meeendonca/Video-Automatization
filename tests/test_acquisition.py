import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import acquisition as ac
import studio


class AcquisitionTests(unittest.TestCase):
    def test_noncommercial_and_unknown_licenses_rejected(self):
        for name in ('CC BY-NC 4.0', 'CC BY-ND 4.0', 'CC BY-SA 4.0', 'Fair use', ''):
            self.assertIsNone(ac.allowed_license({'LicenseShortName': {'value': name}}, True))
        self.assertEqual(ac.allowed_license({'LicenseShortName': {'value': 'CC0'}})[0], 'cc0')

    def test_attribution_requires_explicit_flag_and_license_url(self):
        meta = {'LicenseShortName': {'value': 'CC BY 4.0'},
                'LicenseUrl': {'value': 'https://creativecommons.org/licenses/by/4.0/'}}
        self.assertIsNone(ac.allowed_license(meta))
        self.assertEqual(ac.allowed_license(meta, True)[0], 'cc by 4.0')
        meta['LicenseUrl']['value'] = 'https://example.com'
        self.assertIsNone(ac.allowed_license(meta, True))

    def test_image_results_filter_license_and_declared_ai(self):
        def page(name, license_name):
            return {'title': name, 'imageinfo': [{'mime': 'image/jpeg', 'width': 1800, 'height': 1000,
                    'url': 'https://example.com/image.jpg', 'descriptionurl': 'https://example.com/license',
                    'extmetadata': {'LicenseShortName': {'value': license_name}}}]}
        payload = {'query': {'pages': {'1': page('File:Camera.jpg', 'CC0'),
                                      '2': page('File:AI-generated camera.jpg', 'CC0'),
                                      '3': page('File:Camera two.jpg', 'CC BY-NC 4.0')}}}
        with patch('acquisition.api', return_value=payload):
            found = ac.commons_images('Camera')
        self.assertEqual([r['title'] for r in found], ['File:Camera.jpg'])

    def test_network_rejects_private_and_credentials(self):
        with self.assertRaises(ValueError):
            ac.public_url('file:///etc/passwd')
        with self.assertRaises(ValueError):
            ac.public_url('https://user:password@example.com')
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('127.0.0.1', 443))]):
            with self.assertRaises(ValueError):
                ac.public_url('https://example.com')

    def test_rss_filters_topic_and_normalizes_date(self):
        xml = b'<rss><channel><item><title>GTA 6 report</title><link>https://example.com/gta</link><description>GTA 6 news</description><pubDate>Sat, 05 Sep 2026 10:00:00 GMT</pubDate></item><item><title>Other game</title><link>https://example.com/other</link></item></channel></rss>'
        result = ac.rss_items(xml, 'GTA 6')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['published_at'], '2026-09-05T10:00:00+00:00')

    def test_research_fallback_and_duplicate_do_not_claim_news(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'project.json'
            studio.new_project(path, 'gaming')
            item = {'url': 'https://en.wikipedia.org/wiki/Test', 'title': 'Test',
                    'text': 'Example context. ' * 25, 'source_type': 'encyclopedia', 'provider': 'wikipedia'}
            with patch('acquisition.wikipedia', return_value=[item, item]), \
                 patch('acquisition.gdelt', side_effect=ValueError('429')), \
                 patch('acquisition.fetch', side_effect=ValueError('offline')):
                report = ac.research(path, 'Test')
            self.assertEqual(len(report['added']), 1)
            self.assertEqual(report['news_found'], 0)
            self.assertEqual(report['added'][0]['verification'], 'unverified')
            self.assertTrue(report['errors'])

    def test_failed_research_preserves_project(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'project.json'
            studio.new_project(path, 'gaming')
            original = path.read_bytes()
            with patch('acquisition.wikipedia', side_effect=ValueError('offline')):
                with self.assertRaises(ValueError):
                    ac.research(path, 'Test', use_news=False)
            self.assertEqual(original, path.read_bytes())

    def test_multiple_shots_in_review_and_missing_rights(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            path = base / 'project.json'
            data = studio.read(studio.ROOT / 'examples/demo.json')
            data['ai_disclosure'] = 'no'
            (base / 'a.jpg').write_bytes(b'a')
            (base / 'b.jpg').write_bytes(b'b')
            data['scenes'][0]['visuals'] = [
                {'visual': name, 'asset_origin': 'own', 'asset_rights': 'own'} for name in ('a.jpg', 'b.jpg')]
            studio.write(path, data)
            studio.review_project(path, 'Tester')
            self.assertEqual(len(studio.read(path)['review']['assets']), 2)
            (base / 'b.jpg').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Material mudou'):
                studio.validate(studio.read(path), base, approved=True)

    def test_final_export_rejects_missing_photos_before_synthesis(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'project.json'
            data = studio.read(studio.ROOT / 'examples/demo.json')
            data['ai_disclosure'] = 'no'
            studio.write(path, data)
            studio.review_project(path, 'Tester')
            with patch('piper.PiperVoice.load') as voice:
                with self.assertRaisesRegex(ValueError, 'todas as cenas'):
                    studio.render(path, studio.VOICE)
                voice.assert_not_called()


if __name__ == '__main__':
    unittest.main()
