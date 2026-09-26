import tempfile,unittest,wave
from pathlib import Path
import numpy as np
import youth_renderer as y
from trap_score import create_score
from presentation import callout_plan

class YouthTests(unittest.TestCase):
    def test_natural_duration_and_video_share_by_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp);(b/'a.mp4').touch();(b/'b.jpg').touch()
            shots=[dict(visual=p,seconds=n,asset_origin='source',asset_rights='licensed') for p,n in [('a.mp4',4),('b.jpg',1)]]
            d={'scenes':[{'visuals':shots,'callouts':[]}]}
            frames,tempo,_,share=y.validate_timeline(d,[{'seconds':510}],b)
            self.assertEqual(sum(frames)/30,511.5);self.assertEqual(tempo,1);self.assertAlmostEqual(share,.8,places=3)
            shots[1]['seconds']=4
            with self.assertRaisesRegex(ValueError,'80%'):y.validate_timeline(d,[{'seconds':510}],b)
            with self.assertRaisesRegex(ValueError,'8-15'):y.validate_timeline(d,[{'seconds':901}],b)
            with self.assertRaisesRegex(ValueError,'8-15'):y.validate_timeline(d,[{'seconds':300}],b)

    def test_sparse_explicit_callouts(self):
        self.assertEqual(callout_plan({'heading':'Do not display by default'},30),[])
        p=callout_plan({'callouts':[{'text':'A REAL POINT','start':18,'duration':2}]},30)
        self.assertEqual(p[0]['start'],18);self.assertEqual(p[0]['end'],20)

    def test_trap_signal_duration_dynamic_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'trap.wav';create_score(p,10)
            with wave.open(str(p)) as w:
                self.assertEqual(w.getnframes(),240000);self.assertEqual(w.getnchannels(),2)
                a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')/32768
            self.assertGreater(np.sqrt(np.mean(a*a)),.025)
            self.assertLess(abs(a).max(),.85)
            energy=np.sqrt((a.reshape(-1,4800)**2).mean(axis=1))
            self.assertGreater(energy.max()/np.median(energy),1.3)
