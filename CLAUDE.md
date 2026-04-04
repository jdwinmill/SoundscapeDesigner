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

# Backend tests (128 tests, 379 assertions)
php artisan test

# JS tests (80 tests — curvemath + designer reducer)
npm test

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
- `resources/js/lib/audioEngine.js` — Web Audio engine class for real-time BPM-reactive preview
- `resources/js/lib/stemColors.js` — 12-color palette for stem lane assignment
- `resources/css/app.css` — Tailwind @theme with CSS custom properties mirroring tokens.js
- `resources/js/Layouts/AppLayout.jsx` — Shared layout (nav, footer, flash messages)
- `resources/js/Components/` — FormInput, FlashMessages, SoundscapeCard, PackCard
- `resources/js/Components/Designer/` — DesignerPage, DesignerCanvas, DesignerHeader, StemBand, StemBandHandles, BpmAxis, SpeedCurveEditor, StemPicker, StemPickerCard, constants
- `resources/js/Pages/` — Home, Explore, Dashboard, DesignTokens, Auth/*, Packs/*, Soundscapes/*, Users/*

### Tests

**JS (resources/js/lib/__tests__):**
- `curvemath.test.js` — Volume at all trapezoid zones, speed interpolation/clamping, coordinate round-trips
- `designerReducer.test.js` — CRUD actions, undo/redo, drag operations, transport isolation, INIT_FROM_SERVER, buildSavePayload, TOGGLE_PICKER

**Backend (tests/Feature/):**
- `AuthTest.php` — API auth (register, login, logout, rate limiting)
- `WebAuthTest.php` — Web session auth (register, login, logout, guest redirect)
- `WebPageTest.php` — Page access (visibility, auth guards, server-side props)
- `StemPackTest.php` — CRUD, visibility scoping, search leak prevention, tags, cascade delete
- `StemTest.php` — Upload, scoping, file cleanup, download access across visibility boundaries
- `SoundscapeTest.php` — CRUD with pivot, config accessor, clone, search/tag leak prevention
- `SoundscapeEditPageTest.php` — Edit page access, ownership, PUT update from session
- `SoundscapeSavePayloadTest.php` — Designer payload format passes API validation
- `FavoriteTest.php` — Toggle, list, access control
- `FavoriteHydrationTest.php` — Favorite state passed to frontend
- `ExploreSearchTest.php` — Server-side search filtering
- `SanctumSpaTest.php` — Session-authenticated API calls from browser
- `PackCreateFlowTest.php` — Simplified pack create + stem upload flow
- `UserProfileTest.php` — Public profile, no PII exposure

## Key Architecture Decisions

- **Dual auth**: API routes use Sanctum tokens (for iOS app) and session cookies (for browser SPA). Both work through `auth:sanctum` middleware — Sanctum auto-detects first-party requests.
- **Soundscape config is computed, not stored**: The `config` JSON column was removed. The `soundscape_stem` pivot table is the single source of truth. A computed `config` accessor on the Soundscape model builds the export format from pivot data.
- **Visibility scoping**: Index queries wrap `is_public OR user_id` in a closure so search/tag filters can't leak private data.
- **Stem download access**: Stems can be downloaded if the pack is public, the user owns the pack, OR the stem is referenced by a public soundscape.
- **File cleanup**: `StemObserver::deleting` removes audio files from storage. `StemPack::deleting` iterates stems via Eloquent (triggering the observer) before the DB cascade.
- **Case-insensitive search**: Uses `ilike` on Postgres, `like` on SQLite (already case-insensitive). Helper in base Controller.
- **Slug-based routing**: StemPack and Soundscape use auto-generated slugs for public URLs and route model binding.
- **Server-side data**: Dashboard and Explore pass data as Inertia props. No raw fetch calls for page data — only for mutations (stem upload, favorite toggle, clone) which use XSRF cookies.

## Soundscape Designer Architecture

The designer is a single-page interactive editor at `/soundscapes/create` (and `/soundscapes/{slug}/edit` for existing). The x-axis is BPM (60–240) and stems are visual trapezoid bands you drag, resize, and shape.

### Component tree
```
DesignerPage (shared — owns useReducer + audioEngine ref)
├── DesignerHeader        (name, description, tags, baseBpm, public toggle, save)
├── DesignerCanvas (SVG)
│   ├── BpmAxis           (tick marks, labels)
│   ├── StemBand[]        (trapezoid per lane, color-coded)
│   │   └── StemBandHandles (drag: move, resize edges, fade tips, volume)
│   └── BpmScrubber       (amber vertical line, draggable)
├── Lane Controls         (mute/solo/speed/remove per selected lane)
│   └── SpeedCurveEditor  (piecewise-linear, click/drag/double-click points)
├── TransportBar          (play/stop, level meter, volume, BPM scrubber)
└── StemPicker            (slide-out panel, My Packs / Explore, search)
    └── StemPickerCard[]  (stem info + Add button)
```

Create.jsx and Edit.jsx are thin wrappers around DesignerPage. Edit passes the existing soundscape for INIT_FROM_SERVER.

### State: `designerReducer.js`
- Single `useReducer`, no external library
- Undo/redo via snapshot history (max 50 entries)
- `DRAG_START` pushes one undo entry; `DRAG_UPDATE_LANE` updates without history (one Ctrl+Z undoes an entire drag)
- `lanes[]` holds per-stem config: bpmRange, fadeIn/Out, volume, speed, speedCurve, muted, solo, colorIndex, audioBuffer
- Transport state (scrubBpm, isPlaying, masterVolume) excluded from undo history
- `buildSavePayload(state)` maps directly to `POST /api/soundscapes` format

### Rendering: SVG via React
- Each StemBand is an SVG `<path>` trapezoid — fill opacity maps to volume, x position = BPM range, slopes = fade zones
- Handles appear on hover, persist on selection. 6 drag zones per band.
- `DesignerCanvas` uses ResizeObserver for responsive width, reports width to parent for speed curve alignment

### Audio: `audioEngine.js`
- Plain class, not React state. Accessed via ref.
- Per-stem chain: `AudioBufferSourceNode (loop) → GainNode → masterGain → AnalyserNode → destination`
- `setBpm(bpm)` recalculates all gains + playback rates with 50ms `linearRampToValueAtTime` to avoid clicks
- `playbackRate = (currentBpm / baseBpm) * speedAtBpm(currentBpm)`
- Solo/mute logic applied in gain calculation
- Audio fetched from `/api/stem-packs/{slug}/stems/{id}/download`, decoded with `decodeAudioData()`
- Deduplicates fetches via `fetchedLaneIdsRef` — handles both initial load (edit) and new additions (create)

### Curve math: `curvemath.js`
- `volumeAtBpm()` — trapezoidal volume (matches Python Stem.volume_at_bpm)
- `speedAtBpm()` — piecewise-linear with clamping (matches Python Stem.speed_at_bpm)
- `volumeCurvePath()` — generates SVG path `d` attribute for trapezoid rendering
- `bpmToPixel()` / `pixelToBpm()` — coordinate conversion utilities

### Keyboard shortcuts
- `Ctrl/Cmd+Z` — Undo
- `Ctrl/Cmd+Shift+Z` — Redo
- `Delete/Backspace` — Remove selected lane
- `Escape` — Close picker or deselect lane
- `Space` — Play/pause

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
- Drag operations use `DRAG_START` + `DRAG_UPDATE_LANE` to avoid undo flooding

## Content & Licensing

- **Stem audio licensing**: Users are responsible for having rights to audio they upload. Samples from services like Splice are typically licensed for use in musical compositions, not redistribution. Public stem packs on this platform could be interpreted as redistribution.
- **For production**: Need either original stems, CC0-licensed content (e.g. Freesound.org), or clear user terms stating uploaders are responsible for rights.
- **For development/testing**: Any audio files are fine in private soundscapes on local dev.

## What's Not Built Yet

### CRUD UI gaps
- Delete pack/soundscape/stems from UI (API endpoints exist, no buttons)
- Edit pack metadata after creation (API exists)
- Public/private toggle from UI (API exists)

### iOS App
- Swift AVAudioEngine implementation
- GPS pace → BPM conversion
- Download soundscape config + stems from API
- Offline playback
- User auth (token-based, API ready)

### Production Deployment
- Configure `SANCTUM_STATEFUL_DOMAINS` for production domain
- Switch `FILESYSTEM_DISK` to S3
- Lock down CORS `allowed_origins` to production domain
- Laravel Cloud deployment config
- Serverless Postgres setup

### Designer Polish (nice-to-haves)
- Lane reordering via drag
- Stem preview playback in picker (3-second audition)
- Waveform thumbnails inside stem bands
- E2E browser tests for drag interactions
