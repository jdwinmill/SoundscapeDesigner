<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\FavoriteController;
use App\Http\Controllers\Api\SoundscapeController;
use App\Http\Controllers\Api\StemController;
use App\Http\Controllers\Api\StemPackController;
use App\Http\Controllers\Api\TagController;
use App\Http\Controllers\Api\UserController;
use Illuminate\Support\Facades\Route;

// Auth
Route::middleware('throttle:5,1')->group(function () {
    Route::post('/register', [AuthController::class, 'register']);
    Route::post('/login', [AuthController::class, 'login']);
});

// Public browsing
Route::get('/stem-packs', [StemPackController::class, 'index']);
Route::get('/stem-packs/{stemPack}', [StemPackController::class, 'show']);
Route::get('/stem-packs/{stemPack}/stems/{stem}/download', [StemController::class, 'download']);
Route::get('/soundscapes', [SoundscapeController::class, 'index']);
Route::get('/soundscapes/{soundscape}', [SoundscapeController::class, 'show']);
Route::get('/tags', [TagController::class, 'index']);
Route::get('/users/{username}', [UserController::class, 'show']);

// Authenticated routes
Route::middleware('auth:sanctum')->group(function () {
    // Auth
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/me', [AuthController::class, 'me']);

    // Stem packs
    Route::post('/stem-packs', [StemPackController::class, 'store']);
    Route::put('/stem-packs/{stemPack}', [StemPackController::class, 'update']);
    Route::delete('/stem-packs/{stemPack}', [StemPackController::class, 'destroy']);

    // Stems (nested under packs)
    Route::post('/stem-packs/{stemPack}/stems', [StemController::class, 'store']);
    Route::put('/stem-packs/{stemPack}/stems/{stem}', [StemController::class, 'update']);
    Route::delete('/stem-packs/{stemPack}/stems/{stem}', [StemController::class, 'destroy']);

    // Soundscapes
    Route::post('/soundscapes', [SoundscapeController::class, 'store']);
    Route::put('/soundscapes/{soundscape}', [SoundscapeController::class, 'update']);
    Route::delete('/soundscapes/{soundscape}', [SoundscapeController::class, 'destroy']);
    Route::post('/soundscapes/{soundscape}/clone', [SoundscapeController::class, 'clone']);

    // Favorites
    Route::get('/favorites', [FavoriteController::class, 'index']);
    Route::post('/favorites/toggle', [FavoriteController::class, 'toggle']);
});
