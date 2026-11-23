# Crawls the public dealer parts catalog pages for a car and saves every
# part name and OEM part number it finds.
# Usage: python3 tools/fetch_catalog.py prius
import subprocess, re, json, os, sys, time, html

CARS = {
    'prius': ('https://www.toyotapartsnow.com/parts-select/', '2007-toyota-prius-', '2007 Toyota Prius',
              ['oil-filter', 'fuel-tank', 'car-batteries', 'headlight-bulb', 'weather-strip', 'power-window-switch',
               'brake-pads', 'brake-rotor', 'shock-absorber', 'control-arm', 'strut-housing', 'radiator', 'water-pump',
               'spark-plug', 'ignition-coil', 'axle-shaft', 'wheel-bearing', 'tie-rod-end', 'bumper-cover', 'door-handle',
               'hybrid-battery', 'inverter', 'steering-column', 'brake-caliper', 'brake-shoe-set', 'brake-drum']),
}
car = sys.argv[1]
base, prefix, label, seeds = CARS[car]
out = os.path.join('ref', 'parts')
os.makedirs(out, exist_ok=True)
path = os.path.join(out, 'catalog-%s.json' % car)
LOG = open(os.path.join(out, 'catalog-%s-log.txt' % car), 'a')

def get(url):
    for attempt in range(3):
        try:
            r = subprocess.run(['curl', '-sSL', '-A', 'Mozilla/5.0 (Linux; Android) Firefox', '-w', '\n%{http_code}', url],
                               capture_output=True, timeout=60)
            body = r.stdout
            i = body.rfind(b'\n')
            code = body[i+1:].decode('ascii', 'replace').strip()
            if code == '200':
                return body[:i].decode('utf-8', 'replace')
            LOG.write('%s %s\n' % (code, url)); LOG.flush()
            if code == '404':
                return None
        except Exception as e:
            LOG.write('ERR %s %s\n' % (url, e)); LOG.flush()
        time.sleep(2 + attempt * 3)
    return None

link_re = re.compile(r'/parts-select/(' + re.escape(prefix) + r'[a-z0-9\-]+)')
pn = r'[0-9A-Z]{5}-[0-9A-Z]{5}(?:-[0-9A-Z]{2})?'
part_re = re.compile(re.escape(label) + r' ((?:(?!Toyota Prius|Part Number)[^<>]){2,120}?)\s*Part Number:\s*(' + pn + ')')
seen = set(prefix + s for s in seeds)
queue = list(seen)
items, keyset, pages = [], set(), 0
while queue and pages < 3000:
    slug = queue.pop(0)
    page = get(base + slug)
    pages += 1
    if page is None:
        continue
    if pages <= 2:
        open(os.path.join(out, 'catalog-sample%d.html' % pages), 'w').write(page)
    text = html.unescape(re.sub(r'<[^>]+>', ' ', page))
    text = re.sub(r'\s+', ' ', text)
    for m in part_re.finditer(text):
        name, num = m.group(1).strip(), m.group(2)
        k = (name, num)
        if k not in keyset:
            keyset.add(k)
            items.append({'category': slug[len(prefix):], 'name': name, 'number': num})
    for m in link_re.finditer(page):
        s = m.group(1)
        if s not in seen:
            seen.add(s)
            queue.append(s)
    if pages % 25 == 0:
        json.dump(items, open(path, 'w'), indent=0)
        print(car, 'pages', pages, 'parts', len(items), 'queued', len(queue), flush=True)
    time.sleep(0.4)
json.dump(items, open(path, 'w'), indent=0)
print(car, 'done. pages', pages, 'parts', len(items))
LOG.write('done pages %d parts %d\n' % (pages, len(items))); LOG.flush()
