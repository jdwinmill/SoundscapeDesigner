<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Soundscape;
use App\Models\Tag;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class SoundscapeController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $userId = $request->user()?->id;

        $query = Soundscape::query()
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
                  ->orWhere('description', $like, "%{$search}%");
            });
        }

        $soundscapes = $query->with(['user:id,name,username', 'stems', 'tags'])
            ->withCount('favorites')
            ->latest()
            ->paginate(20);

        return response()->json($soundscapes);
    }

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'nullable|string|max:1000',
            'base_bpm' => 'nullable|numeric|min:30|max:300',
            'is_public' => 'boolean',
            'stems' => 'required|array|min:1',
            'stems.*.stem_id' => 'required|exists:stems,id',
            'stems.*.bpm_range' => 'required|array|size:2',
            'stems.*.bpm_range.*' => 'numeric',
            'stems.*.fade_in' => 'numeric|min:0',
            'stems.*.fade_out' => 'numeric|min:0',
            'stems.*.volume' => 'numeric|min:0|max:1',
            'stems.*.speed' => 'numeric|min:0.1|max:4',
            'stems.*.speed_curve' => 'nullable|array',
            'stems.*.sort_order' => 'integer|min:0',
            'tags' => 'nullable|array',
            'tags.*' => 'string|max:50',
        ]);

        $soundscape = $request->user()->soundscapes()->create($validated);

        $this->syncStems($soundscape, $validated['stems']);

        if (! empty($validated['tags'])) {
            $this->syncTags($soundscape, $validated['tags']);
        }

        return response()->json($soundscape->load('stems', 'tags'), 201);
    }

    public function show(Soundscape $soundscape): JsonResponse
    {
        if (! $soundscape->is_public && $soundscape->user_id !== request()->user()?->id) {
            abort(403);
        }

        return response()->json(
            $soundscape->load(['user:id,name,username', 'stems', 'tags'])
                ->loadCount('favorites')
        );
    }

    public function update(Request $request, Soundscape $soundscape): JsonResponse
    {
        if ($soundscape->user_id !== $request->user()->id) {
            abort(403);
        }

        $validated = $request->validate([
            'name' => 'sometimes|string|max:255',
            'description' => 'nullable|string|max:1000',
            'base_bpm' => 'nullable|numeric|min:30|max:300',
            'is_public' => 'boolean',
            'stems' => 'nullable|array',
            'stems.*.stem_id' => 'required_with:stems|exists:stems,id',
            'stems.*.bpm_range' => 'required_with:stems|array|size:2',
            'stems.*.bpm_range.*' => 'numeric',
            'stems.*.fade_in' => 'numeric|min:0',
            'stems.*.fade_out' => 'numeric|min:0',
            'stems.*.volume' => 'numeric|min:0|max:1',
            'stems.*.speed' => 'numeric|min:0.1|max:4',
            'stems.*.speed_curve' => 'nullable|array',
            'stems.*.sort_order' => 'integer|min:0',
            'tags' => 'nullable|array',
            'tags.*' => 'string|max:50',
        ]);

        $soundscape->update($validated);

        if (array_key_exists('stems', $validated)) {
            $this->syncStems($soundscape, $validated['stems'] ?? []);
        }

        if (array_key_exists('tags', $validated)) {
            $this->syncTags($soundscape, $validated['tags'] ?? []);
        }

        return response()->json($soundscape->load('stems', 'tags'));
    }

    public function destroy(Request $request, Soundscape $soundscape): JsonResponse
    {
        if ($soundscape->user_id !== $request->user()->id) {
            abort(403);
        }

        $soundscape->delete();

        return response()->json(null, 204);
    }

    public function clone(Request $request, Soundscape $soundscape): JsonResponse
    {
        if (! $soundscape->is_public && $soundscape->user_id !== $request->user()->id) {
            abort(403);
        }

        $copy = $soundscape->clone($request->user());

        return response()->json($copy, 201);
    }

    private function syncStems(Soundscape $soundscape, array $stems): void
    {
        $pivotData = [];
        foreach ($stems as $i => $stem) {
            $pivotData[$stem['stem_id']] = [
                'bpm_range' => json_encode($stem['bpm_range']),
                'fade_in' => $stem['fade_in'] ?? 5.0,
                'fade_out' => $stem['fade_out'] ?? 5.0,
                'volume' => $stem['volume'] ?? 1.0,
                'speed' => $stem['speed'] ?? 1.0,
                'speed_curve' => isset($stem['speed_curve']) ? json_encode($stem['speed_curve']) : null,
                'sort_order' => $stem['sort_order'] ?? $i,
            ];
        }
        $soundscape->stems()->sync($pivotData);
    }

    private function syncTags(Soundscape $soundscape, array $tagNames): void
    {
        $tagIds = collect($tagNames)->map(function (string $name) {
            return Tag::firstOrCreate(
                ['slug' => Str::slug($name)],
                ['name' => $name, 'type' => 'general'],
            )->id;
        });
        $soundscape->tags()->sync($tagIds);
    }
}
