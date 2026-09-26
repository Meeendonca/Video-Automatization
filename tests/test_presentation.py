import tempfile
import unittest
import wave
from pathlib import Path
import numpy as np
from presentation import zoom_at, callout_plan, ambient_score


class PresentationTests(unittest.TestCase):
    def test_mixed_photo_video_overlay_preserves_every_frame(self):
        import studio, subprocess, re
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            Image.new('RGB', (320, 180), 'red').save(base/'red.png')
            studio.run([studio.ffmpeg(), '-y', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=c=blue:s=320x180:r=30', '-t', '2', '-c:v', 'libx264',
                        '-colorspace', 'bt470bg', base/'blue.mp4'])
            with wave.open(str(base/'audio.wav'), 'wb') as w:
                w.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
                w.writeframes(b'\x00\x00'*96000)
            scene = {'heading': 'Test', 'callouts': ['HELLO'],
                     'visuals': [{'visual': 'red.png'}, {'visual': 'blue.mp4'}]}
            result = studio.render_scene_visuals(scene, base, base, 0, (320,180), 4,
                                                 base/'audio.wav', 'gaming', True)
            decoded = subprocess.run([studio.ffmpeg(), '-hide_banner', '-i', str(result),
                                      '-map', '0:v', '-f', 'null', '-'], capture_output=True, text=True)
            self.assertEqual(decoded.returncode, 0, decoded.stderr)
            self.assertEqual(int(re.findall(r'frame=\s*(\d+)', decoded.stderr)[-1]), 120)

    def test_zoom_is_small_monotonic_and_smooth(self):
        values = np.array([zoom_at(i, 300) for i in range(300)])
        self.assertEqual(values[0], 1)
        self.assertAlmostEqual(values[-1], 1.08)
        self.assertTrue(np.all(np.diff(values) >= 0))
        self.assertLess(np.max(np.diff(values)), .0005)

    def test_callouts_fit_scene_and_leave_reading_time(self):
        plan = callout_plan({'heading': 'Heading', 'callouts': ['First', 'Second']}, 8)
        self.assertEqual(len(plan), 2)
        self.assertTrue(all(0 <= p['start'] < p['end'] < 8 for p in plan))
        self.assertLess(plan[0]['end'], plan[1]['start'])
        self.assertEqual(callout_plan({'callouts': []}, 8), [])
        with self.assertRaises(ValueError):
            callout_plan({'callouts': ['x'*65]}, 8)

    def test_original_music_has_correct_length_and_no_clipping(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'music.wav'
            ambient_score(path, 10)
            with wave.open(str(path)) as stream:
                self.assertEqual(stream.getnframes(), 240000)
                self.assertEqual(stream.getnchannels(), 2)
                samples = np.frombuffer(stream.readframes(240000), dtype='<i2') / 32768
            self.assertGreater(np.sqrt(np.mean(samples*samples)), .01)
            self.assertLess(np.max(np.abs(samples)), .9)
            self.assertLess(np.max(np.abs(np.diff(samples.reshape(-1, 2), axis=0))), .05)
