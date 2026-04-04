<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class UserController extends Controller
{
    public function show(string $username): JsonResponse
    {
        $user = User::where('username', $username)->firstOrFail();

        $stemPacks = $user->stemPacks()
            ->where('is_public', true)
            ->with('tags')
            ->withCount(['stems', 'favorites'])
            ->latest()
            ->get();

        $soundscapes = $user->soundscapes()
            ->where('is_public', true)
            ->with(['stems', 'tags'])
            ->withCount('favorites')
            ->latest()
            ->get();

        return response()->json([
            'user' => [
                'name' => $user->name,
                'username' => $user->username,
                'joined' => $user->created_at,
            ],
            'stem_packs' => $stemPacks,
            'soundscapes' => $soundscapes,
        ]);
    }
}
