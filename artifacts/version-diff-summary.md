# Version diff summary: 1.1.1 to 1.2.0

The two releases were unpacked and compared file by file to confirm that the published release notes matched the change actually shipped.

This document records the **summary** of that comparison. Raw source diffs are not reproduced here, since Sahne Plus is proprietary software and a line-by-line diff would republish its source.

## Files compared

The application archive contains 29 files in both releases. Hash comparison across the two trees:

| Status | Count |
|---|---|
| Identical | 20 |
| Changed | 9 |

Identical includes all five bundled fonts and their licence files, both brand SVGs, both PNG assets, the stylesheets, `overlay.html`, `overlay.js`, and `preload.js`.

## Changed files

| File | Nature of change |
|---|---|
| `package.json` | version string 1.1.1 to 1.2.0 |
| `LICENSE.txt` | added baha24 to the third-party disclaimer list |
| `electron/main.js` | added `baha24.com` to the external-URL allow-list |
| `server/server.js` | exchange-rate source rework (see below) |
| `public/app.js` | UI label now shows which rate source is live; setup-card condition changed |
| `public/app.html` | rate card heading, minimum interval input, proxy label, About text |
| `public/legal/PRIVACY.md` | baha24 added to the data-flow table |
| `public/legal/TERMS.md` | baha24 added to disclaimers |
| `public/legal/THIRD_PARTY_NOTICES.md` | baha24 entry |

## The substantive change

All functional change is confined to the exchange-rate subsystem.

**Before (1.1.1)** — bonbast.com only, scraped from an HTML page plus a token-extraction POST, minimum refresh interval 5 minutes, default 10 minutes.

**After (1.2.0)** — baha24.com public JSON API as the primary source, bonbast.com retained as a rate-limited fallback, minimum interval lowered to 1 minute, default 2 minutes.

Supporting changes:

- a new rate-fetch function for baha24, parsing a JSON array or `{data: [...]}` envelope, locating the USD entry, and validating the sell value is within 1000 to 1e9 before accepting it
- a `minBonbastInterval` of 5 minutes added, so a failing baha24 does not cause repeated scraping of bonbast
- `rateSource` added to the state object so the UI can label which source produced the current rate
- error messages generalised from bonbast-specific to rate-source-neutral

## The UI change

The first-run setup card condition changed from checking whether the legacy plaintext `secret_id` field was present in config, to checking a `kickbot.configured` flag supplied by the server.

This corresponds to the release note "the first-run setup card no longer stays visible after KickBot is connected." The old condition could not be satisfied once the credential moved to DPAPI-encrypted storage and stopped being returned to the UI, which is why the card remained visible after connecting.

## Confirmed clean

- No new network destination beyond baha24.com, which is documented.
- No new dangerous API usage.
- No change to IPC handlers, the preload bridge, or the renderer security configuration.
- No change to the alert queue, media selection, or playback logic.
- No obfuscation introduced; the new code is plain, commented, and consistent with the surrounding style.

## Assessment

The release notes accurately describe the shipped change. The diff is small, coherent, and contains nothing unexplained.

Notably, the two releases were published on the same day, roughly eight hours apart. That is consistent with an active development session, and the diff supports it — this is a focused change, not a rebuild.
