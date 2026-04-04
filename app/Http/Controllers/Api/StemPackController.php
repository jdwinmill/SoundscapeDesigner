<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\StemPack;
use App\Models\Tag;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class StemPackController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $userId = $request->user()?->id;

        $query = StemPack::query()
            ->where(function ($q) use ($userId) {
                $q->where('is_public', true);
                if ($userId) {
                    $q->orWhere('user_id', $userId);
                }
            });

        if ($tag = $request->query('tag')) {
            $query->whereHas('tags', fn ($q) => $q->where('slug', $tag));
        }

        if ($search = $request->query('search')) {
            $like = $this->likeOperator();
            $query->where(function ($q) use ($search, $like) {
                $q->where('name', $like, "%{$search}%")
                  ->orWhere('genre', $like, "%{$search}%")
                  ->orWhere('mood_summary', $like, "%{$search}%");
            });
        }

        $packs = $query->with(['user:id,name,username', 'stems', 'tags'])
            ->withCount('favorites')
            ->latest()
            ->paginate(20);

        return response()->json($packs);
    }

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'genre' => 'nullable|string|max:100',
            'mood_summary' => 'nullable|string|max:255',
            'key_center' => 'nullable|string|max:10',
            'bpm_center' => 'nullable|numeric|min:30|max:300',
            'energy_range' => 'nullable|array|size:2',
            'energy_range.*' => 'numeric|min:0|max:1',
            'best_for_phases' => 'nullable|array',
            'best_for_phases.*' => 'string',
            'cross_pack_compatible_with' => 'nullable|array',
            'is_public' => 'boolean',
            'tags' => 'nullable|array',
            'tags.*' => 'string|max:50',
        ]);

        $pack = $request->user()->stemPacks()->create($validated);

        if (! empty($validated['tags'])) {
            $this->syncTags($pack, $validated['tags']);
        }

        return response()->json($pack->load('stems', 'tags'), 201);
    }

    public function show(StemPack $stemPack): JsonResponse
    {
        $this->authorizeView($stemPack);

        return response()->json(
            $stemPack->load(['user:id,name,username', 'stems', 'tags'])
                ->loadCount('favorites')
        );
    }

    public function update(Request $request, StemPack $stemPack): JsonResponse
    {
        $this->authorizeOwner($request, $stemPack);

        $validated = $request->validate([
            'name' => 'sometimes|string|max:255',
            'genre' => 'nullable|string|max:100',
            'mood_summary' => 'nullable|string|max:255',
            'key_center' => 'nullable|string|max:10',
            'bpm_center' => 'nullable|numeric|min:30|max:300',
            'energy_range' => 'nullable|array|size:2',
            'energy_range.*' => 'numeric|min:0|max:1',
            'best_for_phases' => 'nullable|array',
            'cross_pack_compatible_with' => 'nullable|array',
            'is_public' => 'boolean',
            'tags' => 'nullable|array',
            'tags.*' => 'string|max:50',
        ]);

        $stemPack->update($validated);

        if (array_key_exists('tags', $validated)) {
            $this->syncTags($stemPack, $validated['tags'] ?? []);
        }

        return response()->json($stemPack->load('stems', 'tags'));
    }

    public function destroy(Request $request, StemPack $stemPack): JsonResponse
    {
        $this->authorizeOwner($request, $stemPack);

        $stemPack->delete();

        return response()->json(null, 204);
    }

    private function authorizeView(StemPack $pack): void
    {
        if (! $pack->is_public && $pack->user_id !== request()->user()?->id) {
            abort(403);
        }
    }

    private function authorizeOwner(Request $request, StemPack $pack): void
    {
        if ($pack->user_id !== $request->user()->id) {
            abort(403);
        }
    }

    private function syncTags(StemPack $pack, array $tagNames): void
    {
        $tagIds = collect($tagNames)->map(function (string $name) {
            return Tag::firstOrCreate(
                ['slug' => Str::slug($name)],
                ['name' => $name, 'type' => 'general'],
            )->id;
        });
        $pack->tags()->sync($tagIds);
    }
}
