#!/usr/bin/env python3
"""Yandex Wordstat frequencies via Yandex Cloud Search API v2 (topRequests), your own key.

    python ws.py "чат gpt в россии" "подписка чат гпт"            # broad (все хвосты и словоформы)
    python ws.py --exact "чат gpt в россии"                        # точная фраза: "..."
    python ws.py --file phrases.txt --both                         # broad + exact
    python ws.py --region 213 ...                                  # 225 Россия (default), 213 Москва
    python ws.py --top 20 "как выложить видео на ютуб"             # + 20 самых частых хвостов фразы

Keys come from .env next to the skill (one level above tools/) or from the environment:
    YC_API_KEY=...      API key of a Yandex Cloud service account
    YC_FOLDER_ID=...    ID of the Yandex Cloud folder
See README.md for where to get them.

Every number is cached in ../data/ws_cache.json with the date — repeated runs do not spend quota.
Quota (09.2026): about 100 requests/hour, one phrase = one request. On HTTP 429 the script stops
and tells how many phrases are left; rerun later, cached ones are skipped.
Operators work through the API (checked 28.09.2026): "фраза" = exact, !слово = exact form.
Only standard library, Python 3.8+.
"""
import argparse, datetime, json, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "data", "ws_cache.json")
URL = "https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests"
PAUSE = 0.3  # seconds between requests: the API also limits requests per second

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # cp1251-консоль Windows роняет print кириллицы
    sys.stderr.reconfigure(encoding="utf-8")


def load_env():
    """KEY=VALUE lines from .env (skill root, then current dir). Real env vars win."""
    for path in (os.path.join(ROOT, ".env"), os.path.join(os.getcwd(), ".env")):
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8-sig"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    key, folder = os.environ.get("YC_API_KEY"), os.environ.get("YC_FOLDER_ID")
    if not key or not folder:
        sys.exit("Нет YC_API_KEY / YC_FOLDER_ID. Скопируй .env.example в .env и впиши ключи (README.md).")
    return key, folder


def load():
    try:
        return json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        return {}


def save(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(c, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def key(phrase, region):
    return "%s|%s" % (region, phrase)


def top_requests(phrase, region, api_key, folder, num=1):
    """One API call. Returns (totalCount, [(phrase, count), ...]). Raises HTTPError."""
    body = json.dumps({"phrase": phrase, "numPhrases": max(1, num), "regions": [str(region)],
                       "devices": ["DEVICE_ALL"], "folderId": folder}).encode("utf-8")
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": "Api-Key " + api_key, "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=30))
    # counts come as strings in the response
    tails = [(x.get("phrase", ""), int(x.get("count", 0) or 0)) for x in r.get("results", [])]
    # "associations" in the same response are semantic noise — never used for keywords
    return int(r.get("totalCount", 0) or 0), tails


def fetch(phrases, region, api_key, folder):
    """Returns {phrase: total} and the phrases not fetched because of the quota (429)."""
    got = {}
    for i, q in enumerate(phrases):
        try:
            got[q], _ = top_requests(q, region, api_key, folder)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return got, phrases[i:]
            print('ERR "%s" %s %s' % (q, e.code, e.read().decode("utf-8", "replace")[:200]), file=sys.stderr)
            if e.code in (401, 403):
                sys.exit("Ключ не подошёл (%s): проверь YC_API_KEY, YC_FOLDER_ID и роль сервисного аккаунта (README.md)." % e.code)
        except Exception as e:
            print('ERR "%s" %s' % (q, e), file=sys.stderr)
        time.sleep(PAUSE)
    return got, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phrases", nargs="*")
    ap.add_argument("--file")
    ap.add_argument("--exact", action="store_true")
    ap.add_argument("--both", action="store_true")
    ap.add_argument("--region", default="225")
    ap.add_argument("--top", type=int, default=0, help="also print N most frequent tails (not cached, costs 1 request per phrase)")
    ap.add_argument("--json", help="write {phrase: {broad, exact}} here")
    a = ap.parse_args()

    base = list(a.phrases)
    if a.file:
        base += [l.strip() for l in open(a.file, encoding="utf-8-sig") if l.strip()]
    base = list(dict.fromkeys(p.replace("\r", "").lower().strip() for p in base))  # \r из Windows-файлов
    if not base:
        ap.error("нет фраз")
    wanted = []
    for p in base:
        if a.both or not a.exact:
            wanted.append(p)
        if a.both or a.exact:
            wanted.append('"%s"' % p)

    cache = load()
    todo = [q for q in wanted if key(q, a.region) not in cache]
    api_key = folder = None
    if todo or a.top:
        api_key, folder = load_env()
    if todo:
        got, limited = fetch(todo, a.region, api_key, folder)
        today = datetime.date.today().isoformat()
        for q, n in got.items():
            cache[key(q, a.region)] = {"total": n, "date": today}
        save(cache)
        if limited:
            print("⚠ квота исчерпана (429): не снято %d фраз — перезапусти позже (снятое уже в кэше)" % len(limited),
                  file=sys.stderr)

    table = {}
    for p in base:
        b = cache.get(key(p, a.region), {}).get("total")
        e = cache.get(key('"%s"' % p, a.region), {}).get("total")
        table[p] = {"broad": b, "exact": e}
        print("%-50s broad=%-9s exact=%s" % (p, b if b is not None else "—", e if e is not None else "—"))
        if a.top:
            try:
                _, tails = top_requests(p, a.region, api_key, folder, a.top)
                for t, n in tails:
                    print("    %-46s %s" % (t, n))
                time.sleep(PAUSE)
            except Exception as err:
                print("    ERR хвосты: %s" % err, file=sys.stderr)
    if a.json:
        json.dump(table, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
