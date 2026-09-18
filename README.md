# Sahne Plus — Independent Code Review

An independent third-party review of the **Sahne Plus** Windows desktop application, version **1.2.0**, published for research and transparency.

> **Disclaimer**
> This review is independent. It is not affiliated with, endorsed by, sponsored by, or commissioned by **AmirEyZed**, the author of Sahne Plus. The product name is used descriptively to identify the software under review. No Sahne Plus source code, binaries, installers, or documentation are redistributed here — see [What this repository does not contain](#what-this-repository-does-not-contain).
>
> This is a **code review**, not a penetration test, not a malware analysis, and not a certification. Read the [scope limits](#what-was-not-reviewed) before drawing conclusions.

---

## Summary

| | |
|---|---|
| **Application** | Sahne Plus 1.2.0 (Electron 43.2.0 / Chromium 150.0.7871.129) |
| **Author** | AmirEyZed |
| **Upstream** | https://github.com/AmirEyZed/sahne-plus |
| **Platform** | Windows x64 |
| **Reviewed** | 2026-09-18 |
| **Application code** | ~1,935 lines across 6 source files |
| **Verdict** | **No malware, no backdoor, no exfiltration, no obfuscation.** Application code is clean and behaves as documented. |
| **Signed** | No — neither the installer nor the executable is code-signed |

The application does what its documentation says it does. Application code was read line by line; build integrity controls were verified against the shipped binary; network behaviour was enumerated from source and confirmed against a sandboxed runtime.

---

## What was reviewed

Sahne Plus is an Electron application. Electron applications ship their logic as plain, unminified JavaScript inside an `app.asar` container — they are not compiled to native code. The review therefore covered the complete application source, not a reconstruction of it.

| File | Lines | Role |
|---|---:|---|
| `server/server.js` | 858 | HTTP/SSE server, KickBot WebSocket client, Kick chat client, exchange-rate fetch, alert queue |
| `public/app.html` | 340 | Controller UI markup |
| `public/app.js` | 311 | Controller UI logic |
| `public/overlay.js` | 242 | Browser Source renderer (OBS / Meld Studio) |
| `electron/main.js` | 152 | Electron shell: window, tray, IPC, DPAPI secret storage, autostart |
| `electron/preload.js` | 32 | Context bridge |

Method:

1. Verified the installer against the published `SHA256SUMS.txt`.
2. Unpacked the NSIS installer, the inner 7z payload, and `resources/app.asar`.
3. Read all application source line by line.
4. Enumerated every network endpoint, every IPC handler, and every dangerous-API category.
5. Read the Electron fuse configuration directly from the executable.
6. Extracted and validated the embedded ASAR integrity record from the PE resource directory.
7. Ran the application in an isolated data directory and confirmed its startup integrity and listening behaviour.
8. Diffed 1.1.1 against 1.2.0 to confirm the release notes matched the actual change.

---

## What was NOT reviewed

Stated plainly, because the difference matters:

- **The bundled Chromium/Electron runtime was not audited.** `Sahne Plus.exe` is a 225 MB Electron binary. Its configuration was verified (fuses, ASAR integrity); its ~200 MB of Chromium and V8 machine code was **not** reverse engineered. This is the single largest unexamined surface.
- **Third-party services were not assessed.** KickBot, Kick, Pusher, baha24 and bonbast were treated as black boxes. Their security is out of scope.
- **No dynamic instrumentation.** No debugger was attached, no memory was inspected, no network traffic was intercepted at the packet level.
- **No fuzzing, no automated analysis, no dependency-CVE sweep of Electron/Chromium.**
- **Not an endorsement of safety.** "No malicious behaviour found in the application code" is a statement about the application code. It is not a claim that the software is free of vulnerabilities.

---

## Verification results

### Published hashes

Both installers were verified byte-for-byte against the `SHA256SUMS.txt` published in the corresponding GitHub release.

```
Sahne-Plus-Setup-1.2.0.exe   100,658,451 bytes
  published  dddbaa942d715021b5636998cb2f62321127b2c031b4daee7efc840eef1bfc92
  measured   dddbaa942d715021b5636998cb2f62321127b2c031b4daee7efc840eef1bfc92   MATCH

Sahne-Plus-Setup-1.1.1.exe   100,658,035 bytes
  published  dc53caf04dfb2e44a34c7521b6aaa4d313dfdefb8d284d7edc162f66ab7d105a
  measured   dc53caf04dfb2e44a34c7521b6aaa4d313dfdefb8d284d7edc162f66ab7d105a   MATCH
```

See [`artifacts/hashes.txt`](artifacts/hashes.txt).

### Code signing

```
Sahne-Plus-Setup-1.2.0.exe        NotSigned
app-1.2.0/Sahne Plus.exe          NotSigned
```

Unsigned, as the release notes state. There is no Authenticode chain, so Windows SmartScreen warnings are expected and the published checksum is the only available integrity anchor.

### Electron fuses

Read directly from the shipped executable:

```
Fuse Version: v1
  RunAsNode                                Disabled
  EnableCookieEncryption                   Enabled
  EnableNodeOptionsEnvironmentVariable     Disabled
  EnableNodeCliInspectArguments            Disabled
  EnableEmbeddedAsarIntegrityValidation    Enabled
  OnlyLoadAppFromAsar                      Enabled
  LoadBrowserProcessSpecificV8Snapshot     Disabled
  GrantFileProtocolExtraPrivileges         Disabled
  WasmTrapHandlers                         Enabled
```

These are the correct settings for a production Electron build. The three that matter most — `RunAsNode`, `NODE_OPTIONS`, and `--inspect` — are all disabled, which closes the usual trivial Electron-to-native-code escalation routes. `OnlyLoadAppFromAsar` prevents loading code from a sibling directory.

See [`artifacts/fuses.txt`](artifacts/fuses.txt).

### ASAR integrity

The executable embeds an integrity record in its PE resources under `INTEGRITY > ELECTRONASAR`:

```
[{"file":"resources\\app.asar","alg":"SHA256","value":"<hash>"}]
```

That value was verified against the actual ASAR header in both releases:

```
1.2.0  embedded  5b1adda8f779dfb0ea2bbbc7391d48c188372f161050b258eba3ba1fb04b17cc
       measured  5b1adda8f779dfb0ea2bbbc7391d48c188372f161050b258eba3ba1fb04b17cc   MATCH

1.1.1  embedded  5ed707921dc7f1037bf77efe75d36bc9dff9025ccb2619aba902e50d4dd001ea
       measured  5ed707921dc7f1037bf77efe75d36bc9dff9025ccb2619aba902e50d4dd001ea   MATCH
```

The scope of the hash is the ASAR header JSON (the file index), which is what Electron validates at startup. Both match. Reproduce with [`tools/verify-asar-integrity.py`](tools/verify-asar-integrity.py).

### Runtime behaviour

The application was started with an isolated data directory and a non-default port:

```
started successfully, ASAR integrity validation passed
listener confirmed on 127.0.0.1:<port>   (loopback only, not 0.0.0.0)
DPAPI secret storage: active
preload: sandboxed=true
```

---

## Architecture

```
Electron main process
  └─ HTTP server bound to 127.0.0.1
       ├─ /            controller window
       ├─ /overlay     Browser Source for OBS / Meld Studio
       ├─ /events      Server-Sent Events push channel
       └─ /api/*       control API
```

Notable: the application has **zero runtime dependencies**. It uses only Node built-ins (`http`, `https`, `tls`, `fs`, `path`, `crypto`). There is no `node_modules`, no npm supply chain, and no bundled third-party JavaScript. For an Electron application this is unusual and materially reduces supply-chain risk.

### Network endpoints

Every outbound host in the application, enumerated from source:

| Endpoint | Purpose |
|---|---|
| `wss://kickbot.live/ws` | donation events |
| `https://widgets.kickbot.com` | `capture_tip`, queue sync, widget metadata |
| `wss://ws-us2.pusher.com/app/32cbd69e...` | Kick public chat (subscriptions, gift subscriptions) |
| `https://kick.com/api/v2/channels/<slug>` | channel slug to chatroom id resolution |
| `https://baha24.com/api/v1/price` | USD to toman rate (primary) |
| `https://www.bonbast.com/` | USD to toman rate (scraped fallback) |
| `ws://127.0.0.1:13376` | Meld Studio layer reload (loopback) |

**Seven hosts. No telemetry, no analytics, no crash reporting, no update checks, no CDN or font loads.** This matches the privacy documentation. See [`artifacts/network-endpoints.md`](artifacts/network-endpoints.md).

---

## What the application does well

Worth recording, because it is above average for a solo-developer tool:

- **No dangerous APIs anywhere.** No `child_process`, `exec`, `spawn`, `eval`, `new Function`, `atob`, `Buffer.from(..., 'base64')`, `process.binding`, or native modules. Verified across the full source.
- **No obfuscation.** No encoded blobs, no strings over 60 characters that look like packed data, no dynamic code construction.
- **Renderer hardened.** `contextIsolation: true`, `sandbox: true`, `nodeIntegration: false`, `webviewTag: false`, DevTools disabled in packaged builds, permission requests denied wholesale.
- **IPC is sender-validated.** All 13 IPC handlers check that the caller is the application's own window.
- **XSS is handled correctly.** Untrusted donor names and messages are escaped at every insertion point, and the overlay template resolver performs a single pass over an escaped template with a function replacer — which correctly defeats `$&` re-injection. The comment above that code is accurate.
- **SVG cannot be imported as media.** The type allow-list and magic-byte sniffer both exclude SVG, closing a classic stored-XSS vector.
- **Media import is validated.** Symlinks resolved, magic bytes checked against the claimed extension, basename-only naming, Windows reserved names handled, control and bidi characters stripped.
- **Overlay CSP is strict.** `default-src 'none'; script-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'`.
- **Secret handling is sound in-app.** The KickBot credential is encrypted via Windows DPAPI, is never returned by `/api/config`, and is redacted from the application's own log.
- **No steganographic or appended data.** PNG files terminate cleanly at `IEND`; font files carry valid signatures and no embedded URLs beyond their own designer credits.

---

## Version diff: 1.1.1 to 1.2.0

The diff was reviewed to confirm the release notes matched the shipped change. It does. Changes are confined to:

- the exchange-rate source: baha24 JSON API as primary, bonbast as a rate-limited fallback
- default refresh interval 10 to 2 minutes, minimum interval 5 to 1
- `rateSource` exposed in state so the UI can label which source is live
- one UI fix: the first-run setup card no longer remains visible after connection
- documentation and licence-notice updates for baha24

No other logic changed. Full summary in [`artifacts/version-diff-summary.md`](artifacts/version-diff-summary.md).

---

## What this repository does not contain

Deliberately, and by design:

- **No Sahne Plus source code.** The review is published; the code is not. Sahne Plus is proprietary software. Its licence states plainly that no right is granted to copy, publish, or distribute the software or its source, and its Terms of Use prohibit redistribution other than of the unmodified official installer or the official download link.
- **No binaries or installers.** Download from the official release page: https://github.com/AmirEyZed/sahne-plus/releases
- **No Sahne Plus documentation.** `PRIVACY.md`, `TERMS.md`, `SECURITY.md`, `CHANGELOG.md` and `LICENSE.txt` are the author's documents — read them upstream.
- **No bundled fonts or artwork.**

Everything here is original analysis, measurement, or tooling produced for this review.

---

## Reproducing

```bash
# 1. Verify the installer against the published checksum
Get-FileHash .\Sahne-Plus-Setup-1.2.0.exe -Algorithm SHA256

# 2. Read the Electron fuse configuration
npx @electron/fuses read --app "Sahne Plus.exe"

# 3. Verify the embedded ASAR integrity record
python tools/verify-asar-integrity.py "Sahne Plus.exe" resources/app.asar
```

Requires 7-Zip for installer extraction and Node.js for ASAR tooling. The script in [`tools/`](tools/) is self-contained.

---

## Scope statement

This review examined the application's JavaScript source, its build integrity configuration, and its network behaviour. It did **not** examine the bundled Chromium/Electron runtime binary, the third-party services the application depends on, or the security of any dependency's future updates.

**The correct conclusion is:** the application code is clean, does what it documents, and shows no sign of malicious behaviour. It is **not** a statement that the software is safe, certified, or free of vulnerabilities.

Users should weigh a further practical consideration that no code review can resolve: the software is **proprietary, unsigned, and built locally by a single developer**, not by public CI. Its integrity can be verified against the published checksum, but its provenance cannot be independently attested.

---

## License

Original content in this repository — the review text, scripts, and measured data — is released under [MIT](LICENSE).

Sahne Plus itself is proprietary software owned by AmirEyZed and is not covered by this licence.
