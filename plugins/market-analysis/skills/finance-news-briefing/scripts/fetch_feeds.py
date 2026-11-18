#!/usr/bin/env python3
"""Fetch finance headlines from RSS/Atom feeds, filter them, and print a digest.

Standard library only (Python 3.9+). Honors HTTPS_PROXY / HTTP_PROXY.

Examples:
  python3 fetch_feeds.py --list
  python3 fetch_feeds.py --group global --hours 24
  python3 fetch_feeds.py --group ch --keyword UBS --keyword SNB
  python3 fetch_feeds.py --search "Nestlé Aktie" --lang de --country CH --hours 48
  python3 fetch_feeds.py --ticker NVDA --ticker NESN.SW --format json

Status lines go to stderr: one FEED_OK / FEED_FAIL line per feed and a final
SUMMARY line. Exit code 0 when at least one feed answered, 2 when all failed
(the caller should then fall back to web search), 1 on bad arguments.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

USER_AGENT = "Mozilla/5.0 (compatible; finance-news-briefing/1.0)"
TIMEOUT_S = 10
MAX_BYTES = 3_000_000

# Feed catalog, verified reachable 2026-11-18. See references/sources.md.
FEEDS = {
    "bloomberg-markets": ("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss", "global", "en"),
    "cnbc-top": ("CNBC Top News", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "us", "en"),
    "marketwatch-top": ("MarketWatch Top Stories", "https://feeds.content.dowjones.io/public/rss/mw_topstories", "us", "en"),
    "fed-press": ("Federal Reserve press releases", "https://www.federalreserve.gov/feeds/press_all.xml", "central-banks", "en"),
    "ecb-press": ("ECB press, speeches, publications", "https://www.ecb.europa.eu/rss/press.html", "central-banks", "en"),
    "nzz-wirtschaft": ("NZZ Wirtschaft", "https://www.nzz.ch/wirtschaft.rss", "ch", "de"),
    "finews-ch": ("finews.ch", "https://www.finews.ch/news?format=feed&type=rss", "ch", "de"),
    "tagesschau-wirtschaft": ("tagesschau Wirtschaft", "https://www.tagesschau.de/wirtschaft/index~rss2.xml", "de", "de"),
    "coindesk": ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/", "crypto", "en"),
}

GROUPS = {
    "global": ["bloomberg-markets", "cnbc-top", "marketwatch-top"],
    "us": ["cnbc-top", "marketwatch-top", "bloomberg-markets"],
    "europe": ["nzz-wirtschaft", "tagesschau-wirtschaft", "ecb-press", "bloomberg-markets"],
    "ch": ["nzz-wirtschaft", "finews-ch"],
    "de": ["tagesschau-wirtschaft"],
    "central-banks": ["fed-press", "ecb-press"],
    "crypto": ["coindesk"],
}
GROUPS["all"] = list(FEEDS)


def google_news_url(query: str, lang: str, country: str, hours: int) -> str:
    days = max(1, -(-hours // 24))  # Google News accepts when:Nd; round up
    q = f"{query} when:{days}d"
    hl = lang if "-" in lang else f"{lang}-{country}" if lang != "en" else "en-US"
    params = {"q": q, "hl": hl, "gl": country, "ceid": f"{country}:{lang.split('-')[0]}"}
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)


def yahoo_ticker_url(symbol: str) -> str:
    params = {"s": symbol, "region": "US", "lang": "en-US"}
    return "https://feeds.finance.yahoo.com/rss/2.0/headline?" + urllib.parse.urlencode(params)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _child(el: ET.Element, *names: str) -> ET.Element | None:
    for child in el:
        if _local(child.tag) in names:
            return child
    return None


def _text(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def _clean(raw: str, limit: int = 300) -> str:
    txt = re.sub(r"<[^>]+>", " ", html.unescape(raw or ""))
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt if len(txt) <= limit else txt[: limit - 1].rstrip() + "…"


def parse_date(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_feed(data: bytes, feed_name: str) -> list[dict]:
    """Parse RSS 2.0, RSS 1.0/RDF, or Atom into a list of item dicts."""
    root = ET.fromstring(data)
    items = [el for el in root.iter() if _local(el.tag) in ("item", "entry")]
    out = []
    for it in items:
        title = _clean(_text(_child(it, "title")), 250)
        if not title:
            continue
        link_el = _child(it, "link")
        link = _text(link_el) or (link_el.get("href", "") if link_el is not None else "")
        published = parse_date(
            _text(_child(it, "pubDate", "published", "updated", "date", "issued"))
        )
        summary = _clean(_text(_child(it, "description", "summary", "content", "encoded")))
        source_el = _child(it, "source")
        source = _text(source_el) or feed_name
        # Google News appends " - Publisher" to titles; drop it when it repeats the source.
        if source_el is not None and title.endswith(f" - {source}"):
            title = title[: -len(source) - 3]
        if summary.startswith(title):  # many feeds repeat the headline as summary
            summary = summary[len(title):].strip(" -–:")
        out.append({
            "published": published.isoformat(timespec="minutes") if published else None,
            "source": source,
            "title": title,
            "summary": summary,
            "link": link.strip(),
            "feed": feed_name,
        })
    return out


def fetch(key: str, name: str, url: str) -> tuple[str, list[dict] | None, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            data = resp.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            return key, None, "response too large"
        return key, parse_feed(data, name), ""
    except ET.ParseError as exc:
        return key, None, f"not a valid feed ({exc})"
    except Exception as exc:  # network errors vary widely by platform/proxy
        return key, None, f"{type(exc).__name__}: {exc}"[:200]


def _norm(title: str) -> str:
    return re.sub(r"[^a-z0-9äöüéèàç]+", "", title.lower())[:80]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list feeds and groups, then exit")
    ap.add_argument("--group", action="append", default=[], choices=sorted(GROUPS), help="feed group (repeatable)")
    ap.add_argument("--feed", action="append", default=[], help="feed key from --list (repeatable)")
    ap.add_argument("--search", action="append", default=[], help="Google News search query (repeatable)")
    ap.add_argument("--ticker", action="append", default=[], help="Yahoo Finance ticker headlines, e.g. AAPL, NESN.SW (repeatable)")
    ap.add_argument("--lang", default="en", help="language for --search, e.g. en, de, fr (default en)")
    ap.add_argument("--country", default="US", help="country for --search, e.g. US, CH, DE (default US)")
    ap.add_argument("--keyword", action="append", default=[], help="keep only items mentioning any keyword (case-insensitive, repeatable)")
    ap.add_argument("--hours", type=int, default=24, help="look-back window in hours (default 24)")
    ap.add_argument("--limit", type=int, default=40, help="max items to print (default 40)")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args(argv)

    if args.list:
        for key, (name, url, region, lang) in FEEDS.items():
            print(f"{key:24} {region:14} {lang}  {name}  {url}")
        print()
        for g, keys in GROUPS.items():
            print(f"group {g:14} {', '.join(keys)}")
        return 0

    jobs: dict[str, tuple[str, str]] = {}
    for g in args.group:
        for key in GROUPS[g]:
            jobs[key] = FEEDS[key][:2]
    for key in args.feed:
        if key not in FEEDS:
            ap.error(f"unknown feed '{key}' (see --list)")
        jobs[key] = FEEDS[key][:2]
    for q in args.search:
        jobs[f"gnews:{q}"] = (f"Google News: {q}", google_news_url(q, args.lang, args.country.upper(), args.hours))
    for sym in args.ticker:
        jobs[f"yahoo:{sym.upper()}"] = (f"Yahoo Finance: {sym.upper()}", yahoo_ticker_url(sym.upper()))
    if not jobs:
        jobs = {k: FEEDS[k][:2] for k in GROUPS["global"]}

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda kv: fetch(kv[0], *kv[1]), jobs.items()))

    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    keywords = [k.lower() for k in args.keyword]
    ok = failed = 0
    seen: set[str] = set()
    items: list[dict] = []
    for key, feed_items, err in results:
        if feed_items is None:
            failed += 1
            print(f"FEED_FAIL {key}: {err}", file=sys.stderr)
            continue
        ok += 1
        print(f"FEED_OK {key}: {len(feed_items)} items", file=sys.stderr)
        for it in feed_items:
            if it["published"] and datetime.fromisoformat(it["published"]) < cutoff:
                continue
            if keywords and not any(k in f"{it['title']} {it['summary']}".lower() for k in keywords):
                continue
            n = _norm(it["title"])
            if n in seen:
                continue
            seen.add(n)
            items.append(it)

    # Newest first; undated items last.
    items.sort(key=lambda i: i["published"] or "", reverse=True)
    items = items[: args.limit]

    if args.format == "json":
        print(json.dumps(items, ensure_ascii=False, indent=1))
    else:
        for it in items:
            when = it["published"].replace("T", " ").replace("+00:00", "Z") if it["published"] else "undated"
            print(f"[{when}] {it['source']}: {it['title']}")
            if it["summary"]:
                print(f"    {it['summary']}")
            print(f"    {it['link']}")
    print(f"SUMMARY feeds_ok={ok} feeds_failed={failed} items={len(items)} window={args.hours}h "
          f"fetched_at={datetime.now(timezone.utc).isoformat(timespec='minutes')}", file=sys.stderr)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
