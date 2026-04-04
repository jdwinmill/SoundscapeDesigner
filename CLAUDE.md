# StrideSoundscape

Web platform for designing BPM-reactive audio soundscapes for runners. Built with Laravel 13 + Inertia.js + React + Tailwind v4.

## Stack

- **Backend**: Laravel 13, PHP 8.5, Sanctum (API tokens + SPA session auth)
- **Frontend**: Inertia.js + React, Tailwind CSS v4, Vite
- **Database**: SQLite (dev), serverless Postgres on Laravel Cloud (prod)
- **Storage**: Local `public` disk (dev), S3 (prod)

## Running

```bash
# Dev server (PHP + Vite)
composer run dev

# Tests (119 tests, 337 assertions)
php artisan test

# Build frontend
npm run build
```

Use `php` from Homebrew (`/opt/homebrew/opt/php/bin/php` — PHP 8.5). The Herd Lite binary at `~/.config/herd-lite/bin/php` is 8.4 and triggers deprecation warnings.

## Project Structure

### Backend

- `app/Models/` — User, StemPack, Stem, Soundscape, Tag, Favorite
- `app/Http/Controllers/Api/` — REST API (token + session auth): Auth, StemPack, Stem, Soundscape, Favorite, Tag, User
- `app/Http/Controllers/Web/` — Session auth (login, register, logout)
- `app/Http/Middleware/HandleInertiaRequests.php` — Shares auth user + flash messages
- `app/Observers/StemObserver.php` — Deletes audio files when stems are deleted
- `routes/api.php` — 23 API routes (public browsing + auth:sanctum for mutations)
- `routes/web.php` — Inertia page routes with server-side data loading
- `database/factories/` — User, StemPack, Stem, Soundscape, Tag

### Frontend

