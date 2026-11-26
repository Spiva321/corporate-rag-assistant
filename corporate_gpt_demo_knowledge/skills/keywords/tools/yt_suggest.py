#!/usr/bin/env python3
"""YouTube autocomplete: what people actually type in YouTube search.

    python yt_suggest.py --out topic.json "чат gpt в россии" "как оплатить чат gpt"
    python yt_suggest.py --alphabet --out topic.json "codex"      # + seed а..я / a..z

Writes {phrase: {"rank": best position (1 = first suggestion), "seed": seed}}.
Rank is the only popularity signal YouTube gives — it has no public search volume.
Region/language default to Russia/Russian (--gl/--hl to change).
"""
import argparse, json, re, sys, time, urllib.parse, urllib.request

RU = "абвгдеёжзийклмнопрстуфхцчшщэюя"
EN = "abcdefghijklmnopqrstuvwxyz"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # cp1251-консоль Windows роняет print кириллицы


def suggest(q, hl, gl):
    url = ("https://suggestqueries-clients6.youtube.com/complete/search?client=youtube&ds=yt"
           "&hl=%s&gl=%s&q=%s" % (hl, gl, urllib.parse.quote(q)))
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                                 timeout=15).read().decode("utf-8", "replace")
    m = re.search(r"\((\[.*\])\)\s*$", raw, re.S)
    return [x[0].strip().lower() for x in json.loads(m.group(1) if m else raw)[1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seeds", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--alphabet", action="store_true", help="also query 'seed а', 'seed б', ... (slow, ~60 calls/seed)")
    ap.add_argument("--hl", default="ru")
    ap.add_argument("--gl", default="RU")
    a = ap.parse_args()

    res = {}
    for seed in a.seeds:
        queries = [seed] + ([seed + " " + ch for ch in RU + EN] if a.alphabet else [])
        for q in queries:
            try:
                got = suggest(q, a.hl, a.gl)
            except Exception as e:
                print("ERR", q, e, file=sys.stderr)
                continue
            for rank, p in enumerate(got, 1):
                if p not in res or rank < res[p]["rank"]:
                    res[p] = {"rank": rank, "seed": seed}
            time.sleep(0.3)
    json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%d phrases -> %s" % (len(res), a.out))


if __name__ == "__main__":
    main()
