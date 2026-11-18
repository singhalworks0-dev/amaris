"""Capture the public Amaris storefront, retaining the original theme and routes."""
import concurrent.futures, gzip, hashlib, json, pathlib, re, threading, time
import urllib.request, urllib.parse, xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
CACHE = ROOT / 'storefront'
ORIGIN = 'https://www.amarisjewels.com'
lock = threading.Lock()

def location(path):
    return CACHE / (hashlib.sha256(path.encode()).hexdigest() + '.bin')

def fetch(path):
    target = location(path)
    meta = target.with_suffix('.json')
    if target.exists() and meta.exists():
        return target.read_bytes(), json.loads(meta.read_text())['type']
    url = ORIGIN + path
    if path.startswith('/_remote/'):
        url = 'https://' + path[len('/_remote/'):]
        host = urllib.parse.urlsplit(url).hostname
        if host not in ('cdn.shopify.com', 'fonts.googleapis.com', 'fonts.gstatic.com'):
            raise ValueError('Unsupported asset host')
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0', 'Accept-Encoding':'gzip'})
            with urllib.request.urlopen(req, timeout=50) as response:
                data = response.read()
                if response.headers.get('Content-Encoding') == 'gzip':
                    data = gzip.decompress(data)
                typ = response.headers.get('Content-Type', 'application/octet-stream')
            CACHE.mkdir(exist_ok=True)
            temp = target.with_suffix(f'.{threading.get_ident()}.tmp')
            temp.write_bytes(data)
            temp.replace(target)
            temp_meta = meta.with_suffix(f'.{threading.get_ident()}.meta.tmp')
            temp_meta.write_text(json.dumps({'path':path, 'type':typ, 'source':url}))
            temp_meta.replace(meta)
            return data, typ
        except Exception:
            if attempt == 2: raise
            time.sleep(attempt + 1)

def rewrite(data, typ):
    if not any(x in typ for x in ('text/', 'javascript', 'json', 'xml')): return data
    s = data.decode('utf-8', errors='replace')
    for host in ('www.amarisjewels.com', 'amarisjewels.com'):
        s = s.replace('https://' + host, '').replace('http://' + host, '').replace('//' + host, '')
        s = s.replace('https:\\/\\/' + host, '').replace('\\/\\/' + host, '')
    for host in ('cdn.shopify.com', 'fonts.googleapis.com', 'fonts.gstatic.com'):
        s = s.replace('https://' + host, '/_remote/' + host).replace('//' + host, '/_remote/' + host)
    if 'text/html' in typ:
        # Keep storefront scripts, remove third party visitor tracking and live form submission.
        s = re.sub(r'<script\b[^>]*\bsrc=["\x27](?:https?:)?//(?:www\.googletagmanager\.com|connect\.facebook\.net|static\.klaviyo\.com|analytics\.tiktok\.com)[^>]*>.*?</script>', '', s, flags=re.S|re.I)
        # The speed app preloads every navigation destination, overwhelming a local mirror.
        s = re.sub(r'<script\b[^>]*>(?:(?!</script>).)*instantPageUrl(?:(?!</script>).)*</script>', '', s, flags=re.S|re.I)
        seen_interactions = False
        def dedupe(match):
            nonlocal seen_interactions
            script = match.group(0)
            if 'pmUserInteractions' not in script: return script
            if seen_interactions: return ''
            seen_interactions = True
            return script
        s = re.sub(r'<script\b[^>]*>.*?</script>', dedupe, s, flags=re.S|re.I)
        s = s.replace('</head>', '<script src="/replica.js" defer></script></head>')
    return s.encode()

