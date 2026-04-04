<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Favorite;
use App\Models\Soundscape;
use App\Models\StemPack;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class FavoriteController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $favorites = $request->user()->favorites()
            ->with('favorable')
            ->latest()
            ->paginate(20);

        return response()->json($favorites);
    }

    public function toggle(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'type' => 'required|string|in:soundscape,stem_pack',
            'id' => 'required|integer',
        ]);

        $model = match ($validated['type']) {
            'soundscape' => Soundscape::findOrFail($validated['id']),
            'stem_pack' => StemPack::findOrFail($validated['id']),
        };

        if (! $model->is_public && $model->user_id !== $request->user()->id) {
            abort(403);
        }

        $existing = $request->user()->favorites()
            ->where('favorable_type', $model::class)
            ->where('favorable_id', $model->id)
            ->first();

        if ($existing) {
            $existing->delete();
            return response()->json(['favorited' => false]);
        }

        $request->user()->favorites()->create([
            'favorable_type' => $model::class,
            'favorable_id' => $model->id,
        ]);

        return response()->json(['favorited' => true], 201);
    }
}
