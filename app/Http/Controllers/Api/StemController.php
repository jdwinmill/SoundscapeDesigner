<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Stem;
use App\Models\StemPack;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;

class StemController extends Controller
{
    public function store(Request $request, StemPack $stemPack): JsonResponse
    {
        $this->authorizeOwner($request, $stemPack);

        $validated = $request->validate([
            'file' => 'required|file|mimes:wav,mp3,ogg,flac,aiff|max:51200',
            'name' => 'required|string|max:255',
            'duration_s' => 'nullable|numeric|min:0',
            'loopable' => 'boolean',
            'key' => 'nullable|string|max:10',
            'bpm' => 'nullable|numeric|min:30|max:300',
            'scale' => 'nullable|string|max:50',
            'time_signature' => 'nullable|string|max:10',
            'key_confidence' => 'nullable|numeric|min:0|max:1',
            'role_type' => 'nullable|string|in:rhythmic,melodic,textural,harmonic,percussive',
            'role_layer' => 'nullable|string|in:low,mid,high,full',
            'role_function' => 'nullable|string|in:foundation,hook,fill,accent,atmosphere,drive',
            'intensity' => 'nullable|numeric|min:0|max:1',
            'drive' => 'nullable|numeric|min:0|max:1',
            'groove' => 'nullable|numeric|min:0|max:1',
            'mood_tags' => 'nullable|array',
            'valence' => 'nullable|numeric|min:0|max:1',
            'arousal' => 'nullable|numeric|min:0|max:1',
            'brightness' => 'nullable|numeric|min:0|max:1',
            'density' => 'nullable|numeric|min:0|max:1',
            'space' => 'nullable|numeric|min:0|max:1',
            'warmth' => 'nullable|numeric|min:0|max:1',
            'solo_capable' => 'boolean',
            'intro_suitable' => 'boolean',
            'climax_suitable' => 'boolean',
            'fade_in_beats' => 'nullable|integer|min:0',
            'fade_out_beats' => 'nullable|integer|min:0',
            'entry_point' => 'nullable|string|in:downbeat,any,pickup',
            'exit_style' => 'nullable|string|in:fade,cut,filter_sweep',
            'best_for' => 'nullable|array',
            'avoid_for' => 'nullable|array',
        ]);

        $path = $request->file('file')->store(
            "stems/{$stemPack->id}",
            'public'
        );

        $validated['file_path'] = $path;
        unset($validated['file']);

        $stem = $stemPack->stems()->create($validated);

        return response()->json($stem, 201);
    }

    public function update(Request $request, StemPack $stemPack, Stem $stem): JsonResponse
    {
        $this->authorizeOwner($request, $stemPack);
        $this->verifyStemBelongsToPack($stem, $stemPack);

        $validated = $request->validate([
            'name' => 'sometimes|string|max:255',
            'loopable' => 'boolean',
            'key' => 'nullable|string|max:10',
            'bpm' => 'nullable|numeric|min:30|max:300',
            'scale' => 'nullable|string|max:50',
            'role_type' => 'nullable|string|in:rhythmic,melodic,textural,harmonic,percussive',
            'role_layer' => 'nullable|string|in:low,mid,high,full',
            'role_function' => 'nullable|string|in:foundation,hook,fill,accent,atmosphere,drive',
            'intensity' => 'nullable|numeric|min:0|max:1',
            'drive' => 'nullable|numeric|min:0|max:1',
            'groove' => 'nullable|numeric|min:0|max:1',
            'mood_tags' => 'nullable|array',
            'valence' => 'nullable|numeric|min:0|max:1',
            'arousal' => 'nullable|numeric|min:0|max:1',
            'brightness' => 'nullable|numeric|min:0|max:1',
            'density' => 'nullable|numeric|min:0|max:1',
            'space' => 'nullable|numeric|min:0|max:1',
            'warmth' => 'nullable|numeric|min:0|max:1',
            'solo_capable' => 'boolean',
            'intro_suitable' => 'boolean',
            'climax_suitable' => 'boolean',
            'best_for' => 'nullable|array',
            'avoid_for' => 'nullable|array',
        ]);

        $stem->update($validated);

        return response()->json($stem);
    }

    public function destroy(Request $request, StemPack $stemPack, Stem $stem): JsonResponse
    {
        $this->authorizeOwner($request, $stemPack);
        $this->verifyStemBelongsToPack($stem, $stemPack);

        Storage::disk('public')->delete($stem->file_path);
        $stem->delete();

        return response()->json(null, 204);
    }

    public function download(StemPack $stemPack, Stem $stem)
    {
        $this->verifyStemBelongsToPack($stem, $stemPack);

        $isOwner = $stemPack->user_id === request()->user()?->id;
        $isPublicPack = $stemPack->is_public;
        $isInPublicSoundscape = $stem->isInPublicSoundscape();

        if (! $isOwner && ! $isPublicPack && ! $isInPublicSoundscape) {
            abort(403);
        }

        return Storage::disk('public')->download($stem->file_path, $stem->name);
    }

    private function authorizeOwner(Request $request, StemPack $pack): void
    {
        if ($pack->user_id !== $request->user()->id) {
            abort(403);
        }
    }

    private function verifyStemBelongsToPack(Stem $stem, StemPack $pack): void
    {
        if ($stem->stem_pack_id !== $pack->id) {
            abort(404);
        }
    }
}
