"""Public-source research and licensed photographs. No paid keys required."""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import html
import io
import ipaddress
import json
from pathlib import Path
import re
import socket
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

USER_AGENT = 'LocalVideoStudio/0.2 (personal documentary research; Python urllib)'
COMMONS = 'https://commons.wikimedia.org/w/api.php'
WIKIPEDIA = 'https://en.wikipedia.org/w/api.php'
FEEDS = {'gaming': ['https://www.pcgamer.com/rss/', 'https://www.gamesradar.com/rss/'],
         'company_stories': ['https://feeds.bbci.co.uk/news/business/rss.xml']}


def public_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Somente URLs públicas HTTP(S), sem credenciais.')
    if parsed.port not in (None, 80, 443):
        raise ValueError('Porta não permitida.')
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Endereço local ou privado não permitido na pesquisa.')
    return url


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, limit=4_000_000, timeout=20):
    public_url(url)
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept-Encoding': 'identity'})
    with urllib.request.build_opener(PublicRedirect()).open(request, timeout=timeout) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Resposta excedeu o limite de tamanho.')
        return data, response.geturl()


def api(url, params):
    raw, _ = fetch(url + '?' + urllib.parse.urlencode(params))
    data = json.loads(raw)
    if isinstance(data, dict) and data.get('error'):
        raise ValueError(str(data['error']))
    return data


def clean(text):
    return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', str(text))).split())


def tokens(text):
    stop = {'the', 'and', 'for', 'with', 'from', 'about', 'history', 'company', 'latest', 'news'}
    return set(re.findall(r'[a-z0-9]+', text.lower())) - stop


def canonical(url):
    parsed = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parsed.query)
             if not k.startswith('utm_') and k not in ('fbclid', 'gclid')]
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path,
                                    urllib.parse.urlencode(query), ''))


