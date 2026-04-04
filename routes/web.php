<?php

use App\Http\Controllers\Web\AuthController;
use App\Models\StemPack;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::get('/', fn () => Inertia::render('Home'));
Route::get('/design-tokens', fn () => Inertia::render('DesignTokens'));

Route::get('/explore', function (\Illuminate\Http\Request $request) {
    $search = $request->query('search');
    $like = DB::getDriverName() === 'pgsql' ? 'ilike' : 'like';

    $soundscapeQuery = \App\Models\Soundscape::query()
        ->where('is_public', true)
        ->with(['user:id,name,username', 'tags'])
        ->withCount('favorites');

    $packQuery = StemPack::query()
        ->where('is_public', true)
        ->with(['user:id,name,username', 'tags'])
        ->withCount(['stems', 'favorites']);

    if ($search) {
        $soundscapeQuery->where(function ($q) use ($search, $like) {
            $q->where('name', $like, "%{$search}%")
              ->orWhere('description', $like, "%{$search}%");
        });
        $packQuery->where(function ($q) use ($search, $like) {
            $q->where('name', $like, "%{$search}%")
              ->orWhere('genre', $like, "%{$search}%")
              ->orWhere('mood_summary', $like, "%{$search}%");
        });
    }

    return Inertia::render('Explore', [
        'soundscapes' => $soundscapeQuery->latest()->paginate(20),
        'packs' => $packQuery->latest()->paginate(20),
        'search' => $search ?? '',
    ]);
});

// Auth
Route::middleware('guest')->group(function () {
    Route::get('/login', fn () => Inertia::render('Auth/Login'))->name('login');
    Route::post('/login', [AuthController::class, 'login']);
    Route::get('/register', fn () => Inertia::render('Auth/Register'));
    Route::post('/register', [AuthController::class, 'register']);
});

Route::post('/logout', [AuthController::class, 'logout'])->middleware('auth')->name('logout');

// Authenticated pages
Route::middleware('auth')->group(function () {
    Route::get('/dashboard', function () {
        $user = request()->user();
        return Inertia::render('Dashboard', [
            'packs' => $user->stemPacks()->with('tags')->withCount('stems')->latest()->get(),
            'soundscapes' => $user->soundscapes()->with('tags')->latest()->get(),
        ]);
    });
    Route::get('/packs/create', fn () => Inertia::render('Packs/Create'));
    Route::get('/soundscapes/create', fn () => Inertia::render('Soundscapes/Create'));
});

// Public pack detail (with visibility check)
Route::get('/packs/{stemPack:slug}', function (StemPack $stemPack) {
    if (! $stemPack->is_public && $stemPack->user_id !== request()->user()?->id) {
        abort(403);
    }

    return Inertia::render('Packs/Show', [
        'pack' => $stemPack->load('stems', 'tags', 'user:id,name,username'),
        'isOwner' => $stemPack->user_id === request()->user()?->id,
    ]);
});

// Public soundscape detail (with visibility check)
Route::get('/s/{soundscape:slug}', function (\App\Models\Soundscape $soundscape) {
    if (! $soundscape->is_public && $soundscape->user_id !== request()->user()?->id) {
        abort(403);
    }

    $user = request()->user();
    $isFavorited = $user
        ? $user->favorites()
            ->where('favorable_type', \App\Models\Soundscape::class)
            ->where('favorable_id', $soundscape->id)
            ->exists()
        : false;

    return Inertia::render('Soundscapes/Show', [
        'soundscape' => $soundscape->load('stems', 'tags', 'user:id,name,username')->loadCount('favorites'),
        'isFavorited' => $isFavorited,
    ]);
});

// Public user profile
Route::get('/u/{username}', function (string $username) {
    $user = \App\Models\User::where('username', $username)->firstOrFail();
    return Inertia::render('Users/Profile', [
        'profile' => [
            'name' => $user->name,
            'username' => $user->username,
            'joined' => $user->created_at,
        ],
        'packs' => $user->stemPacks()->where('is_public', true)->with('tags')->withCount('stems', 'favorites')->latest()->get(),
        'soundscapes' => $user->soundscapes()->where('is_public', true)->with('tags')->withCount('favorites')->latest()->get(),
    ]);
});
