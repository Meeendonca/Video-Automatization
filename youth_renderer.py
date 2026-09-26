"""Video-first renderer: natural 8-15 minute episodes or explicit short prototypes.

Shots have visual, start, seconds (relative timing weight), optional crop,
asset_origin and asset_rights. No looping, corner credits, SRT or thumbnails.
"""
from pathlib import Path
import json,math,re,sys,subprocess
import studio,presentation

VIDEO={'.mp4','.mov','.mkv'}

def shot_plan(scene,frames,base):
    shots=studio.scene_assets(scene)
    if not shots:raise ValueError('Add relevant video footage before rendering.')
    weights=[float(s.get('seconds',4)) for s in shots]
    if any(w<=0 for w in weights):raise ValueError('Shot seconds must be positive.')
    bounds=[round(sum(weights[:i])/sum(weights)*frames) for i in range(len(shots)+1)]
    result=[]
    for i,s in enumerate(shots):
        p=studio.local_asset(base,s['visual']);n=bounds[i+1]-bounds[i]
        if n<1:raise ValueError('Shot shorter than a frame.')
        if not s.get('asset_origin') or not s.get('asset_rights'):raise ValueError('Footage needs recorded origin and rights.')
        if float(s.get('start',0))<0:raise ValueError('Negative source start.')
        result.append((s,p,n))
    return result

def validate_timeline(data,timing,base,preview=False):
    frames=[math.ceil(t['seconds']*30) for t in timing]
    tempo=1.0
    if preview and data.get('preview_seconds'):
        target=float(data['preview_seconds'])
        natural=sum(t['seconds'] for t in timing)
        tempo=natural/(target-1)
        if not .85<=tempo<=1.15:raise ValueError('Revise prototype narration to fit naturally; do not truncate it.')
        bounds=[round(sum(t['seconds'] for t in timing[:i])/natural*(target-1)*30) for i in range(len(timing)+1)]
        frames=[bounds[i+1]-bounds[i] for i in range(len(timing))];frames[-1]+=30
    else:frames[-1]+=45
    duration=sum(frames)/30
    if not preview and not 480<=duration<=900:
        raise ValueError(f'Narration lasts {duration:.1f}s. Edit script to 8-15 minutes; never pad to ten minutes or cut speech.')
    plans=[shot_plan(s,n,base) for s,n in zip(data['scenes'],frames)]
    moving=sum(n for plan in plans for _,p,n in plan if p.suffix.lower() in VIDEO)
    share=moving/sum(frames)
    if share<.8:raise ValueError(f'Only {share:.0%} moving footage: add video to reach 80% of screen time.')
    absolute=[];offset=0
    for scene,n in zip(data['scenes'],frames):
        for c in presentation.callout_plan(scene,n/30):absolute.append((offset+c['start'],offset+c['end']))
        offset+=n/30
    if any(b[0]-a[0]<10 for a,b in zip(absolute,absolute[1:])):
        raise ValueError('Space meaningful callouts at least ten seconds apart.')
    if sum(b-a for a,b in absolute)>duration*.18:
        raise ValueError('Callouts occupy too much of the video; keep under 18%.')
    return frames,tempo,plans,share

