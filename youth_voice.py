"""Run using the installed Kokoro environment; cache complete scene narration."""
from pathlib import Path
import os,json,hashlib,sys
os.environ['OMP_NUM_THREADS']='6'
import soundfile as sf
from kokoro_onnx import Kokoro

def main():
    project=Path(sys.argv[1]);out=Path(sys.argv[2]);models=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
    k=Kokoro(str(models/'kokoro-v1.0.onnx'),str(models/'voices-v1.0.bin'))
    voice=.75*k.get_voice_style('am_fenrir')+.25*k.get_voice_style('am_michael')
    timing=[]
    for i,s in enumerate(json.loads(project.read_text(encoding='utf-8'))['scenes']):
        h=hashlib.sha256(s['narration'].encode()).hexdigest();p=out/f'{i:03}-{h[:12]}.wav'
        if not p.exists():
            a,rate=k.create(s['narration'],voice=voice,speed=1.0,lang='en-us');sf.write(p,a,rate)
        timing.append(dict(file=str(p),seconds=sf.info(p).duration,text_sha256=h))
        print('Voice',i+1,len(timing),flush=True)
    (out/'timing.json').write_text(json.dumps(timing,indent=2))

if __name__=='__main__':main()
