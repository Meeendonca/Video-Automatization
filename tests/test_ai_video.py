import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ai_images
import studio
import video_assets


class NewMediaTests(unittest.TestCase):
    def test_video_relevance_requires_subject_not_search_template(self):
        self.assertTrue(video_assets.related('pulping machines', 'Pulping machines in a museum', 'Papermaking'))
        self.assertFalse(video_assets.related('camera manufacturing', 'Vacuum cleaner', 'A cleaner in use'))
        self.assertFalse(video_assets.related('Miami skyline', 'Miami sheriff interview', 'A police interview'))

    def test_ogg_video_allowed_and_noncommercial_filtered(self):
        def page(license_name):
            return {'title': 'File:Pulping machines.ogv', 'videoinfo': [{
                'mime': 'application/ogg', 'duration': 12, 'width': 1280, 'height': 720, 'size': 2500000,
                'url': 'https://example.com/video.ogv', 'descriptionurl': 'https://example.com/license',
                'extmetadata': {'LicenseShortName': {'value': license_name},
                                'ImageDescription': {'value': 'Pulping machines'}}}]}
        with patch('video_assets.api', return_value={'query': {'pages': {'1': page('CC0'), '2': page('CC BY-NC 4.0')}}}):
            self.assertEqual(len(video_assets.commons_videos('pulping machines')), 1)

    def test_prompt_requires_concrete_input(self):
        with self.assertRaises(ValueError):
            ai_images.build_prompt({})
        result = ai_images.build_prompt({'image_prompt': 'A camera on a wooden desk'})
        self.assertIn('A camera on a wooden desk', result)
        self.assertIn('No text or logos', result)

    def test_missing_model_gives_setup_instructions(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'project.json'
            studio.new_project(path, 'gaming')
            with patch('ai_images.MODEL_DIR', Path(temp) / 'missing'):
                with self.assertRaisesRegex(ValueError, 'setup-ai.ps1'):
                    ai_images.generate(path)

    def test_synthetic_image_cannot_be_exported_as_non_ai(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'project.json'
            data = studio.read(studio.ROOT / 'examples/demo.json')
            data['ai_disclosure'] = 'no'
            image = path.parent / 'ai.png'
            image.write_bytes(b'test')
            data['scenes'][0]['visuals'] = [{'visual': 'ai.png', 'asset_origin': 'local',
                                            'asset_rights': 'generated', 'synthetic': True}]
            studio.write(path, data)
            studio.review_project(path, 'test')
            with self.assertRaisesRegex(ValueError, 'ai_disclosure=yes'):
                studio.validate(studio.read(path), path.parent, approved=True)

    def test_photograph_uses_subpixel_motion_without_zoompan(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            Image.new('RGB', (960, 540), '#224466').save(base / 'photo.png')
            scene = {'visual': 'photo.png', 'heading': 'Test'}
            with patch('studio.run') as run, patch('presentation.encode_photo') as encode, patch('presentation.decorate_segment'):
                studio.render_scene_visuals(scene, base, base, 0, (1280, 720), 1.0,
                                             base / 'test.wav', 'gaming', True)
            calls = [' '.join(map(str, c.args[0])) for c in run.call_args_list]
            self.assertEqual(encode.call_args.args[-1], .08)
            self.assertFalse(any('zoompan' in c for c in calls))


if __name__ == '__main__':
    unittest.main()
