# Ideas: Stem Definition Object for AI-Driven DJ

## The Problem

Today, stems carry only mechanical metadata — BPM range, volume, fade curves. A human
has to manually curate which stems layer together and when. There's no way to hand an AI
a pile of stems and say "build me a 45-minute running set that starts mellow and peaks
at mile 3."

The AI has no idea what a stem *sounds like*, what role it plays in a mix, or how it
relates to other stems. It's flying blind.

## The Concept: Stem Definition Object

Attach a rich, semantic definition to every stem so an AI can reason about music the way
a DJ does — understanding mood, energy, texture, harmonic compatibility, and listener
experience.

### Proposed Schema

```json
{
  "id": "forest_marimba",
  "file": "forest_marimba.wav",

  "musical": {
    "key": "Cm",
    "scale": "minor_pentatonic",
    "bpm": 150,
    "time_signature": "4/4",
    "duration_s": 32.0,
    "loopable": true
  },

  "role": {
    "type": "melodic",
    "layer": "mid",
    "function": "hook"
  },

  "energy": {
    "intensity": 0.5,
    "drive": 0.3,
    "groove": 0.7
  },

  "mood": {
    "tags": ["serene", "organic", "warm"],
    "valence": 0.7,
    "arousal": 0.4
  },

  "sonic": {
    "brightness": 0.6,
    "density": 0.3,
    "space": 0.8,
    "warmth": 0.9
  },

  "mix_hints": {
    "pairs_well_with": ["forest_pad", "forest_clicks"],
    "conflicts_with": ["neon_lead"],
    "solo_capable": false,
    "intro_suitable": true,
    "climax_suitable": false
  },

  "listener_context": {
    "best_for": ["easy_run", "warmup", "cooldown"],
    "avoid_for": ["sprint", "interval_peak"]
  }
}
```

### Field Breakdown

| Section | Purpose | Why AI Needs It |
|---------|---------|-----------------|
| **musical** | Harmonic and rhythmic identity | Key/scale let AI avoid clashing stems. BPM confirms time-stretch limits. |
| **role** | What this stem *does* in a mix | AI needs to know "this is a bassline" vs "this is a texture pad" to build balanced layers. Without it, you get 4 basslines stacked or no rhythm. |
| **energy** | Numeric intensity profile | Maps directly to running effort. AI can curve energy up/down over a run. |
| **mood** | Emotional character | Lets AI build emotional arcs — start calm, build tension, euphoric peak, wind down. Valence/arousal follow the circumplex model of emotion. |
| **sonic** | Timbral qualities | Prevents muddy mixes. AI can balance bright vs warm, dense vs spacious. |
| **mix_hints** | Explicit compatibility rules | Hard guardrails. Even if AI reasons well about mood/energy, these catch known clashes. |
| **listener_context** | Activity-phase mapping | Directly ties stems to running phases — the end goal. |

## How the AI DJ Would Work

```
Input:
  - Library of stems + definitions
  - Run plan: { duration: 45min, phases: [warmup(5m), build(10m), peak(15m), sustain(10m), cooldown(5m)] }
  - Preferences: { mood_arc: "uplifting_journey", genres: ["organic_electronic", "synthwave"] }

Output:
  - Timeline of stem activations with crossfade points
  - Per-segment BPM targets
  - Volume automation curves
```

### AI Reasoning Chain

1. **Phase mapping** — Match `listener_context.best_for` to run phases
2. **Energy curve** — Plot target `energy.intensity` across the run timeline
3. **Harmonic planning** — Group stems by compatible keys, plan key changes at phase transitions
4. **Layer balancing** — Ensure each active segment has coverage across `role.layer` (low/mid/high) and `role.type` (rhythmic/melodic/textural)
5. **Transition design** — Use `mix_hints.pairs_well_with` and sonic profiles to plan smooth crossfades
6. **Conflict avoidance** — Respect `conflicts_with` and avoid stacking stems with similar `role.function`

## Gap Analysis

### Gap 1: Who Populates the Definitions?
Manually tagging every stem is tedious and error-prone.

**Mitigation:** Use audio analysis AI (e.g. Essentia, librosa, or an LLM with audio
input) to auto-generate definitions from the audio files. Human review for `mix_hints`
and `listener_context` only. Could be a CLI command:
```
soundscape analyze stems/forest/ --output definitions/
```

