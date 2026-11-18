import json, re, urllib.parse
from mirror import ROOT, ORIGIN, fetch, location

routes=set(json.loads((ROOT/'routes.json').read_text()))
home=(ROOT/'reference.html').read_text(encoding='utf-8')
for href in re.findall(r'href=["\x27]([^"\x27]+)',home):
    u=urllib.parse.urlsplit(urllib.parse.urljoin(ORIGIN,href.replace('&amp;','&')))
    if u.hostname in ('www.amarisjewels.com','amarisjewels.com') and u.path.startswith(('/pages/','/collections/','/products/','/blogs/','/policies/')):
        routes.add(u.path)
failures=[]
for route in sorted(routes):
    if not location(route).exists():
        try: fetch(route)
        except Exception as e: failures.append({'path':route,'error':str(e)})
(ROOT/'routes.json').write_text(json.dumps(sorted(routes),indent=2))
metas=[json.loads(p.read_text()) for p in (ROOT/'storefront').glob('*.json')]
report={'routes':len(routes),'cached_routes':sum(location(p).exists() for p in routes),'cached_responses':len(metas),'cached_assets':sum(not m['path'] in routes for m in metas),'unavailable_pages':failures,'asset_mode':'Theme files and homepage assets cached; additional product imagery and query variants cached on demand.'}
(ROOT/'capture-report.json').write_text(json.dumps(report,indent=2))
(ROOT/'page-capture-report.json').write_text(json.dumps({'routes':len(routes),'cached_routes':report['cached_routes'],'unavailable_pages':failures},indent=2))
print(json.dumps(report,indent=2),flush=True)
