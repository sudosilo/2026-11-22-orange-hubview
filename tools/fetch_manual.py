# Crawls the Operation CHARM repair manual for a car and saves every diagram
# image plus an index of where each image came from.
# Usage: python3 tools/fetch_manual.py accord   (or prius, crownvic)
import urllib.request, urllib.parse, re, json, os, sys, time, html

CARS = {
    'accord': 'https://charm.li/Honda/1982/Accord%20L4-1751cc%201800%20EK1/Repair%20and%20Diagnosis/',
    'prius': 'https://charm.li/Toyota/2007/Prius%20L4-1.5L%20%281NZ-FXE%29%20Hybrid/Repair%20and%20Diagnosis/',
    'crownvic': 'https://charm.li/Ford/2006/Crown%20Victoria%20V8-4.6L%20VIN%20W/Repair%20and%20Diagnosis/',
}
MAX_PAGES = 9000
MAX_IMAGES = 2500
# Skip sections the exploded view never uses: trouble codes, bulletins,
# diagnostic flowcharts and the mileage service schedules.
SKIP = re.compile(r'Diagnostic Trouble Codes|Technical Service Bulletins|Testing and Inspection|Symptom Related|Diagnostic Procedures|Initial Inspection|Normal Service|Severe Service|Service Precautions|Road Test|Relays and Modules|Sensors and Switches|Computers and Control Systems|Description and Operation|Trouble Code|Pinpoint Test', re.I)
CAPS = {'crownvic': 2600}
# sections read first, so the chassis and body diagrams come in before the cap
FIRST = {'crownvic': ['Steering and Suspension', 'Brakes and Traction Control', 'Body and Frame', 'Windows and Glass', 'Lighting and Horns', 'Starting and Charging', 'Heating and Air Conditioning', 'Restraints and Safety Systems', 'Wiper and Washer Systems', 'Power and Ground Distribution', 'Instrument Panel, Gauges and Warning Indicators', 'Accessories and Optional Equipment']}
MAX_BYTES = 800000

car = sys.argv[1]
base = CARS[car]
MAX_IMAGES = CAPS.get(car, MAX_IMAGES)
out = os.path.join('ref', 'manual', car)
os.makedirs(out, exist_ok=True)
index_path = os.path.join(out, 'index.json')
index = json.load(open(index_path)) if os.path.exists(index_path) else []
have = {e['src'] for e in index}

import subprocess
LOG = open(os.path.join(out, 'log.txt'), 'a')
def get(url):
    # curl handles TLS and redirects the same way the rest of the workflow does
    for attempt in range(3):
        try:
            r = subprocess.run(['curl', '-sSL', '-A', 'Mozilla/5.0 (Linux; Android) Firefox', '-w', '\n%{http_code} %{content_type}', url],
                               capture_output=True, timeout=60)
            body = r.stdout
            i = body.rfind(b'\n')
            meta = body[i+1:].decode('ascii', 'replace').split(' ', 1)
            code, ctype = meta[0], (meta[1] if len(meta) > 1 else '')
            if code == '200':
                return body[:i], ctype
            LOG.write('%s %s %s\n' % (code, url, r.stderr.decode('utf-8', 'replace')[:200])); LOG.flush()
        except Exception as e:
            LOG.write('ERR %s %s\n' % (url, e)); LOG.flush()
        time.sleep(2 + attempt * 3)
    return None, ''

tok = re.compile(r'<h[1-6][^>]*>(.*?)</h[1-6]>|<img[^>]*src="([^"]+)"|<a[^>]*href="([^"]+)"', re.S | re.I)
# also accept single quoted attributes
tok = re.compile(r'<h[1-6][^>]*>(.*?)</h[1-6]>|<img[^>]*src=["\']([^"\']+)|<a[^>]*href=["\']([^"\']+)', re.S | re.I)
seeds = [base + urllib.parse.quote(x) + '/' for x in FIRST.get(car, [])]
queue, seen, pages, saved = seeds + [base], set(seeds) | {base}, 0, len(index)
while queue and pages < MAX_PAGES and saved < MAX_IMAGES:
    url = queue.pop(0)
    body, ctype = get(url)
    pages += 1
    if not body or 'html' not in ctype:
        continue
    text = body.decode('utf-8', 'replace')
    if pages <= 2:
        open(os.path.join(out, 'sample%d.html' % pages), 'w').write(text)
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
            if href.startswith(base) and href.endswith('/') and href not in seen and not (car in CAPS and SKIP.search(urllib.parse.unquote(href[len(base):]))):
                seen.add(href)
                queue.append(href)
    if pages % 25 == 0:
        json.dump(index, open(index_path, 'w'), indent=0)
        print(car, 'pages', pages, 'images', saved, 'queued', len(queue), flush=True)
    time.sleep(0.2)

json.dump(index, open(index_path, 'w'), indent=0)
print(car, 'done. pages', pages, 'images', saved)
LOG.write('done pages %d images %d\n' % (pages, saved)); LOG.flush()
