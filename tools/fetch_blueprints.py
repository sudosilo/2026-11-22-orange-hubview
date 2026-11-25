# Pulls every free raster car blueprint from getoutlines.com into ref/blueprints/<make>/.
# Walks the make list, every page of each make, opens each blueprint page, saves the image and
# records title, year, size and license in ref/blueprints/index.jsonl. Resumable: rerun to continue.
# Progress is pushed to GitHub every 300 images. Optional: python3 tools/fetch_blueprints.py honda ford
import re, json, os, sys, time, html, subprocess, urllib.parse

BASE = 'https://getoutlines.com'
OUT = os.path.join('ref', 'blueprints')
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, 'log.txt'), 'a')
IDX = os.path.join(OUT, 'index.jsonl')

def get(url, binary=False):
    for attempt in range(3):
        try:
            r = subprocess.run(['curl', '-sSL', '-A', 'Mozilla/5.0 (Linux; Android) Firefox', '-w', '\n%{http_code}', url], capture_output=True, timeout=90)
            body = r.stdout; i = body.rfind(b'\n'); code = body[i+1:].strip()
            if code == b'200':
                return body[:i] if binary else body[:i].decode('utf-8', 'replace')
            LOG.write('%s %s\n' % (code.decode()[:5], url)); LOG.flush()
            if code == b'404': return None
        except Exception as e:
            LOG.write('ERR %s %s\n' % (url, e)); LOG.flush()
        time.sleep(3 + attempt * 5)
    return None

def checkpoint(msg):
    subprocess.run(['git', 'add', OUT])
    subprocess.run(['git', 'commit', '-q', '-m', msg])
    subprocess.run(['git', 'pull', '-q', '--rebase', '-X', 'theirs'])
    subprocess.run(['git', 'push', '-q'])

done = set()
if os.path.exists(IDX):
    for line in open(IDX):
        try: done.add(json.loads(line)['id'])
        except Exception: pass

top = get(BASE + '/car-blueprints') or ''
makes = sorted(set(m for m in re.findall(r'/car-blueprints/([a-z0-9-]+)(?=["\'?])', top)))
if len(sys.argv) > 1:
    makes = [m for m in makes if m in sys.argv[1:]] or sys.argv[1:]
print('makes', len(makes), flush=True)

saved = 0
for make in makes:
    ids, page = {}, 1
    while page < 200:
        t = get('%s/car-blueprints/%s?page=%d' % (BASE, make, page))
        if not t: break
        found = re.findall(r'/blueprints/(\d+)/([a-z0-9._-]+?)-blueprints', t)
        new = [(i, s) for i, s in found if i not in ids]
        for i, s in new: ids[i] = s
        if not new or ('page=%d' % (page + 1)) not in t: break
        page += 1
        time.sleep(0.3)
    todo = [(i, s) for i, s in ids.items() if i not in done and not s.endswith('-tag')]
    print(make, 'blueprints', len(ids), 'to fetch', len(todo), flush=True)
    for bid, slug in todo:
        page_url = '%s/blueprints/%s/%s-blueprints' % (BASE, bid, slug)
        t = get(page_url)
        time.sleep(0.3)
        if not t: continue
        m = re.search(r'((?:https?://getoutlines\.com)?/blueprints/car/[^"\'\s<>]+?\.(?:gif|png|jpe?g))', t, re.I)
        title = re.search(r'<title>(.*?)</title>', t, re.S)
        lic = re.search(r'License:\s*(?:<[^>]+>\s*)*([^<\n]+)', t)
        dims = re.search(r'Dimensions:\s*(?:<[^>]+>\s*)*(\d+\s*x\s*\d+)', t)
        rec = {'id': bid, 'make': make, 'slug': slug, 'page': page_url,
               'title': html.unescape(title.group(1)).strip() if title else slug,
               'license': html.unescape(lic.group(1)).strip() if lic else '',
               'dims': dims.group(1) if dims else '', 'file': ''}
        if m:
            img = urllib.parse.urljoin(BASE, m.group(1))
            data = get(img, binary=True)
            if data:
                d = os.path.join(OUT, make); os.makedirs(d, exist_ok=True)
                fn = bid + '-' + os.path.basename(urllib.parse.urlparse(img).path)
                open(os.path.join(d, fn), 'wb').write(data)
                rec['file'] = make + '/' + fn; rec['image'] = img
                saved += 1
        with open(IDX, 'a') as f: f.write(json.dumps(rec) + '\n')
        done.add(bid)
        if saved and saved % 300 == 0:
            print('saved', saved, flush=True)
            checkpoint('blueprints checkpoint %d images' % saved)
print('done, saved', saved)
checkpoint('blueprints complete, %d new images' % saved)