- `resources/js/app.jsx` — Inertia entry point
- `resources/js/lib/tokens.js` — Design tokens (colors, typography, effects, radii)
- `resources/js/lib/curvemath.js` — Trapezoidal volume + piecewise-linear speed math (pure functions)
- `resources/js/lib/designerReducer.js` — Soundscape Designer state management with undo/redo
- `resources/js/lib/stemColors.js` — 12-color palette for stem lane assignment
- `resources/css/app.css` — Tailwind @theme with CSS custom properties mirroring tokens.js
- `resources/js/Layouts/AppLayout.jsx` — Shared layout (nav, footer, flash messages)
- `resources/js/Components/` — FormInput, FlashMessages, SoundscapeCard, PackCard
- `resources/js/Components/Designer/` — DesignerCanvas, StemBand, BpmAxis, constants
- `resources/js/Pages/` — Home, Explore, Dashboard, DesignTokens, Auth/*, Packs/*, Soundscapes/*, Users/*

### Tests

- `tests/Feature/AuthTest.php` — API auth (register, login, logout, rate limiting)
- `tests/Feature/WebAuthTest.php` — Web session auth (register, login, logout, guest redirect)
- `tests/Feature/WebPageTest.php` — Page access (visibility, auth guards, server-side props)
- `tests/Feature/StemPackTest.php` — CRUD, visibility scoping, search leak prevention, tags, cascade delete
- `tests/Feature/StemTest.php` — Upload, scoping, file cleanup, download access across visibility boundaries
- `tests/Feature/SoundscapeTest.php` — CRUD with pivot, config accessor, clone, search/tag leak prevention
- `tests/Feature/FavoriteTest.php` — Toggle, list, access control
- `tests/Feature/UserProfileTest.php` — Public profile, no PII exposure
- `tests/Feature/SanctumSpaTest.php` — Session-authenticated API calls from browser
- `tests/Feature/ExploreSearchTest.php` — Server-side search filtering
- `tests/Feature/FavoriteHydrationTest.php` — Favorite state passed to frontend
- `tests/Feature/PackCreateFlowTest.php` — Simplified pack create + stem upload flow

## Key Architecture Decisions

- **Dual auth**: API routes use Sanctum tokens (for iOS app) and session cookies (for browser SPA). Both work through `auth:sanctum` middleware — Sanctum auto-detects first-party requests.
- **Soundscape config is computed, not stored**: The `config` JSON column was removed. The `soundscape_stem` pivot table is the single source of truth. A computed `config` accessor on the Soundscape model builds the export format from pivot data.
- **Visibility scoping**: Index queries wrap `is_public OR user_id` in a closure so search/tag filters can't leak private data. This was a bug that was caught and fixed.
- **Stem download access**: Stems can be downloaded if the pack is public, the user owns the pack, OR the stem is referenced by a public soundscape.
- **File cleanup**: `StemObserver::deleting` removes audio files from storage. `StemPack::deleting` iterates stems via Eloquent (triggering the observer) before the DB cascade.
- **Case-insensitive search**: Uses `ilike` on Postgres, `like` on SQLite (already case-insensitive). Helper in base Controller.
- **Slug-based routing**: StemPack and Soundscape use auto-generated slugs for public URLs and route model binding.
- **Server-side data**: Dashboard and Explore pass data as Inertia props. No raw fetch calls for page data — only for mutations (stem upload, favorite toggle, clone) which use XSRF cookies.

## Soundscape Designer Architecture

The designer is on branch `feature/soundscape-designer`. It's a single-page interactive editor at `/soundscapes/create` where the x-axis is BPM (60–240) and stems are visual trapezoid bands you drag, resize, and shape.

### Component tree
```
Create.jsx (page — owns useReducer + audioEngine ref)
├── DesignerHeader        (name, description, tags, save)
├── DesignerCanvas (SVG)
│   ├── BpmAxis           (tick marks, labels)
│   ├── StemBand[]        (trapezoid per lane)
│   │   └── StemBandHandles (drag: move, resize, fade, volume)
│   ├── BpmScrubber       (amber vertical line)
│   └── SpeedCurveEditor  (piecewise-linear overlay)
├── StemLaneControls      (mute/solo/delete/speed)
├── TransportBar          (play/stop, volume, BPM readout)
└── StemPicker            (slide-out, browse packs, add stems)
```

### State: `designerReducer.js`
- Single `useReducer`, no external library
- Undo/redo via snapshot history (max 50 entries)
- `lanes[]` holds per-stem config: bpmRange, fadeIn/Out, volume, speed, speedCurve, muted, solo, colorIndex, audioBuffer
- Transport state (scrubBpm, isPlaying, masterVolume) excluded from undo history
- `buildSavePayload(state)` maps directly to `POST /api/soundscapes` format

### Rendering: SVG via React
- Each StemBand is an SVG `<path>` trapezoid — fill opacity = volume, x position = BPM range, slopes = fade zones
- Small element count (2-20 stems) — SVG gives free hit detection and pointer events
- `DesignerCanvas` uses ResizeObserver for responsive width

### Audio: `audioEngine.js` (planned)
- Plain class, not React state. Accessed via ref.
- Per-stem chain: `AudioBufferSourceNode (loop) → GainNode → masterGain → AnalyserNode → destination`
- `setBpm(bpm)` recalculates all gains + playback rates with 50ms ramp to avoid clicks
- `playbackRate = (currentBpm / baseBpm) * speedAtBpm(currentBpm)`

### Curve math: `curvemath.js`
- `volumeAtBpm()` — trapezoidal volume (matches Python Stem.volume_at_bpm)
- `speedAtBpm()` — piecewise-linear with clamping (matches Python Stem.speed_at_bpm)
- `volumeCurvePath()` — generates SVG path `d` attribute for trapezoid rendering
- `bpmToPixel()` / `pixelToBpm()` — coordinate conversion utilities

## Design System

- **Palette**: Dark base (#0a0a0f), teal-to-violet accent gradient, amber highlights
- **Fonts**: Sora (headings), Inter (body) — loaded from fonts.bunny.net
- **Tokens**: `resources/js/lib/tokens.js` (JS) + `resources/css/app.css` @theme (CSS custom properties)
- **Design token reference page**: `/design-tokens`
- **Utility classes**: `.text-gradient`, `.bg-gradient-accent`, `.glass`, `.glow-teal`, `.glow-violet`, `.glow-amber`

## Conventions

- Use Homebrew PHP 8.5 (not Herd Lite)
- Models use `#[Fillable]` attribute (Laravel 13 style), not `$fillable` property
- Factories exist for all models — use them in tests
- `RefreshDatabase` trait on all feature tests (in-memory SQLite)
- API returns JSON, web routes return Inertia responses
- Public URLs: `/s/{slug}` (soundscapes), `/u/{username}` (profiles), `/packs/{slug}` (packs)
- Designer uses SVG for the canvas (not HTML/CSS or Canvas 2D)
- Designer state is a single `useReducer` — no external state library
- Web Audio engine is a plain class accessed via ref — not React state
