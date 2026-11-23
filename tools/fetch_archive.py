# Builds a full text archive of a car's Operation CHARM manual.
# The top page already holds the whole section tree, so we read it once,
# then fetch every leaf page and keep its text, tables and image links.
# Output: ref/archive/<car>/<section>.jsonl plus specs.json (torque and spec lines).
# Usage: python3 tools/fetch_archive.py crownvic   (resumable, rerun to continue)
import re, json, os, sys, time, html, subprocess, urllib.parse

CARS = {
    'accord': 'https://charm.li/Honda/1982/Accord%20L4-1751cc%201800%20EK1/Repair%20and%20Diagnosis/',
    'prius': 'https://charm.li/Toyota/2007/Prius%20L4-1.5L%20%281NZ-FXE%29%20Hybrid/Repair%20and%20Diagnosis/',
    'crownvic': 'https://charm.li/Ford/2006/Crown%20Victoria%20V8-4.6L%20VIN%20W/Repair%20and%20Diagnosis/',
}
car = sys.argv[1]
base = CARS[car]
out = os.path.join('ref', 'archive', car)
os.makedirs(out, exist_ok=True)
LOG = open(os.path.join(out, 'log.txt'), 'a')

def get(url):
    for attempt in range(3):
        try:
            r = subprocess.run(['curl', '-sSL', '-A', 'Mozilla/5.0 (Linux; Android) Firefox', '-w', '\n%{http_code}', url], capture_output=True, timeout=90)
            body = r.stdout; i = body.rfind(b'\n')
            if body[i+1:].strip() == b'200':
                return body[:i].decode('utf-8', 'replace')
            LOG.write('%s %s\n' % (body[i+1:].decode()[:5], url)); LOG.flush()
        except Exception as e:
            LOG.write('ERR %s %s\n' % (url, e)); LOG.flush()
        time.sleep(2 + attempt * 3)
    return None

def main_html(t):
    i = t.find("<div class='main'>")
    if i < 0: i = t.find('<div class="main">')
    j = t.find('theme-colors footer', i)
    return t[i:j] if i >= 0 else ''

def to_text(h):
    h = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', h, flags=re.S | re.I)
    h = re.sub(r'<button[^>]*>.*?</button>', '', h, flags=re.S | re.I)
    h = re.sub(r'</t[dh]>', ' | ', h, flags=re.I)
    h = re.sub(r'<(br|/p|/tr|/li|/h[1-6]|/div|/caption)[^>]*>', '\n', h, flags=re.I)
    h = re.sub(r'<[^>]+>', '', h)
    lines = [re.sub(r'[ \t\xa0]+', ' ', html.unescape(l)).strip(' |') for l in h.split('\n')]
    return '\n'.join(l for l in lines if l)

# 1. section tree from the top page
top = get(base)
if not top:
    sys.exit('could not load the top page')
hrefs = []
for m in re.finditer(r"<a[^>]*href=['\"]([^'\"]+)['\"]", main_html(top)):
    u = urllib.parse.urljoin(base, html.unescape(m.group(1))).split('#')[0]
    if u.startswith(base) and u.endswith('/') and u != base:
        hrefs.append(u)
hrefs = list(dict.fromkeys(hrefs))
hs = set(hrefs)
srt = sorted(hrefs)
leaves = [u for i, u in enumerate(srt) if not (i + 1 < len(srt) and srt[i + 1].startswith(u))]
rel = lambda u: urllib.parse.unquote(u[len(base):]).strip('/')
late = re.compile(r'Diagnostic Trouble Codes|Technical Service Bulletins|Relays and Modules|Sensors and Switches', re.I)
leaves.sort(key=lambda u: (1 if late.search(rel(u)) else 0))
json.dump([rel(u) for u in hrefs], open(os.path.join(out, 'tree.json'), 'w'), indent=0)
print(car, 'sections', len(hrefs), 'pages to read', len(leaves), flush=True)

# 2. resume
done = set()
for f in os.listdir(out):
    if f.endswith('.jsonl'):
        for line in open(os.path.join(out, f)):
            try: done.add(json.loads(line)['path'])
            except Exception: pass

def section_file(p):
    s = re.sub(r'[^a-z0-9]+', '-', p.split('/')[0].lower()).strip('-') or 'misc'
    k = 1
    while True:
        f = os.path.join(out, s + ('' if k == 1 else '-%d' % k) + '.jsonl')
        if not os.path.exists(f) or os.path.getsize(f) < 40 * 1024 * 1024:
            return f
        k += 1

def checkpoint(msg):
    # save progress to GitHub so a crash or a closed Termux loses nothing
    subprocess.run(['git', 'add', out])
    subprocess.run(['git', 'commit', '-q', '-m', msg])
    subprocess.run(['git', 'pull', '-q', '--rebase', '-X', 'theirs'])
    subprocess.run(['git', 'push', '-q'])

# 3. leaves
n = 0
queue = list(leaves)
while queue:
    u = queue.pop(0)
    p = rel(u)
    if p in done: continue
    t = get(u); n += 1
    if t is None: continue
    try:
      m = main_html(t)
      for k in re.findall(r"<a[^>]*href=['\"]([^'\"]+)['\"]", m):
          c = urllib.parse.urljoin(u, html.unescape(k)).split('#')[0]
          if c.startswith(u) and c != u and c.endswith('/') and c not in hs:
              hs.add(c); queue.append(c)
      imgs = [urllib.parse.urljoin(u, x) for x in re.findall(r"<img[^>]*src=['\"]([^'\"]+)", m) if '/images/' in x]
      title = re.search(r'<h1>(.*?)</h1>', m, re.S)
      rec = {'path': p, 'title': html.unescape(title.group(1)).strip() if title else p.split('/')[-1], 'text': to_text(m), 'images': imgs}
      with open(section_file(p), 'a') as f:
          f.write(json.dumps(rec) + '\n')
      done.add(p)
    except Exception as e:
        LOG.write('PARSE %s %s\n' % (u, e)); LOG.flush()
    if n % 50 == 0:
        print(car, 'read', len(done), 'left', len(queue), flush=True)
    if n % 500 == 0:
        checkpoint('%s archive checkpoint %d pages' % (car, len(done)))
    time.sleep(0.15)

# 4. specs index: torque and spec lines with their page path
TQ = re.compile(r'(\bN\.?m\b|N·m|ft\.?\s*-?\s*lb|lb\.?\s*-?\s*ft|in\.?\s*-?\s*lb|kgf)', re.I)
specs = []
for f in sorted(os.listdir(out)):
    if not f.endswith('.jsonl'): continue
    for line in open(os.path.join(out, f)):
        r = json.loads(line)
        is_spec = 'Specification' in r['path']
        ls = [l for l in r['text'].split('\n') if TQ.search(l) or (is_spec and re.search(r'\d', l))]
        if ls:
            specs.append({'path': r['path'], 'title': r['title'], 'lines': ls[:80]})
json.dump(specs, open(os.path.join(out, 'specs.json'), 'w'), indent=0)
print(car, 'done. pages', len(done), 'spec pages', len(specs))
checkpoint('%s archive complete, %d pages' % (car, len(done)))
