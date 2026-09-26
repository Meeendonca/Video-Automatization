"""Gentle subpixel camera motion, short animated callouts, original ambient score."""
import math
from pathlib import Path
import subprocess
import wave


def zoom_at(frame, count, amount=0.08):
    t = frame / max(1, count - 1)
    return 1 + amount * t * t * (3 - 2 * t)


def photo_frame(image, frame, count, amount):
    from PIL import Image
    scale = 1 / zoom_at(frame, count, amount)
    # Float coordinates and bicubic interpolation avoid integer crop-position jumps.
    return image.transform(image.size, Image.Transform.AFFINE,
                           (scale, 0, image.width * (1-scale)/2,
                            0, scale, image.height * (1-scale)/2), Image.Resampling.BICUBIC)


def encode_photo(image_path, target, frames, size, amount=0.08):
    import studio
    from PIL import Image
    if not 0 <= amount <= .12:
        raise ValueError('photo_zoom deve estar entre 0 e 0.12 (até 12%).')
    args = [studio.ffmpeg(), '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', f'{size[0]}x{size[1]}', '-r', '30', '-i', 'pipe:0', '-an',
            '-vf', 'setsar=1', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', str(target)]
    with Image.open(image_path) as source:
        source = source.convert('RGB')
        log_path = target.with_suffix('.encoder.log')
        with log_path.open('w+b') as log:
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
            try:
                for index in range(frames):
                    process.stdin.write(photo_frame(source, index, frames, amount).tobytes())
                process.stdin.close()
                code = process.wait()
            except BaseException:
                process.kill()
                process.wait()
                raise
            if code:
                log.seek(0)
                raise ValueError(log.read().decode('utf-8', 'replace')[-3000:])


def callout_plan(scene, duration):
    raw = scene.get('callouts', [])
    if not isinstance(raw, list) or len(raw) > 5:
        raise ValueError('callouts deve ser uma lista de até cinco textos.')
    plan = []
    for i, entry in enumerate(raw):
        text = entry.get('text') if isinstance(entry, dict) else entry
        if not isinstance(text, str) or not text.strip() or len(text) > 64:
            raise ValueError('Cada callout deve ter 1–64 caracteres.')
        start = float(entry.get('start', .45)) if isinstance(entry, dict) else .45 + i * duration / max(1, len(raw))
        if start < 0 or start >= duration:
            raise ValueError('Callout fora da duração da cena.')
        end = min(start + 2.3, duration - .12,
                  .45 + (i+1) * duration / max(1, len(raw)) - .2)
        if isinstance(entry, dict):
            end = min(start + float(entry.get('duration', 2.3)), duration - .12)
        if end-start >= .6:
            plan.append({'text': text, 'start': start, 'end': end})
    return plan


def decorate_segment(segment, scene, duration, size, channel):
    import studio
    from PIL import Image, ImageDraw
    import textwrap
    plan = callout_plan(scene, duration)
    if not plan:
        return segment
    inputs = []
    filters = ['[0:v]setpts=PTS-STARTPTS[v0]']
    layer = 0
    for i, item in enumerate(plan):
        # Large outlined typography, staggered word reveals, no presentation box.
        from PIL import ImageFont
        words = item['text'].upper().split()
        font_path = Path('C:/Windows/Fonts/impact.ttf')
        font_size = round(size[1] * .095)
        def face_at(n):
            return ImageFont.truetype(str(font_path), n) if font_path.exists() else studio.font(n)
        face = face_at(font_size)
        max_width = size[0] * .84
        lines, line = [], []
        for word in words:
            if line and face.getlength(' '.join(line + [word])) > max_width:
                lines.append(line)
                line = []
            line.append(word)
        if line:
            lines.append(line)
        while max(face.getlength(' '.join(row)) for row in lines) > max_width:
            font_size -= 2
            face = face_at(font_size)
        line_height = font_size * 1.15
        base_y = min(size[1] * .64, size[1] * .87 - line_height * len(lines))
        word_index = 0
        for row_index, row in enumerate(lines):
            x = (size[0] - face.getlength(' '.join(row))) / 2
            for word in row:
                image = Image.new('RGBA', size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(image)
                y = base_y + row_index * line_height
                accent = '#b5ff38' if channel == 'gaming' else '#51efff'
                color = accent if word_index == len(words)-1 else 'white'
                stroke = max(2, round(size[1]*.006))
                draw.text((x+4,y+7), word, font=face, fill=(0,0,0,150), stroke_width=stroke, stroke_fill=(0,0,0,150))
                draw.text((x,y), word, font=face, fill=color, stroke_width=stroke, stroke_fill='#121420')
                png = segment.with_name(segment.stem + f'-callout-{i}-{word_index}.png')
                image.save(png)
                inputs.extend(['-loop', '1', '-framerate', '30', '-i', png])
                start = item['start'] + min(word_index*.085, (item['end']-item['start'])*.25)
                end = item['end']
                filters.append(f'[{layer+1}:v]format=rgba,fade=t=in:st={start}:d=0.06:alpha=1,'
                               f'fade=t=out:st={end-.15}:d=0.15:alpha=1[o{layer}]')
                # One fast upward entrance with a small settling overshoot, no sustained shake.
                age = f'(t-{start})'
                movement = f'if(lt({age},0.18),42*(1-{age}/0.18)*(1-{age}/0.18),if(lt({age},0.3),-4*sin(({age}-0.18)/0.12*PI),0))'
                filters.append(f"[v{layer}][o{layer}]overlay=x=0:y='{movement}':"
                               f"enable='between(t,{start},{end})':shortest=1[v{layer+1}]")
                layer += 1
                word_index += 1
                x += face.getlength(word+' ')
    target = segment.with_name(segment.stem + '-styled.mp4')
    # Geometry/pixel format are normalized upstream. Source color metadata can
    # still change between photo and stock shots; restarting the graph would
    # reset setpts and discard the preceding shot when timestamps overlap.
    studio.run([studio.ffmpeg(), '-y', '-v', 'error', '-reinit_filter', '0', '-i', segment, *inputs,
                '-filter_complex', ';'.join(filters), '-map', f'[v{layer}]', '-map', '0:a:0',
                '-t', f'{duration:.6f}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                '-pix_fmt', 'yuv420p', '-c:a', 'copy', target])
    return target


def ambient_score(path, duration):
    """Synthesized original harmonic pad/arpeggio; no recordings or third-party samples."""
    import numpy as np
    rate = 24000
    chords = [(48,55,59,64), (45,52,55,60), (41,48,52,57), (43,50,55,59)]
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
        total = math.ceil(duration * rate)
        for offset in range(0, total, rate):
            t = np.arange(offset, min(offset+rate,total))/rate
            stereo = np.zeros((len(t),2), dtype=np.float64)
            # Overlapping 9-second pads, one new chord every 8 seconds.
            first = max(0, int(t[0]//8)-1)
            for chord_index in range(first, int(t[-1]//8)+1):
                local = t-chord_index*8
                envelope = np.clip(local/1.8,0,1) * np.clip((9-local)/2,0,1)
                for note_index,note in enumerate(chords[chord_index % len(chords)]):
                    freq = 440*2**((note-69)/12)
                    for side in range(2):
                        phase = 2*np.pi*freq*(1+(side*2-1)*.0007)*local
                        stereo[:,side] += envelope*(np.sin(phase)+.15*np.sin(2*phase))*.032
            # Sparse, rounded upper notes; no drums or sharp transients.
            for beat in range(max(0,int(t[0]/2)-2), int(t[-1]/2)+1):
                age = t-beat*2
                note = chords[(beat//4)%4][beat%4]+12
                freq = 440*2**((note-69)/12)
                env = np.where(age>=0, np.minimum(np.maximum(age,0)/.12,1)*np.exp(-np.maximum(age,0)/1.4),0)
                tone = np.sin(2*np.pi*freq*age)*env*.035
                stereo += tone[:,None]
            fade = np.minimum(t/2,1)*np.clip((duration-t)/3,0,1)
            stream.writeframes((np.clip(stereo*fade[:,None],-.9,.9)*32767).astype('<i2').tobytes())


def add_music(video, target, duration, db=-12, style='trap'):
    import studio
    if not -24 <= db <= -8:
        raise ValueError('music.gain_db deve estar entre -24 e -8 dB.')
    if style not in ('trap', 'ambient'):
        raise ValueError('Music style must be trap or ambient.')
    track = target.with_name('original-' + style + '.wav')
    if style == 'trap':
        from trap_score import create_score
        create_score(track, duration)
    else:
        ambient_score(track, duration)
    # Normalize music before setting level, then duck it further under narration.
    graph = (f'[0:a]asplit=2[voice][key];[1:a]loudnorm=I=-18:TP=-3:LRA=7,volume={db}dB[m];'
             '[m][key]sidechaincompress=threshold=0.02:ratio=5:attack=30:release=700[bed];'
             '[voice][bed]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95:level=0[a]')
    studio.run([studio.ffmpeg(), '-y', '-v', 'error', '-i', video, '-i', track,
                '-filter_complex', graph, '-map', '0:v:0', '-map', '[a]', '-map', '0:s?',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-c:s', 'copy',
                '-t', str(duration), '-movflags', '+faststart', target])
    return {'title': 'Midnight Pursuit' if style == 'trap' else 'Quiet Workshop', 'style': style, 'origin': 'Original algorithmic composition generated locally',
            'third_party_samples': False, 'music_gain_db': db, 'ducking': True,
            'note': 'No third-party recordings used; not a guarantee against automated Content ID errors.'}
