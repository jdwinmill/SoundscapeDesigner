# StrideSoundscape — TODO

## Soundscape Designer (feature/soundscape-designer branch)

### Done
- [x] Phase 1: Foundation — `curvemath.js`, `designerReducer.js`, `stemColors.js`
- [x] Phase 2: Static canvas — `BpmAxis`, `StemBand`, `DesignerCanvas`, wired into `Create.jsx` with reducer, transport bar, lane controls, undo/redo

### In Progress
- [ ] **Phase 3: Interaction — drag handles on stem bands**
  - [ ] `StemBandHandles.jsx` — 6 drag zones: center move, left/right edge resize, fade tip drag, volume drag
  - [ ] Pointer event handling with `setPointerCapture` for smooth tracking
  - [ ] Scrubber drag on the SVG canvas (currently only the range slider works)
  - [ ] Keyboard shortcuts: Ctrl+Z undo, Ctrl+Shift+Z redo, Delete remove lane

### Not Started
- [ ] **Phase 4: Audio — Web Audio engine + real-time preview**
  - [ ] `audioEngine.js` — AudioContext, per-stem AudioBufferSourceNode + GainNode chain
  - [ ] Audio fetching + decoding from `/api/stem-packs/{slug}/stems/{id}/download`
  - [ ] `setBpm()` drives gain + playbackRate with 50ms ramps
  - [ ] Solo/mute logic in gain calculation
  - [ ] `TransportBar.jsx` — level meter via AnalyserNode
  - [ ] Connect engine to reducer state via useEffect hooks
  - [ ] Loading spinners on stem bands while audio decodes

- [ ] **Phase 5: Stems + save — picker panel, header, persistence**
  - [ ] `StemPicker.jsx` — slide-out panel, glass morphism, 400px wide
  - [ ] `StemPickerCard.jsx` — stem card with name, role, key, "Add" button
  - [ ] Tabs: "My Packs" | "Explore" — fetches from `/api/stem-packs`
  - [ ] Search within picker
  - [ ] `DesignerHeader.jsx` — description textarea, tags, public toggle
  - [ ] Save button: `POST /api/soundscapes` with `buildSavePayload(state)`
  - [ ] Redirect to `/s/{slug}` on save
  - [ ] Unsaved changes warning (beforeunload)

- [ ] **Phase 6: Polish — speed curves, mute/solo, edit page**
  - [ ] `SpeedCurveEditor.jsx` — piecewise-linear overlay on selected lane
  - [ ] Draggable control points, click-to-add, right-click-to-delete
  - [ ] `StemLaneControls.jsx` — refined mute/solo/delete/speed UI (currently inline in Create.jsx)
  - [ ] `Soundscapes/Edit.jsx` — loads existing soundscape, dispatches INIT_FROM_SERVER
  - [ ] Web route: `GET /soundscapes/{soundscape:slug}/edit` with auth + ownership check
  - [ ] Lane reordering via drag
  - [ ] Remove test stem button from Create.jsx
  - [ ] Stem preview playback in picker (3-second audition)

## Platform — Not Yet Built

### CRUD UI gaps
- [ ] Delete pack from UI (API exists)
- [ ] Delete soundscape from UI (API exists)
- [ ] Delete individual stems from pack detail (API exists)
- [ ] Edit pack metadata after creation (API exists)
- [ ] Public/private toggle from UI (API exists)

### iOS App
- [ ] Swift AVAudioEngine implementation
- [ ] GPS pace → BPM conversion
- [ ] Download soundscape config + stems
- [ ] Offline playback
- [ ] User auth (token-based, API ready)

### Production
- [ ] Configure `SANCTUM_STATEFUL_DOMAINS` for production domain
- [ ] Switch `FILESYSTEM_DISK` to S3
- [ ] Lock down CORS `allowed_origins` to production domain
- [ ] Laravel Cloud deployment config
- [ ] Serverless Postgres setup
