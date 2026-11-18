# Finance News Briefing

Research financial news on the web for a specific subject and get a short, source-linked briefing in your language.

## What it does

- Turns a request ("Morgenbriefing Schweiz", "news on NVDA this week", "why did UBS drop?") into a concrete scope: subject, time window, region, language
- Collects news from built-in web search and page fetching, plus a bundled RSS/Atom headline fetcher (Bloomberg, CNBC, MarketWatch, NZZ, finews.ch, tagesschau, Fed, ECB, CoinDesk, Google News search in any language, Yahoo Finance ticker headlines)
- Checks the news: every figure traced to a dated source, key numbers cross-checked, primary sources preferred, rumors and opinions attributed, duplicates merged
- Adds a market snapshot (indices, FX, commodities, or the stock's own move) via yfinance when available
- Writes a skimmable briefing that leads with the essentials, has inline source links and timestamps, lists dated upcoming events, and notes coverage gaps

The model does the summarizing itself; no external LLM, API key, or account is needed.

## Triggers

`morning market briefing`, `what's moving markets today`, `news on NVDA`, `fasse mir die News zu Nestlé zusammen`, `why did UBS shares fall`, `SNB news`, `Fed decision recap`, `oil price news this week`, `crypto news today`, `Börsen-News Schweiz`, `watchlist news digest`

## Prerequisites

- Built-in web search and fetch tools (any modern agent host)
- Optional: Python 3.9+ for `scripts/fetch_feeds.py` (standard library only, no installs)
- Optional: `yfinance` for the market snapshot

## Platform

- **Claude Code / Codex / other CLI agents**: full functionality (web search + feed fetcher + yfinance)
- **Claude.ai**: web search path only; the feed fetcher and yfinance need shell and network access

## Setup

None. The skill checks at load time whether Python, the news feeds, and yfinance are reachable and picks the methods that work.

## Usage examples

```bash
# Feed fetcher on its own (run from the skill directory)
python3 scripts/fetch_feeds.py --list
python3 scripts/fetch_feeds.py --group ch --group central-banks --hours 24
python3 scripts/fetch_feeds.py --ticker NESN.SW --search "Nestlé" --lang de --country CH --hours 72
python3 scripts/fetch_feeds.py --group global --keyword tariff --format json
```

Exit code 0 means at least one feed answered and 2 means all feeds failed (the skill then falls back to web search). Per-feed status goes to stderr.

## Reference Files

- `references/search-playbook.md`: query templates, search operators, multilingual search, primary-source locations, edge cases
- `references/sources.md`: source quality tiers, bundled feed catalog (verified 2026-11-18), recommended outlets by topic
- `scripts/fetch_feeds.py`: RSS/Atom fetcher with groups, Google News search, Yahoo ticker feeds, filters, dedupe, text/JSON output

## Maintenance notes

- Feed URLs were verified on 2026-11-18. Yahoo's general `news/rssindex` feed was dead (404) and is not included; the per-ticker Yahoo headline feed works.
- When a feed breaks, update `FEEDS` in `scripts/fetch_feeds.py` and the catalog table in `references/sources.md` together.
- Inspired by the OpenClaw `finance-news` skill, rebuilt for Claude Code: no Gemini/OpenClaw dependency, no messaging delivery, and summarization done by the host model.
