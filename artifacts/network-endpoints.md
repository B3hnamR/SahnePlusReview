# Network endpoints

Every outbound network destination in Sahne Plus 1.2.0, enumerated by searching the full application source for URL literals, `WebSocket` constructions, and `fetch`/`https.request` call sites.

**Result: seven destinations. No telemetry, no analytics, no crash reporting, no update checks, no CDN or font loads.**

## Endpoints

| # | Endpoint | Protocol | Purpose |
|---|---|---|---|
| 1 | `wss://kickbot.live/ws` | WebSocket | donation event stream; subscribes to channel `tipping_<streamer_id>` |
| 2 | `https://widgets.kickbot.com` | HTTPS | `capture_tip` (payment confirmation), `tip_queue_sync`, widget metadata, streamer id resolution |
| 3 | `wss://ws-us2.pusher.com/app/32cbd69e4b950bf97679?...` | WebSocket | Kick public chat feed — subscription and gift-subscription events |
| 4 | `https://kick.com/api/v2/channels/<slug>` | HTTPS | resolves a channel slug to its chatroom id |
| 5 | `https://baha24.com/api/v1/price` | HTTPS | USD to toman rate (primary source) |
| 6 | `https://www.bonbast.com/` | HTTPS | USD to toman rate (scraped fallback, rate-limited to once per 5 minutes) |
| 7 | `ws://127.0.0.1:13376` | WebSocket | Meld Studio local API — reloads the Browser Source layer if it disconnects |

## Loopback listener

The application runs an HTTP server bound explicitly to `127.0.0.1`. It does not bind `0.0.0.0` and is not reachable from other machines.

| Route | Purpose |
|---|---|
| `/` | controller window |
| `/overlay` | Browser Source for OBS / Meld Studio |
| `/events` | Server-Sent Events push channel (roles: `overlay`, `admin`, `preview`) |
| `/api/*` | control API |
| `/media/*` | imported alert media |
| `/fonts/`, `/brand/`, `/legal/` | bundled static assets |

## Hosts explicitly absent

The following were searched for and are **not** present anywhere in the application:

- Google Fonts, Google Analytics, or any Google endpoint
- Any CDN (jsDelivr, unpkg, cdnjs, Cloudflare)
- Sentry, Bugsnag, Rollbar, or any crash-reporting service
- Any analytics or telemetry SDK
- Any update-check or auto-update endpoint
- Any paste, webhook, or generic exfiltration destination

## Third-party page loads

The Browser Source page loads KickBot TTS audio and, when a donation carries one, a GIF URL supplied by KickBot. Its Content-Security-Policy restricts this:

```
default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self';
img-src 'self' https:; media-src 'self' https:; connect-src 'self';
base-uri 'none'; form-action 'none'; frame-ancestors 'self'
```

All fonts are bundled locally. Nothing is loaded from an external CDN.

## Proxy behaviour

If the user configures a proxy, it is used for the Kick channel lookup and the exchange-rate requests. The KickBot connection does not use the proxy. This matches the privacy documentation.

## Method

Sources searched: all `.js`, `.html`, `.css`, and `.json` files in the application archive, plus the Electron main process and preload script. Patterns: `https?://` and `wss?://` literals, `new WebSocket(`, `fetch(`, `https.request(`, `url(` in stylesheets, and `src=` / `href=` attributes.

Reproduce with the endpoint enumeration described in the top-level README.
