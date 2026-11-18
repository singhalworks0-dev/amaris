"""Retry uncached public pages at a conservative request rate."""
import concurrent.futures, json, threading, time, urllib.error
from mirror import fetch, location, ROOT

gate=threading.Lock()
last=0.0
def repair(path):
    global last
    if location(path).exists() and location(path).with_suffix('.json').exists(): return None
    for attempt in range(5):
        with gate:
            time.sleep(max(0,0.8-(time.monotonic()-last)))
            last=time.monotonic()
        try:
            fetch(path)
            return None
        except urllib.error.HTTPError as e:
            if e.code in (404,410): return {'path':path,'status':e.code}
            if attempt==4: return {'path':path,'error':str(e)}
            time.sleep(10*(attempt+1))
        except Exception as e:
            if attempt==4: return {'path':path,'error':str(e)}
            time.sleep(3)

if __name__=='__main__':
    routes=json.loads((ROOT/'routes.json').read_text())
    missing=[p for p in routes if not (location(p).exists() and location(p).with_suffix('.json').exists())]
    print(f'Retrying {len(missing)} uncached pages',flush=True)
    errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,result in enumerate(pool.map(repair,missing),1):
            if result: errors.append(result)
            if i%25==0: print(f'Retry {i}/{len(missing)}; unavailable {len(errors)}',flush=True)
    report={'routes':len(routes),'cached_routes':sum(location(p).exists() for p in routes),'unavailable_pages':errors}
    (ROOT/'page-capture-report.json').write_text(json.dumps(report,indent=2))
    capture=ROOT/'capture-report.json'
    if capture.exists():
        original=json.loads(capture.read_text())
        original['cached_routes']=report['cached_routes']
        original['failures']=[f for f in original['failures'] if not location(f['path']).exists()]
        original['page_retry_complete']=True
        capture.write_text(json.dumps(original,indent=2))
    print(json.dumps(report),flush=True)
