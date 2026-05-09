# Stock Analysis (TIA) — E2E + SLA Architect Review

**Target**: `https://test.ktrading.tech/analysis/{TICKER}` (test VPS `147.93.27.80`)
**Tickers**: QSI, TOST, TMDX
**Date**: 2026-05-09
**SLA budget**: 30s end-to-end (per spec REQ-TIA Phase-1 contract)

---

## Executive summary

The TIA backend orchestrator and the SSE streaming pipeline both meet SLA — measured ~13s end-to-end through the public HTTPS path for QSI. **Three real issues were uncovered and two were fixed in this session**; the remainder are environmental or frontend-coupling problems with named owners.

| # | Severity | Component | Issue | Status |
|---|---|---|---|---|
| 1 | **P1** | aitradingnode `/api/analysis/[ticker]/stream` route | Sent hop-by-hop `Connection: keep-alive` header → Chrome aborts the HTTP/2 SSE response with `ERR_HTTP2_PROTOCOL_ERROR` (RFC 9113 §8.1.2.2 violation) | **Fixed** in source + hot-deployed to test VPS |
| 2 | **P1** | nginx test.ktrading.tech config | `/api/analysis/*` was served by the catch-all `location /` block with default `proxy_buffering on` → SSE chunks were buffered until size threshold, blocking SSE delivery to client | **Fixed** by adding dedicated `location /api/analysis/` block with `proxy_buffering off`, `proxy_hide_header Connection/Keep-Alive`, longer `proxy_read_timeout` |
| 3 | **P0** | Anthropic API account | Credit balance exhausted → every `ai_reasoning` step fails with `400 invalid_request_error: Your credit balance is too low`. Orchestrator gracefully degrades to `status: partial` and emits `final`, so SLA stays green, but the AI investment thesis is missing from every report | **Action required** — top up account or rotate API key |
| 4 | **P2** | aitradingnode `/api/watchlists` proxy | Returns 403 for `e2etest@ktrading.tech` admin user → react-query retry loop on the Stock Analysis page → page re-renders abort the in-flight `useAnalysisStream` consumer mid-stream | **Mitigated in tests** via Playwright route stub; **real fix needed** in app (decouple watchlist hook from analysis page) |
| 5 | **P2** | aitradingnode `useAnalysisStream` hook | `useEffect(() => () => cancel(), [cancel])` aborts the active fetch on every component unmount; component is sensitive to re-renders triggered by peripheral hooks. Already-arrived response bytes can be discarded if the React tree re-mounts the page wrapper | **Open** — needs a follow-up to retain stream state across remounts (e.g., move state to a context or only abort on explicit `start()` call) |
| 6 | **P2** | nginx 1.24 listener | Grafana subdomain on the same `:443 ssl http2` socket enables HTTP/2 socket-wide for **all** server names on this nginx 1.24 build. Test.ktrading.tech inadvertently negotiates h2 even though its `listen` directive omits `http2`. **Not** the cause of any failure (HTTP/2 SSE works fine after fixes #1+#2), but the implicit coupling is fragile | **Open** — tracked for follow-up. Either upgrade to nginx 1.25+ (per-server-block `http2 on;`) or move grafana to a separate listener |

---

## What we built

### Playwright project — `test-suite/e2e/tia/`

```
playwright.config.ts          # baseURL, timeouts, globalSetup, storageState
tests/global-setup.ts         # one-time login → writes storage-state.json
tests/helpers/auth.ts         # test creds (env-overridable)
tests/helpers/sla.ts          # per-test SlaSample + Playwright network listener
tests/stock-analysis.spec.ts  # 1 test per ticker; navigates /analysis/{T}, waits for recommendation tier, asserts SLA + section presence
tests/smoke.spec.ts           # diagnostic-only; verbose console+network logging
```

Run:

```bash
cd test-suite/e2e/tia
npm install                     # one-off
npx playwright install chromium # one-off
npx playwright test             # full spec (3 tests)
TIA_TICKERS=QSI npx playwright test  # single ticker
TIA_REQUIRE_REASONING=true npx playwright test  # fail when ai_reasoning degrades
```

Reports land in `playwright-report/` (HTML), `playwright-report/sla.json`, `playwright-report/sla.txt`, and per-test traces under `test-results/`.

---

## SLA evidence (collected via direct probes)

The E2E **SSE pipeline** was measured three ways. Numbers are wall-clock from the POST request to the `event: final` line.

| Path | Tool | Ticker | TTFB | Total | Events | Final | Notes |
|---|---|---|---|---|---|---|---|
| Internal: VPS → TIA `:8113` direct | curl over HTTP/1.1 | QSI | <100ms | **14.1s** | 28 | ✓ | matches `analysis.done duration_ms=14111` in TIA logs |
| Public HTTPS, HTTP/1.1 | curl `--max-time 35` | QSI | <500ms | **~13.0s** | 28 | ✓ | through nginx + Next.js proxy |
| Public HTTPS, HTTP/2 | Node `http2.connect()` | QSI | 96ms | **10.9s** | 28 | ✓ | bytes=8661, status=200, no protocol error after fix #1 |

**Stage breakdown** (from sse-starlette `step_status` events on the QSI run):

| Stage | Step | Status | Elapsed (start→done) |
|---|---|---|---|
| 1 | `price_data` | done | 14.1s |
| 1 | `technical_indicators` | done | 14.1s |
| 1 | `fundamentals` | done | 14.1s |
| 1 | `ml_predictions` | done | 14.1s |
| 1 | `news_sentiment` | done | 14.1s |
| 1 | `rag_evidence` | done | 14.1s |
| 1 | `sector_context` | done | 14.1s |
| 2 | `ai_reasoning` | **failed** | <0.5s (Anthropic 400 — billing) |

> Stage-1 fan-out blocks on the slowest underlying call (yfinance for fundamentals/news, RAG vector search, sector cache). All seven completed in ~14s wall-clock — they ran in parallel.

### Margin analysis vs the 30s SLA budget

- **Today (reasoning failed)**: ~14s — **53% under budget**
- **Projected when reasoning works**: 14s + ~10–15s Anthropic Claude → ~24–29s — **slim 1–6s margin**
- **p95 risk** (yfinance flakiness, cold sector cache, large RAG corpus): + 5–10s easily ⇒ p95 likely *over* 30s

---

## Improvement opportunities — ranked

| # | Effort | Impact | Recommendation |
|---|---|---|---|
| 1 | XS (creds top-up) | **HIGH** | **Top up Anthropic API credits** or rotate to a billed key. Without this the entire AI-thesis value-prop is dead — recommendations are computed from numerical signals only, with empty thesis cards |
| 2 | XS (PR ship) | **HIGH** | Land the Connection-header + abort-forwarding fix in `aitradingnode` repo (`feature/tia-page-redesign` branch already has the source change locally). Promote via the standard release-branch CD |
| 3 | S (PR + infra) | **HIGH** | Check the new nginx `location /api/analysis/` block into infra-as-code (`AITradingAPP/infra/nginx/test.ktrading.tech.conf` — does not exist today). Currently it lives on the VPS only and would be lost on next nginx config redeploy |
| 4 | S | **HIGH** | **Decouple `useWatchlistMeta` from the Stock Analysis page initial render**. Lazy-load it only when the user clicks "Add to watchlist". The current 403 retry loop tears down the SSE consumer and would also degrade real users any time the watchlist service is slow |
| 5 | M | **HIGH** | **Make `useAnalysisStream` resilient to component remounts**. Today the cleanup function aborts the in-flight fetch on every effect unmount. Options: lift state to a React context, persist the stream phase in URL/sessionStorage, or only abort on explicit user action (new ticker, retry button) — not on incidental re-renders |
| 6 | M | **MED** | **Add LLM fallback chain**. When Anthropic returns 4xx/5xx or a budget circuit-breaker fires, generate a template thesis from the structured signals (rule-based composition of trend + technicals + fundamentals into 3 paragraphs). Better than an empty card. Document the fallback in the report so users know |
| 7 | M | **MED** | **Server-side anonymous dedup cache** — already in spec at 75% hit-rate target. Verify it's wired and observable: emit `tia_cache_hit_ratio` metric. Big-cap tickers (AAPL, NVDA) should hit cache; QSI/TOST/TMDX rarely will |
| 8 | M | **MED** | **Pre-warm sector_context / correlation_cache** for the long tail. The orchestrator's `SectorPrecomputeJob` runs nightly at 02:00 UTC for the top 500 tickers — verify QSI/TOST/TMDX are in the universe (they were small-cap, may not be) so cold-cache cost doesn't dominate p95 |
| 9 | M | **MED** | **Per-stage Prometheus histograms** — `tia_analysis_duration_seconds{stage}` with buckets at 1, 2, 5, 10, 15, 25, 30s. Today the only metric is `analysis.done duration_ms` in structured logs — not graphed. Add a Grafana panel matching the SLA budget |
| 10 | S | **MED** | **CI gate: Playwright TIA E2E on every PR to release**. The new test-suite/e2e/tia/ workflow can run as a GitHub Action gating release-branch deploys. Requires VPS-side cookies for `e2etest@ktrading.tech` — already exists |
| 11 | M | **LOW** | **Move grafana off the shared `:443 ssl http2` socket** — either separate IP, separate port (e.g., `:8443`), or upgrade nginx to 1.25 for per-server-block `http2 on;`. Today h2 negotiation for the test domain depends on grafana's listener config — surprising and fragile |
| 12 | XS | **LOW** | **Drop `vary: RSC, Next-Router-State-Tree, …` from SSE responses**. Next.js auto-adds those for SSR routes; on a `text/event-stream` response they are pure overhead and confuse some intermediaries |

---

## Files changed in this session

### `aitradingnode/app/api/analysis/[ticker]/stream/route.ts` (source-controlled fix)

- Removed `Connection: keep-alive` from the SSE response headers (the actual root cause of `ERR_HTTP2_PROTOCOL_ERROR`)
- Added `export const dynamic = 'force-dynamic'` to defeat any accidental edge / static optimisation on the streaming route
- Documented the rationale in the file's docstring

> **Owner action**: open an aitradingnode PR from `feature/tia-page-redesign` (the change is already on disk on that branch)

### Test VPS hot-fixes (out-of-tree, reproduce in source via PR)

1. `/etc/nginx/sites-enabled/test.ktrading.tech` — added the `location /api/analysis/` block. Backup at `.bak.20260509_025154`. Diff:
   ```
   167a168,187
   >     location /api/analysis/ {
   >         proxy_pass http://localhost:3001;
   >         proxy_http_version 1.1;
   >         proxy_set_header Host $host;
   >         proxy_set_header X-Real-IP $remote_addr;
   >         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   >         proxy_set_header X-Forwarded-Proto $scheme;
   >         proxy_buffering off;
   >         proxy_cache off;
   >         proxy_read_timeout 90s;
   >         proxy_send_timeout 90s;
   >         chunked_transfer_encoding on;
   >         proxy_hide_header Connection;
   >         proxy_hide_header Keep-Alive;
   >     }
   ```
2. `/opt/ai-trading/aitradingnode-test/.next/server/` and `.../static/` — replaced with the rebuilt standalone bundle from this laptop. PM2 `aitradingnode-test` restarted.

### Playwright project — `test-suite/e2e/tia/` (new)

Self-contained, no impact on existing test-suite. Untracked under the WS5 branch; safe to commit on its own dedicated branch.

---

## Outstanding (intentional non-fixes from this session)

1. **The Anthropic credit issue** is not fixable from CLI — owner-level billing action.
2. **Frontend issues #4 and #5** (watchlist coupling + stream cancellation) need product/UX consideration. The Playwright tests now stub `/api/watchlists` so the SSE flow can be verified, but the bug is real and would degrade live users any time the watchlist service is unresponsive.
3. **The aitradingnode source PR** for the streaming-proxy fix is staged on the `feature/tia-page-redesign` branch but **not committed** — owner should review and PR via the standard `feature → development → release` flow.
4. **The nginx config diff** is live on the test VPS but **not** in source control. Will be lost on the next infra redeploy. Recommended: create `AITradingAPP/infra/nginx/test.ktrading.tech.conf` and check it in (the aitradingnode repo or a dedicated infra repo, depending on conventions).
