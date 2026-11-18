# Search Playbook

How to find the right financial news fast and confirm it. Use these patterns with the host's web search tool and with `scripts/fetch_feeds.py --search`.

## Query Templates by Request Type

Replace the placeholders and keep queries specific. Two or three sharp queries beat one vague one.

| Request | Web search queries (illustrative) | Feed fetcher |
|---|---|---|
| Market briefing | `stock market today <date>`, `Börse Zürich SMI heute`, `DAX Schluss <date>`, `Wall Street close <date>` | `--group <region> --group central-banks` |
| Company news | `"<Company>" news`, `"<Company>" shares`, `"<Company>" Aktie`, `"<Company>" press release <month year>` | `--ticker <SYM> --search "<Company>"` |
| Why did it move | `"<Company>" shares fall OR drop OR jump why`, `"<Company>" Aktie bricht ein Grund`, `<ticker> stock down <date>` | `--ticker <SYM> --hours 24` |
| Earnings reaction | `"<Company>" quarterly results guidance`, `"<Company>" Q3 <year> results` | `--search "<Company> results"` |
| Central bank | `SNB Zinsentscheid <month year>`, `FOMC statement <month year>`, `ECB monetary policy decision <date>` | `--group central-banks` |
| Macro data | `US CPI <month year> release`, `Schweiz Teuerung <Monat Jahr> BFS`, `Eurozone inflation flash <month>` | `--search "CPI inflation"` |
| Commodity / FX | `Brent crude price today why`, `gold price record <month>`, `Franken Euro Kurs aktuell` | `--keyword oil --keyword Öl` |
| Sector / theme | `semiconductor stocks <theme> <month year>`, `Schweizer Banken Regulierung Eigenkapital <year>` | `--search "<theme>"` with `--lang`/`--country` |
| Crypto | `bitcoin price today why`, `<token> ETF flows <date>` | `--group crypto` |

Always put the current year (and month for fast-moving topics) into queries; otherwise search engines surface old, well-linked articles.

## Search Operators

| Operator | Use |
|---|---|
| `"exact phrase"` | Company names with common words ("Swiss Re", "Partners Group") |
| `site:sec.gov`, `site:six-group.com`, `site:snb.ch` | Jump straight to primary sources |
| `site:reuters.com OR site:bloomberg.com` | Restrict to first-tier outlets |
| `-site:<domain>` | Drop a noisy aggregator |
| `when:1d` / `when:7d` (Google News feed via `--search`) | Hard time filter; the fetcher adds it from `--hours` |

## Searching in Several Languages

Local outlets often break local stories first, and international outlets often break the international angle. For a Swiss or German company, search in German and in English. For a Swiss company with Romandie relevance, add French (`"<Société>" bourse`). Pass `--lang de --country CH`, `--lang fr --country CH`, or `--lang en --country US` to the fetcher's Google News search to get the matching regional edition.

Summarize in the user's language no matter which language the source used; keep direct quotes in the original language with a translation when they matter.

## Where Primary Sources Live

| What | Where |
|---|---|
| US company filings (8-K, 10-Q, 10-K) | SEC EDGAR full-text search at `sec.gov/edgar/search/`, or a company's filing list at `sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<ticker>` |
| Swiss ad hoc announcements | Company investor relations "media releases" page; SIX Exchange Regulation publications |
| EU issuer announcements | Company IR page; national officially appointed mechanisms |
| Company results and guidance | Investor relations: results press release and presentation PDF |
| Fed | `federalreserve.gov` press releases, FOMC statements and minutes |
| ECB | `ecb.europa.eu` press releases, monetary policy decisions |
| SNB | `snb.ch` press releases and monetary policy assessments |
| Swiss statistics (CPI, GDP, labor market) | Swiss Federal Statistical Office (BFS/FSO), SECO |
| US statistics | BLS (CPI, jobs), BEA (GDP, PCE) |
| Eurozone statistics | Eurostat |

When a story rests on a filing or official release, link the primary document next to the press coverage.

## Confirming a Story

1. Find the earliest credible report (a wire or the primary release).
2. Confirm the key figure in a second independent source or the primary document.
3. Check whether there has been an update since then: a correction, a company statement, or a rebound in the share price.
4. Attribute anything unconfirmed ("Bloomberg reports, citing people familiar with the matter...").

## Edge Cases

- **Ticker ambiguity**: the same symbol can mean different companies on different exchanges. Use the exchange suffix (`.SW` SIX Swiss, `.DE` Xetra, `.PA` Paris, `.L` London, none for US) and confirm with the company name.
- **Dual listings**: UBS, Novartis, and others trade in Zurich and New York (ADR). Report the move on the home exchange, in its currency, unless the user asks otherwise.
- **Weekends and holidays**: if the window has no trading session, report the last session's close and say so. Swiss, German, and US holidays differ.
- **Time zones**: US news after 22:00 CET often lands "tomorrow" for European readers. Convert times to the user's zone and label them.
- **Paywalls** (WSJ, FT, Bloomberg, NZZ, Handelsblatt): use the headline and the visible snippet, say the article is paywalled, and look for free coverage of the same facts (wires, the company release). Don't fill gaps with guesses.
- **Google News links** are redirects. Prefer the publisher's own URL when you open the article, and cite the publisher, not Google News.
- **Same-day news missing from web search**: search indexes lag behind news. If a query for today returns only older items, switch to the Google News feed (`--search "<topic>" --hours 24`) or fetch the outlet's live page (for example the daily market close report or live ticker) instead of concluding that nothing happened.
- **Breaking news**: early reports are often revised. Say "early reports" and give the time.
- **Prediction or opinion pieces dressed as news** ("X stock could double"): skip them, or label them as opinion if they are relevant.
- **Nothing found**: say so, give the window you searched, and mention the latest relevant item with its date.
