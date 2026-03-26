import json, math, re, time
from pathlib import Path
from urllib.parse import urljoin
import requests

BASE = 'https://osmedica.com.ar/wp-json/wp/v2/'
SITE = 'https://osmedica.com.ar/'
OUT = Path('research/osmedica-api')
OUT.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; CloBot/1.0; +https://osmedica.com.ar)'})


def fetch_json(url, params=None):
    r = session.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r


def fetch_all(endpoint, per_page=100):
    url = urljoin(BASE, endpoint)
    first = fetch_json(url, {'per_page': per_page, 'page': 1})
    total_pages = int(first.headers.get('X-WP-TotalPages', '1'))
    total = int(first.headers.get('X-WP-Total', '0'))
    items = first.json()
    for page in range(2, total_pages + 1):
        r = fetch_json(url, {'per_page': per_page, 'page': page})
        items.extend(r.json())
        time.sleep(0.1)
    return {'endpoint': endpoint, 'total': total, 'pages': total_pages, 'items': items}


def strip_html(s):
    if not s:
        return ''
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

# Pull collections
collections = {}
for endpoint in ['tipo_de_prestador', 'provincia', 'especialidades', 'estudios', 'cartilla']:
    collections[endpoint] = fetch_all(endpoint)
    (OUT / f'{endpoint}.json').write_text(json.dumps(collections[endpoint], ensure_ascii=False, indent=2))

# Build taxonomy maps
maps = {}
for endpoint in ['tipo_de_prestador', 'provincia', 'especialidades', 'estudios']:
    maps[endpoint] = {item['id']: item for item in collections[endpoint]['items']}

# Normalize cartilla items
normalized = []
for item in collections['cartilla']['items']:
    provincias = [maps['provincia'].get(pid) for pid in item.get('provincia', []) if pid in maps['provincia']]
    top_regions = [p for p in provincias if p and p.get('parent') == 0]
    sub_locations = [p for p in provincias if p and p.get('parent') != 0]
    normalized.append({
        'id': item['id'],
        'slug': item['slug'],
        'nombre': strip_html(item.get('title', {}).get('rendered', '')),
        'url': item.get('link'),
        'tipo_prestador': [maps['tipo_de_prestador'][tid]['name'] for tid in item.get('tipo_de_prestador', []) if tid in maps['tipo_de_prestador']],
        'especialidades': [maps['especialidades'][eid]['name'] for eid in item.get('especialidades', []) if eid in maps['especialidades']],
        'estudios': [maps['estudios'][eid]['name'] for eid in item.get('estudios', []) if eid in maps['estudios']],
        'zonas': [{'id': p['id'], 'nombre': p['name'], 'slug': p['slug']} for p in top_regions],
        'localidades': [{'id': p['id'], 'nombre': p['name'], 'slug': p['slug'], 'parent': p['parent']} for p in sub_locations],
        'class_list': item.get('class_list', []),
        'modified': item.get('modified')
    })

(OUT / 'cartilla.normalized.json').write_text(json.dumps(normalized, ensure_ascii=False, indent=2))

# Summary
summary = {
    'counts': {k: v['total'] for k, v in collections.items()},
    'tipo_prestador': [{'id': x['id'], 'name': x['name'], 'slug': x['slug'], 'count': x['count']} for x in collections['tipo_de_prestador']['items']],
    'top_level_zonas': [{'id': x['id'], 'name': x['name'], 'slug': x['slug'], 'count': x['count']} for x in collections['provincia']['items'] if x.get('parent') == 0],
    'sample_cartilla': normalized[:10]
}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))

# Probe individual page enrichment for first 30 items
probes = []
patterns = {
    'telefono_links': r'tel:[^"\']+',
    'mailto_links': r'mailto:[^"\']+',
    'google_maps': r'https?://(?:www\.)?google\.[^"\'\s<>]+',
    'whatsapp': r'https?://(?:wa\.me|api\.whatsapp\.com)[^"\'\s<>]*',
}
for item in normalized[:30]:
    try:
        html = session.get(item['url'], timeout=30).text
    except Exception as e:
        probes.append({'id': item['id'], 'url': item['url'], 'error': str(e)})
        continue
    rec = {'id': item['id'], 'slug': item['slug'], 'url': item['url']}
    for key, pat in patterns.items():
        rec[key] = sorted(set(re.findall(pat, html, re.I)))[:20]
    rec['contains_main_content_length'] = len(strip_html(re.search(r'<main.*?</main>', html, re.S|re.I).group(0) if re.search(r'<main.*?</main>', html, re.S|re.I) else ''))
    probes.append(rec)
    time.sleep(0.1)

(OUT / 'detail-page-probe.json').write_text(json.dumps(probes, ensure_ascii=False, indent=2))
print(json.dumps(summary, ensure_ascii=False, indent=2))