def wikipedia(query, limit):
    result = api(WIKIPEDIA, {'action': 'query', 'generator': 'search', 'gsrsearch': query,
                            'gsrnamespace': 0, 'gsrlimit': min(limit, 4), 'prop': 'extracts|info',
                            'exintro': 1, 'explaintext': 1, 'inprop': 'url', 'format': 'json'})
    pages = sorted(result.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
    return [{'url': p['fullurl'], 'title': p['title'], 'text': p.get('extract', ''),
             'source_type': 'encyclopedia', 'published_at': None, 'provider': 'wikipedia'} for p in pages]


def rss_items(raw, query):
    tree = ET.fromstring(raw)
    wanted = tokens(query)
    result = []
    for item in tree.findall('.//item'):
        title = clean(item.findtext('title', ''))
        description = clean(item.findtext('description', ''))
        score = len(wanted & tokens(title + ' ' + description))
        if not wanted or score < max(1, min(2, len(wanted))):
            continue
        published = item.findtext('pubDate')
        try:
            published = parsedate_to_datetime(published).isoformat() if published else None
        except (ValueError, TypeError):
            published = None
        result.append({'url': item.findtext('link', ''), 'title': title, 'text': description,
                       'source_type': 'news', 'published_at': published, 'provider': 'rss', 'score': score})
    return sorted(result, key=lambda x: x['score'], reverse=True)


def gdelt(query, limit):
    safe_query = ' '.join(re.findall(r'[\w-]+', query))
    result = api('https://api.gdeltproject.org/api/v2/doc/doc',
                 {'query': f'"{safe_query}" sourcelang:english', 'mode': 'artlist', 'format': 'json',
                  'maxrecords': max(5, limit), 'timespan': '3months', 'sort': 'datedesc'})
    return [{'url': a['url'], 'title': a.get('title', ''), 'text': '', 'source_type': 'news',
             'published_at': None, 'discovered_at': a.get('seendate'), 'provider': 'gdelt'}
            for a in result.get('articles', [])]


def extract_article(url):
    import trafilatura
    raw, final = fetch(url)
    text = trafilatura.extract(raw, include_comments=False, include_tables=False) or ''
    return text, final


def research(path, query, limit=8, supplied_urls=(), use_news=True):
    import studio
    data = studio.read(path)
    if not query.strip() or not 1 <= limit <= 20:
        raise ValueError('Informe um tema e limite entre 1 e 20.')
    candidates, errors = [], []
    for url in supplied_urls:
        candidates.append({'url': url, 'title': url, 'text': '', 'source_type': 'user_selected',
                           'provider': 'direct', 'published_at': None})
    print('Pesquisando contexto histórico...', flush=True)
    try:
        candidates.extend(wikipedia(query, min(3, limit)))
    except Exception as exc:
        errors.append({'provider': 'wikipedia', 'error': str(exc)})
    if use_news:
        print('Pesquisando notícias e feeds...', flush=True)
        try:
            candidates.extend(gdelt(query, limit))
        except Exception as exc:
            errors.append({'provider': 'gdelt', 'error': str(exc)})
        for feed in FEEDS[data['channel']]:
            try:
                raw, _ = fetch(feed)
                candidates.extend(rss_items(raw, query)[:limit])
            except Exception as exc:
                errors.append({'provider': feed, 'error': str(exc)})
    existing = {canonical(s['url']) for s in data.get('sources', [])}
    added = []
    for candidate in candidates:
        if len(added) >= limit:
            break
        url = canonical(candidate['url'])
        if url in existing:
            continue
        text = candidate.get('text', '')
        if candidate['provider'] != 'wikipedia':
            try:
                article, final = extract_article(url)
                if article:
                    text = article
                url = canonical(final)
            except Exception as exc:
                errors.append({'provider': url, 'error': str(exc)})
        if len(text.split()) < 20 or url in existing:
            continue
        # Store a bounded research excerpt, not an article mirror or a claimed verified summary.
        excerpt = ' '.join(text.split()[:100])
        now = datetime.now(timezone.utc).isoformat()
        item = {'id': 'web-' + hashlib.sha256(url.encode()).hexdigest()[:16], 'url': url,
                'title': candidate['title'], 'accessed_at': now, 'published_at': candidate.get('published_at'),
                'source_type': candidate['source_type'], 'provider': candidate['provider'],
                'notes': 'AUTOMATIC UNVERIFIED EXCERPT — verify context and facts before publication: ' + excerpt,
                'verification': 'unverified', 'excerpt_sha256': hashlib.sha256(excerpt.encode()).hexdigest()}
        if candidate.get('discovered_at'):
            item['discovered_at'] = candidate['discovered_at']
        added.append(item)
        existing.add(url)
    report = {'query': query, 'time': datetime.now(timezone.utc).isoformat(), 'added': added,
              'errors': errors, 'news_found': sum(s['source_type'] == 'news' for s in added),
              'note': 'Automated collection, not fact checking. Encyclopedia context is not current-news verification.'}
    report_path = path.with_name(path.stem + '-research.json')
    studio.write(report_path, report)
    if not added:
        raise ValueError(f'Nenhuma fonte com texto suficiente. Consulte {report_path}. Tente tema mais curto ou --url.')
    data.setdefault('sources', []).extend(added)
    data.pop('review', None)
    studio.write(path, data)
    print(f'{len(added)} fontes adicionadas; {report["news_found"]} notícias. Relatório: {report_path}')
    for error in errors:
        print(f'Aviso: {error["provider"]}: {error["error"]}')
    return report


def allowed_license(meta, attribution=False):
    name = clean(meta.get('LicenseShortName', {}).get('value', '')).lower()
    url = html.unescape(meta.get('LicenseUrl', {}).get('value', ''))
    # Exact allowlist; unknown/NC/ND/share-alike licenses are never silently admitted.
    if name in ('public domain', 'cc0', 'cc0 1.0'):
        return name, url
    if attribution and re.fullmatch(r'cc by (1\.0|2\.0|2\.5|3\.0|4\.0)', name):
        if re.match(r'https?://creativecommons.org/licenses/by/[0-9.]+/?$', url):
            return name, url
    return None


def commons_images(query, attribution=False, limit=6):
    data = api(COMMONS, {'action': 'query', 'generator': 'search', 'gsrsearch': query + ' filetype:bitmap',
                        'gsrnamespace': 6, 'gsrlimit': 50, 'prop': 'imageinfo',
                        'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': 1920, 'format': 'json'})
    result = []
    pages = sorted(data.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
    for page in pages:
        info = page.get('imageinfo', [{}])[0]
        meta = info.get('extmetadata', {})
        license_info = allowed_license(meta, attribution)
        description = clean(meta.get('ImageDescription', {}).get('value', ''))
        labels = (page['title'] + ' ' + description + ' ' +
                  clean(meta.get('Categories', {}).get('value', ''))).lower()
        if any(term in labels for term in ('ai-generated', 'ai generated', 'midjourney', 'dall-e',
                                          'stable diffusion', 'computer-generated', 'illustration', 'painting')):
            continue
        if not license_info or info.get('mime') not in ('image/jpeg', 'image/png', 'image/webp'):
            continue
        if info.get('width', 0) < 900 or info.get('height', 0) < 500:
            continue
        result.append({'url': info.get('thumburl', info['url']), 'origin': info['descriptionurl'],
                       'title': page['title'], 'creator': clean(meta.get('Artist', {}).get('value', 'Unknown')),
                       'license': license_info[0], 'license_url': license_info[1],
                       'description': description[:800],
                       'provider': 'Wikimedia Commons', 'license_evidence': meta})
        if len(result) >= limit:
            break
    return result


def download_photo(item, destination):
    from PIL import Image, ImageOps
    raw, final_url = fetch(item['url'], limit=20_000_000)
    with Image.open(io.BytesIO(raw)) as image:
        if image.width * image.height > 40_000_000 or min(image.size) < 450:
            raise ValueError('Imagem grande demais ou resolução insuficiente.')
        image = ImageOps.exif_transpose(image).convert('RGB')
        image.thumbnail((2400, 2400))
        image.save(destination, quality=93)
    return final_url


def visuals(path, attribution=False, per_scene=2):
    import studio
    data = studio.read(path)
    assets = path.parent / 'assets'
    assets.mkdir(exist_ok=True)
    report = {'time': datetime.now(timezone.utc).isoformat(), 'downloaded': [], 'errors': []}
    used = {shot['asset_origin'] for scene in data['scenes'] for shot in studio.scene_assets(scene)
            if shot.get('asset_origin')}
    for scene_index, scene in enumerate(data['scenes'], 1):
        if scene.get('visual') or scene.get('visuals'):
            continue
        query = scene.get('visual_query', '').strip()
        if not query:
            report['errors'].append({'scene': scene_index, 'error': 'Falta visual_query em inglês.'})
            continue
        print(f'Cena {scene_index}: buscando fotos de {query}...', flush=True)
        try:
            candidates = commons_images(query, attribution, limit=12)
        except Exception as exc:
            report['errors'].append({'scene': scene_index, 'error': str(exc)})
            continue
        shots = []
        for candidate in candidates:
            if candidate['origin'] in used:
                continue
            digest = hashlib.sha256(candidate['origin'].encode()).hexdigest()[:12]
            target = assets / f'commons-{digest}.jpg'
            try:
                downloaded = download_photo(candidate, target)
            except Exception as exc:
                report['errors'].append({'scene': scene_index, 'url': candidate['origin'], 'error': str(exc)})
                continue
            record = {**candidate, 'download_url': downloaded, 'downloaded_at': report['time'],
                      'file': target.relative_to(path.parent).as_posix(), 'sha256': studio.file_hash(target),
                      'changes': 'Resized, cropped and animated for video; original license retained.',
                      'relevance': 'automatic_keyword_match_requires_review'}
            studio.write(target.with_suffix('.license.json'), record)
            shots.append({'visual': record['file'], 'asset_origin': candidate['origin'],
                          'asset_rights': candidate['license'], 'creator': candidate['creator'],
                          'license_url': candidate['license_url'], 'asset_title': candidate['title'],
                          'visual_context': 'Illustrative photograph; not proof of the narrated event.'})
            used.add(candidate['origin'])
            report['downloaded'].append(record)
            if len(shots) >= per_scene:
                break
        if shots:
            scene['visuals'] = shots
            scene.pop('visual', None)
        else:
            report['errors'].append({'scene': scene_index, 'error': 'Nenhuma foto utilizável com licença permitida. Tente visual_query mais concreta.'})
    if report['downloaded']:
        data.pop('review', None)
        studio.write(path, data)
    report_path = path.with_name(path.stem + '-visuals.json')
    studio.write(report_path, report)
    print(f'{len(report["downloaded"])} fotos obtidas. Relatório: {report_path}')
    for error in report['errors']:
        print(f'Aviso cena {error["scene"]}: {error["error"]}')
    if not report['downloaded'] and report['errors']:
        raise ValueError('Não foi possível obter fotos novas; consulte o relatório.')
    return report
