# Sources

Which sources to trust for what, and the feeds bundled with `scripts/fetch_feeds.py`.

## Quality Tiers

| Tier | Examples | How to use |
|---|---|---|
| 1. Primary | Company press releases and filings, central banks, statistics offices, exchanges, regulators (SEC, FINMA, BaFin) | The authority on facts and figures; link it whenever a story rests on it |
| 2. Wires and first-tier financial press | Reuters, Bloomberg, Dow Jones/WSJ, FT, AP, AWP (Switzerland), dpa-AFX | Fast and edited; fine as the main source for a story; attribute exclusives |
| 3. Major general and regional outlets | CNBC, MarketWatch, NZZ, finews.ch, Handelsblatt, FAZ, tagesschau, Les Echos | Good context and local angles; cross-check figures |
| 4. Aggregators, data portals, blogs | Yahoo Finance news, Google News, finanzen.net, cash.ch, Seeking Alpha, Substack | Good for discovery; confirm in tier 1-3 before stating facts |
| 5. Social media and forums | X/Twitter, Reddit, Telegram, Discord | Sentiment and rumors only, always labeled; use finance-sentiment or twitter-reader for this |

## Bundled Feed Catalog

Verified reachable on 2026-11-18. Feed URLs change; if one fails repeatedly (`FEED_FAIL`), fall back to web search for that outlet and update `FEEDS` in `scripts/fetch_feeds.py`.

| Key | Outlet | Region / group | Language |
|---|---|---|---|
| `bloomberg-markets` | Bloomberg Markets | global, us, europe | en |
| `cnbc-top` | CNBC Top News | us, global | en |
| `marketwatch-top` | MarketWatch Top Stories | us, global | en |
| `fed-press` | Federal Reserve press releases | central-banks | en |
| `ecb-press` | ECB press releases, speeches, publications | central-banks, europe | en |
| `nzz-wirtschaft` | NZZ Wirtschaft | ch, europe | de |
| `finews-ch` | finews.ch (Swiss financial industry) | ch | de |
| `tagesschau-wirtschaft` | tagesschau Wirtschaft | de, europe | de |
| `coindesk` | CoinDesk | crypto | en |

Dynamic feeds (built from arguments):

| Flag | Source | Notes |
|---|---|---|
| `--search "<query>"` | Google News RSS search | Any topic, any language; set `--lang` and `--country` for the regional edition; returns publisher names in `source` |
| `--ticker <SYM>` | Yahoo Finance headline feed per ticker | Works for US and suffixed tickers (`NESN.SW`, `SAP.DE`); coverage is thinner outside the US |

Feeds checked and left out (2026-11-18): Yahoo Finance general `news/rssindex` (404), cash.ch (no stable public feed URL found). The SNB has no verified feed here, so use `site:snb.ch` in web search.

## Recommended Outlets by Topic

| Topic | Look here first |
|---|---|
| Swiss companies and market | Company IR, SIX, FINMA; AWP wire reports (republished on finanzen.ch and cash.ch, e.g. the daily "Aktien Schweiz Schluss" close report), NZZ, finews.ch |
| German and euro area | Handelsblatt, FAZ, Börsen-Zeitung, tagesschau, ECB, Bundesbank, Destatis |
| US markets and companies | SEC EDGAR, Reuters, Bloomberg, WSJ, CNBC, MarketWatch |
| Central banks and rates | Fed, ECB, SNB, BoE, BoJ websites; Reuters for reaction |
| Commodities and energy | Reuters, Bloomberg, OPEC and IEA releases; hormuz-strait skill for Gulf shipping |
| Crypto | CoinDesk, The Block, exchange announcements; hyperliquid-reader for perp data |
| Startups and private markets | yc-reader and startup-analysis skills, TechCrunch, company blogs |

## Edge Cases

- **A feed returns items without dates**: the fetcher keeps them and lists them last as `undated`. Confirm the date in the article before using them.
- **A feed returns stale items**: some publishers cache feeds for hours. Cross-check the newest items against web search for very recent events.
- **Rate limiting or 403**: Google News and Yahoo occasionally throttle automated clients. Retry once later or switch to web search.
