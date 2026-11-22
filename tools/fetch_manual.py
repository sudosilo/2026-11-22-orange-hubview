# Crawls the Operation CHARM repair manual for a car and saves every diagram
# image plus an index of where each image came from.
# Usage: python3 tools/fetch_manual.py accord   (or prius)
import urllib.request, urllib.parse, re, json, os, sys, time, html

CARS = {
    'accord': 'https://charm.li/Honda/1982/Accord%20L4-1751cc%201800%20EK1/Repair%20and%20Diagnosis/',
    'prius': 'https://charm.li/Toyota/2007/Prius%20L4-1.5L%20%281NZ-FXE%29%20Hybrid/Repair%20and%20Diagnosis/',
}
MAX_PAGES = 4000
MAX_IMAGES = 2500
MAX_BYTES = 800000

car = sys.argv[1]
base = CARS[car]
out = os.path.join('ref', 'manual', car)
os.makedirs(out, exist_ok=True)
index_path = os.path.join(out, 'index.json')
index = json.load(open(index_path)) if os.path.exists(index_path) else []
have = {e['src'] for e in index}

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 hubview-manual-fetch'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read(), r.headers.get('Content-Type', '')
        except Exception as e:
            time.sleep(2 + attempt * 3)
    return None, ''

tok = re.compile(r'<h[1-6][^>]*>(.*?)</h[1-6]>|<img[^>]*src="([^"]+)"|<a[^>]*href="([^"]+)"', re.S | re.I)
queue, seen, pages, saved = [base], {base}, 0, len(index)
while queue and pages < MAX_PAGES and saved < MAX_IMAGES:
    url = queue.pop(0)
    body, ctype = get(url)
    pages += 1
    if not body or 'html' not in ctype:
        continue
    text = body.decode('utf-8', 'replace')
    rel = urllib.parse.unquote(url[len(base):]).strip('/')
    caption = ''
    for m in tok.finditer(text):
        if m.group(1) is not None:
            caption = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
        elif m.group(2):
            src = urllib.parse.urljoin(url, m.group(2))
            if '/images/' not in src or src in have:
                continue
            data, it = get(src)
            if not data or len(data) > MAX_BYTES:
                continue
            ext = 'png' if 'png' in it else 'gif' if 'gif' in it else 'jpg'
            name = '%04d.%s' % (len(index), ext)
            open(os.path.join(out, name), 'wb').write(data)
            index.append({'file': name, 'path': rel, 'caption': caption, 'src': src})
            have.add(src)
            saved += 1
        elif m.group(3):
            href = urllib.parse.urljoin(url, html.unescape(m.group(3))).split('#')[0]
            if href.startswith(base) and href.endswith('/') and href not in seen:
                seen.add(href)
                queue.append(href)
    if pages % 25 == 0:
        json.dump(index, open(index_path, 'w'), indent=0)
        print(car, 'pages', pages, 'images', saved, 'queued', len(queue), flush=True)
    time.sleep(0.2)

json.dump(index, open(index_path, 'w'), indent=0)
print(car, 'done. pages', pages, 'images', saved)