def render(project,preview=False):
    project=Path(project).resolve();base=project.parent;data=studio.read(project)
    studio.validate(data,base,approved=False)
    if any(not studio.scene_assets(s) for s in data['scenes']):
        raise ValueError('Exportação exige vídeos/imagens em todas as cenas antes de gerar voz.')
    out=base/'renders/youth-v1';out.mkdir(parents=True,exist_ok=True)
    repo=studio.ROOT.parents[1];models=repo/'work/voice-audition'
    python=models/'.venv/Scripts/python.exe'
    studio.run([python,studio.ROOT/'youth_voice.py',project,out/'audio',models])
    timing=studio.read(out/'audio/timing.json')
    frames,tempo,plans,share=validate_timeline(data,timing,base,preview)
    segments=[];asset_records=[];timeline=[];offset=0
    for i,(scene,plan,n,t) in enumerate(zip(data['scenes'],plans,frames,timing)):
        duration=n/30;parts=[]
        print(f'Rendering video-first scene {i+1}/{len(plans)}',flush=True)
        for j,(shot,source,count) in enumerate(plan):
            dest=out/f'shot-{i:03}-{j:02}.mp4'
            if source.suffix.lower() in VIDEO:
                filters=[]
                if shot.get('crop'):
                    crop=shot['crop']
                    if len(crop)!=4 or any(not isinstance(v,int) or v<0 for v in crop):raise ValueError('crop must be [width,height,x,y] integers')
                    filters.append('crop='+':'.join(map(str,crop)))
                filters+=['scale=1920:1080:force_original_aspect_ratio=increase','crop=1920:1080','setsar=1','fps=30','setpts=PTS-STARTPTS']
                studio.run([studio.ffmpeg(),'-y','-v','error','-ss',str(shot.get('start',0)),'-i',source,'-an','-vf',','.join(filters),'-frames:v',str(count),'-c:v','h264_nvenc','-preset','p4','-cq','20','-pix_fmt','yuv420p',dest])
            else:
                from PIL import Image,ImageOps
                photo=out/f'photo-{i:03}-{j:02}.jpg'
                ImageOps.fit(Image.open(source).convert('RGB'),(1920,1080)).save(photo)
                presentation.encode_photo(photo,dest,count,(1920,1080),.06)
            # Short sources must fail rather than freeze or silently loop.
            check=studio.run([studio.ffmpeg(),'-hide_banner','-xerror','-i',dest,'-map','0:v','-f','null','-'])
            actual=int(re.findall(r'frame=\s*(\d+)',check.stderr)[-1])
            if actual!=count:raise ValueError(f'{source.name}: {actual}/{count} frames; choose a longer source range.')
            parts.append(dest);asset_records.append(dict(file=str(source),start=shot.get('start',0),frames=count,origin=shot['asset_origin'],rights=shot['asset_rights']))
        manifest=out/f'concat-{i:03}.txt';manifest.write_text(''.join(f"file '{p.as_posix()}'\nduration {shot[2]/30:.9f}\n" for p,shot in zip(parts,plan)))
        segment=out/f'scene-{i:03}.mp4'
        studio.run([studio.ffmpeg(),'-y','-v','error','-reinit_filter','0','-f','concat','-safe','0','-i',manifest,'-i',t['file'],'-map','0:v','-map','1:a',
                    '-vf','setpts=PTS-STARTPTS,fps=30,tpad=stop_mode=clone:stop=3','-frames:v',str(n),'-c:v','h264_nvenc','-preset','p4','-cq','20','-af',f'highpass=f=75,lowpass=f=10500,atempo={tempo},loudnorm=I=-19:TP=-3:LRA=7,apad','-ar','48000','-ac','2','-c:a','aac','-t',str(duration),segment])
        segments.append(presentation.decorate_segment(segment,scene,duration,(1920,1080),'gaming'))
        timeline.append(dict(start=offset,end=offset+duration,heading=scene['heading']));offset+=duration
    manifest=out/'concat.txt';manifest.write_text(''.join(f"file '{p.as_posix()}'\n" for p in segments))
    joined=out/'joined.mp4'
    studio.run([studio.ffmpeg(),'-y','-v','error','-f','concat','-safe','0','-i',manifest,'-map','0:v','-map','0:a','-c','copy',joined])
    final=out/('prototype.mp4' if preview else 'video.mp4')
    mixed=out/'mixed.mp4'
    music=presentation.add_music(joined,mixed,offset,float(data.get('music',{}).get('gain_db',-10)),style='trap')
    # Reset codec/mux offsets so the delivery duration includes no AAC lead-in.
    studio.run([studio.ffmpeg(),'-y','-v','error','-i',mixed,'-map','0:v:0','-map','0:a:0',
                '-vf','setpts=PTS-STARTPTS,fps=30','-af','asetpts=PTS-STARTPTS',
                '-c:v','h264_nvenc','-preset','p4','-cq','20','-pix_fmt','yuv420p',
                '-c:a','aac','-b:a','192k','-t',str(offset),'-movflags','+faststart',final])
    check=studio.run([studio.ffmpeg(),'-hide_banner','-xerror','-i',final,'-map','0:v','-map','0:a','-af','volumedetect','-f','null','-'])
    count=int(re.findall(r'frame=\s*(\d+)',check.stderr)[-1]);duration=studio.probe(final)
    if count!=sum(frames) or abs(duration-offset)>.05:raise ValueError('Final duration/frame mismatch')
    studio.write(out/'verification.json',dict(seconds=duration,frames=count,resolution='1920x1080',video_share=share,decode_passed=True,music=music,voice_tempo=tempo,corner_labels=False,subtitles=False,thumbnail=False,description=False,sha256=studio.file_hash(final),audio_levels=[s.strip() for s in check.stderr.splitlines() if 'mean_volume' in s or 'max_volume' in s]))
    studio.write(out/'provenance.json',asset_records);studio.write(out/'timeline.json',timeline)
    print('COMPLETE',final,flush=True)
    return final

if __name__=='__main__':
    render(Path(sys.argv[1]),preview='--preview' in sys.argv[2:])