### Gap 2: Key Detection Accuracy
Auto-detected keys are often wrong, especially for ambient/textural stems with no clear tonal center.

**Mitigation:** Add a `key_confidence` field. AI treats low-confidence stems as
harmonically neutral — safe to layer with anything, but not relied on for key anchoring.

### Gap 3: Energy/Mood Are Subjective
My "0.5 intensity" and your "0.5 intensity" might be different.

**Mitigation:** Define intensity relative to a calibration set within each stem pack.
The pack's metadata file declares the energy range. Alternatively, normalize across the
full library at import time — rank all stems by spectral energy and map to 0-1.

### Gap 4: Run Cadence != BPM
Current system maps BPM to running pace, but runners don't lock step to beat. The
relationship is more about perceived energy than literal footfall sync.

**Mitigation:** The stem definition should distinguish `musical.bpm` (actual tempo)
from `energy.drive` (perceived push). A 150 BPM ambient pad and a 150 BPM drum loop
feel completely different to run to. The energy fields handle this.

### Gap 5: Transition Intelligence
Knowing stems pair well isn't enough. The AI needs to know *how* to transition.

**Mitigation:** Add optional `transition_hints`:
```json
"transition_hints": {
  "fade_in_beats": 8,
  "fade_out_beats": 4,
  "entry_point": "downbeat",
  "exit_style": "filter_sweep"
}
```

### Gap 6: No "Set" or "Pack" Level Metadata
Individual stem defs don't capture the *collection* identity. "Forest" is a cohesive
vibe — that context matters.

**Mitigation:** Add a pack-level definition:
```json
{
  "pack": "forest",
  "genre": "organic_electronic",
  "mood_summary": "nature-inspired, meditative, building",
  "key_center": "Cm",
  "bpm_center": 150,
  "stem_count": 8,
  "energy_range": [0.2, 0.8],
  "best_for_phases": ["warmup", "easy_run", "cooldown"]
}
```

### Gap 7: Cross-Pack Compatibility
Can you mix "forest" stems with "neon" stems? Currently undefined.

**Mitigation:** Pack-level definitions declare harmonic compatibility (`key_center`)
and the AI uses stem-level `musical.key` + `sonic` profiles to evaluate cross-pack
blending. Some combos will work (forest_pad over neon_kick), others won't. The AI
should be able to reason about this from the definitions.

### Gap 8: Real-Time vs Pre-Planned
End goal says "create a set" — but the current system is real-time BPM-reactive.

**Mitigation:** Support both modes:
- **Pre-planned:** AI generates a full timeline before the run. Predictable, optimized.
- **Reactive:** AI adjusts in real-time based on live BPM/heart rate. Needs simpler
  decision rules — full reasoning chain is too slow per-beat. The stem definitions
  would fuel a pre-computed lookup table: "at this energy level, these stems are valid."

## Sanity Check

| Question | Verdict |
|----------|---------|
| Is this over-engineered for the use case? | No — the minimum viable version is `role` + `energy` + `mood` + `musical.key`. That alone is enough for basic AI mixing. The rest is progressive enhancement. |
| Can AI actually reason about this? | Yes. LLMs are strong at structured constraint satisfaction. Given stems as JSON + a run plan, producing a timeline is well within capability. |
| Does this break the existing system? | No. Current `mix.json` files stay as-is. Definitions are additive — a new file alongside each mix. |
| Is the running-to-music mapping sound? | The `listener_context` + `energy` fields directly address this. The key insight is that runners respond to *perceived energy*, not raw BPM. The schema captures this distinction. |
| What's the MVP? | Tag 1 stem pack with definitions, write a prompt template, test with Claude. If the output timeline makes musical sense, the concept holds. |

## Next Steps

1. **Define the minimal schema** — `musical`, `role`, `energy`, `mood` only
2. **Tag the forest pack** — 8 stems, manual definitions
3. **Write a prompt template** — "Given these stems and this run plan, produce a timeline"
4. **Test with Claude** — Feed stems + definitions, evaluate the output
5. **Iterate** — Add fields as needed based on output quality
6. **Automate tagging** — Build the `analyze` CLI command