def assets(text):
    found = set()
    for u in re.findall(r'''(?:https?:)?//(?:www\.amarisjewels\.com|cdn\.shopify\.com)/[^\s"'<>\\)]+|/cdn/[^\s"'<>\\)]+''', text):
        u = u.replace('&amp;', '&')
        u = re.sub(r'^(?:https?:)?//www\.amarisjewels\.com', '', u)
        u = re.sub(r'^(?:https?:)?//cdn\.shopify\.com', '/_remote/cdn.shopify.com', u)
        if u.startswith(('/cdn/', '/_remote/')):
            found.add(u)
    return found

def capture():
    CACHE.mkdir(exist_ok=True)
    home = (ROOT / 'reference.html').read_bytes()
    location('/').write_bytes(home)
    location('/').with_suffix('.json').write_text(json.dumps({'path':'/','type':'text/html; charset=utf-8'}))
    ns = {'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap = ET.fromstring((ROOT / 'sitemap.xml').read_text())
    maps = [e.text for e in sitemap.findall('s:sitemap/s:loc',ns) if '/en-int/' not in e.text and 'agentic' not in e.text]
    pages = {'/', '/cart', '/search', '/policies/privacy-policy', '/policies/refund-policy', '/policies/terms-of-service', '/policies/shipping-policy'}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for data, _ in pool.map(fetch, [u.replace(ORIGIN,'') for u in maps]):
            xml = ET.fromstring(data)
            pages.update(e.text.replace(ORIGIN,'') for e in xml.findall('s:url/s:loc',ns))
    pages.update(re.findall(r'href=["\x27]((?:/pages/|/collections/|/blogs/)[^"\x27?#]+)', home.decode()))
    for href in re.findall(r'href=["\x27]([^"\x27]+)',home.decode()):
        url=urllib.parse.urlsplit(urllib.parse.urljoin(ORIGIN,href.replace('&amp;','&')))
        if url.hostname in ('www.amarisjewels.com','amarisjewels.com') and url.path.startswith(('/pages/','/collections/','/products/','/blogs/','/policies/')):
            pages.add(url.path)
    (ROOT/'routes.json').write_text(json.dumps(sorted(pages),indent=2))
    print(f'Found {len(pages)} public routes', flush=True)
    failures=[]
    theme_assets=set()
    def page(path):
        try:
            data,typ=fetch(path)
            if 'html' in typ:
                urls=assets(data.decode(errors='replace'))
                with lock: theme_assets.update(u for u in urls if re.search(r'\.(?:js|css|woff2?|ttf|otf)(?:\?|$)',u))
            return True
        except Exception as e:
            with lock: failures.append({'path':path,'error':str(e)})
            return False
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for i,_ in enumerate(pool.map(page, sorted(pages)),1):
            if i%25==0: print(f'Pages {i}/{len(pages)}',flush=True)
    theme_assets.update(assets(home.decode()))
    print(f'Capturing {len(theme_assets)} theme and homepage assets',flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for i,_ in enumerate(pool.map(page,sorted(theme_assets)),1):
            if i%100==0: print(f'Assets {i}/{len(theme_assets)}',flush=True)
    # Font faces and CSS background images are dependencies of the stylesheets.
    dependencies=set()
    for m in CACHE.glob('*.json'):
        meta=json.loads(m.read_text())
        if 'css' in meta['type']:
            content=m.with_suffix('.bin').read_text(encoding='utf-8',errors='replace')
            for u in re.findall(r'url\(["\x27]?([^\)"\x27]+)',content):
                absolute=urllib.parse.urljoin(ORIGIN+meta['path'],u)
                if absolute.startswith(ORIGIN): dependencies.add(absolute.replace(ORIGIN,''))
                elif absolute.startswith('https://cdn.shopify.com'): dependencies.add(absolute.replace('https://cdn.shopify.com','/_remote/cdn.shopify.com'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: list(pool.map(page,dependencies))
    (ROOT/'capture-report.json').write_text(json.dumps({'routes':len(pages),'assets':len(theme_assets),'failures':failures},indent=2))
    print('Capture complete. Failures: '+str(len(failures)),flush=True)

if __name__=='__main__': capture()
