"""License-filtered public-domain/CC0 footage from Wikimedia Commons."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import urllib.request

from acquisition import api, COMMONS, allowed_license, clean, tokens, public_url, PublicRedirect, USER_AGENT


def related(query, title, description):
    wanted = tokens(query) - {'video', 'footage', 'clip', 'b', 'roll'}
    # Match the actual title/description, not license templates or the whole search page.
    actual = tokens(title + ' ' + description)
    return bool(wanted) and wanted <= actual


def commons_videos(query, attribution=False, limit=8):
    result = api(COMMONS, {'action': 'query', 'generator': 'search', 'gsrsearch': query + ' filetype:video',
                          'gsrnamespace': 6, 'gsrlimit': 50, 'prop': 'videoinfo',
                          'viprop': 'url|size|mime|extmetadata|derivatives', 'format': 'json'})
    found = []
    pages = sorted(result.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
    for page in pages:
        info = page.get('videoinfo', [{}])[0]
        meta = info.get('extmetadata', {})
        license_info = allowed_license(meta, attribution)
        description = clean(meta.get('ImageDescription', {}).get('value', ''))
        if not license_info or not related(query, page['title'], description):
            continue
        if info.get('duration', 0) < 4 or not (info.get('mime', '').startswith('video/') or
                                              info.get('mime') == 'application/ogg'):
            continue
        choices = [{'src': info['url'], 'width': info.get('width', 0), 'height': info.get('height', 0)}]
        if info.get('size', 0) > 120_000_000:
            choices = info.get('derivatives', [])
        choices = [d for d in choices if d.get('width', 0) >= 854 and d.get('height', 0) >= 480
                   and d['width'] / d['height'] >= 1.3]
        if not choices:
            continue
        selected = min(choices, key=lambda d: abs(d['height'] - 720))
        found.append({'url': selected['src'], 'origin': info['descriptionurl'], 'title': page['title'],
                      'description': description[:800], 'duration': info['duration'],
                      'creator': clean(meta.get('Artist', {}).get('value', 'See source')),
                      'license': license_info[0], 'license_url': license_info[1], 'license_evidence': meta})
        if len(found) >= limit:
            break
    return found


def download_video(item, target, seconds=12):
    import studio
    public_url(item['url'])
    request = urllib.request.Request(item['url'], headers={'User-Agent': USER_AGENT, 'Accept-Encoding': 'identity'})
    source = target.with_suffix('.download')
    with urllib.request.build_opener(PublicRedirect()).open(request, timeout=30) as response, source.open('wb') as out:
        size = 0
        while block := response.read(1024 * 1024):
            size += len(block)
            if size > 120_000_000:
                raise ValueError('Vídeo excedeu o limite de 120 MB.')
            out.write(block)
    pending = target.with_name(target.stem + '-pending.mp4')
    studio.run([studio.ffmpeg(), '-y', '-v', 'error', '-i', source, '-t', str(seconds), '-map', '0:v:0',
                '-an', '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', pending])
    studio.run([studio.ffmpeg(), '-v', 'error', '-xerror', '-i', pending, '-map', '0:v:0', '-f', 'null', '-'])
    pending.replace(target)
    # Delete only this exact intermediate generated within the episode assets folder.
    source.unlink()


def videos(path, attribution=False, per_scene=4, selected_scene=None):
    import studio
    data = studio.read(path)
    if selected_scene is not None and not 1 <= selected_scene <= len(data['scenes']):
        raise ValueError('Número de cena inválido.')
    assets = path.parent / 'assets'
    assets.mkdir(exist_ok=True)
    report = {'downloaded': [], 'errors': [], 'time': datetime.now(timezone.utc).isoformat()}
    used = {s.get('asset_origin') for scene in data['scenes'] for s in studio.scene_assets(scene)}
    for index, scene in enumerate(data['scenes'], 1):
        if selected_scene is not None and index != selected_scene:
            continue
        shots = [dict(s) for s in studio.scene_assets(scene)]
        moving = [s for s in shots if s.get('media_kind') == 'video' or Path(s.get('visual', '')).suffix.lower() in ('.mp4', '.mov', '.mkv')]
        if len(moving) >= per_scene:
            continue
        stills = [s for s in shots if s not in moving]
        shots = moving + stills[:1]
        query = scene.get('video_query') or scene.get('visual_query')
        if not query:
            report['errors'].append({'scene': index, 'error': 'Falta video_query ou visual_query.'})
            continue
        print(f'Cena {index}: buscando clipes de {query}...', flush=True)
        try:
            candidates = commons_videos(query, attribution)
        except Exception as exc:
            report['errors'].append({'scene': index, 'error': str(exc)})
            continue
        count = len(moving)
        for candidate in candidates:
            if count >= per_scene or len(shots) >= 8:
                break
            if candidate['origin'] in used:
                continue
            digest = hashlib.sha256(candidate['origin'].encode()).hexdigest()[:12]
            target = assets / f'clip-{digest}-{datetime.now().strftime("%H%M%S%f")}.mp4'
            try:
                download_video(candidate, target)
                record = {**candidate, 'file': target.relative_to(path.parent).as_posix(),
                          'sha256': studio.file_hash(target), 'downloaded_at': report['time'],
                          'changes': 'First 12 seconds maximum; original audio removed; resized to 720p.',
                          'relevance': 'keyword match; review the actual footage before publication'}
                studio.write(target.with_suffix('.license.json'), record)
                shots.append({'visual': record['file'], 'asset_origin': candidate['origin'],
                              'asset_rights': candidate['license'], 'creator': candidate['creator'],
                              'license_url': candidate['license_url'], 'asset_title': candidate['title'],
                              'media_kind': 'video', 'visual_context': candidate['description']})
                used.add(candidate['origin'])
                report['downloaded'].append(record)
                count += 1
            except Exception as exc:
                report['errors'].append({'scene': index, 'error': str(exc), 'url': candidate['origin']})
        if count:
            scene['visuals'] = shots
            scene.pop('visual', None)
            data.pop('review', None)
            studio.write(path, data)
        elif len(shots) < 8:
            report['errors'].append({'scene': index, 'error': 'Sem clipe relacionado com licença permitida. Fotos existentes preservadas.'})
    studio.write(path.with_name(path.stem + '-videos.json'), report)
    print(f'{len(report["downloaded"])} clipes adicionados.')
    for error in report['errors']:
        print(f'Aviso cena {error["scene"]}: {error["error"]}')
    if report['errors'] and not report['downloaded']:
        raise ValueError('Nenhum clipe obtido; consulte o relatório -videos.json.')
    return report
