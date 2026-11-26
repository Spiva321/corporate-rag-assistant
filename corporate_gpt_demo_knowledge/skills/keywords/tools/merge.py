#!/usr/bin/env python3
"""One table per topic: YouTube suggestion rank × Wordstat broad/exact.

    python merge.py --topic "4 оплата" suggest_4.json ws_4.json --topic "7 карта" suggest_7.json ws_7.json > semantika.md

suggest_*.json — output of yt_suggest.py; ws_*.json — output of ws.py --json.
Sorted by broad frequency (SEO = охват: broad counts every tail that contains the phrase).
Exact shows how much of the broad is the phrase itself — if broad is big but the tails are
someone else's intent (например «как сделать сайт» → «...на тильде»), the number is not ours.
"""
import json, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # cp1251-консоль Windows роняет print кириллицы


def fmt(n):
    return "—" if n is None else f"{n:,}".replace(",", " ")


def main(argv):
    out, i = [], 0
    while i < len(argv):
        if argv[i] != "--topic":
            sys.exit("usage: --topic NAME suggest.json ws.json [...]")
        name, sj, wj = argv[i + 1], argv[i + 2], argv[i + 3]
        i += 4
        sug = json.load(open(sj, encoding="utf-8"))
        ws = json.load(open(wj, encoding="utf-8"))
        rows = []
        for p in set(sug) | set(ws):
            rows.append((p, sug.get(p, {}).get("rank"), ws.get(p, {}).get("broad"), ws.get(p, {}).get("exact")))
        rows.sort(key=lambda r: -(r[2] or 0))
        out += ["## " + name, "",
                "| Фраза | Место в подсказках YouTube | Вордстат широкая | точная |",
                "|---|---|---|---|"]
        out += ["| %s | %s | %s | %s |" % (p, r or "—", fmt(b), fmt(e)) for p, r, b, e in rows]
        out.append("")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
