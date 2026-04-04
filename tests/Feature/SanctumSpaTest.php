<?php

namespace Tests\Feature;

use App\Models\Soundscape;
use App\Models\Stem;
use App\Models\StemPack;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class SanctumSpaTest extends TestCase
{
    use RefreshDatabase;

    /**
     * Simulate a browser session-authenticated API call.
     * Web login sets the session, then API calls with that session
     * should be authenticated via Sanctum's stateful middleware.
     */
    public function test_session_authenticated_user_can_create_pack_via_api(): void
    {
        $user = User::factory()->create(['password' => bcrypt('password123')]);

        // Log in via web (sets session)
        $this->post('/login', [
            'email' => $user->email,
            'password' => 'password123',
        ]);

        // Now hit the API with session auth
        $response = $this->postJson('/api/stem-packs', [
            'name' => 'Browser Pack',
        ]);

        $response->assertStatus(201);
        $this->assertDatabaseHas('stem_packs', ['name' => 'Browser Pack', 'user_id' => $user->id]);
    }

    public function test_session_authenticated_user_can_upload_stem_via_api(): void
    {
        Storage::fake('public');

        $user = User::factory()->create(['password' => bcrypt('password123')]);
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        $this->post('/login', [
            'email' => $user->email,
            'password' => 'password123',
        ]);

        $response = $this->postJson("/api/stem-packs/{$pack->slug}/stems", [
            'file' => UploadedFile::fake()->create('kick.wav', 1024, 'audio/wav'),
            'name' => 'Kick',
        ]);

        $response->assertStatus(201);
    }

    public function test_session_authenticated_user_can_toggle_favorite_via_api(): void
    {
        $user = User::factory()->create(['password' => bcrypt('password123')]);
        $soundscape = Soundscape::factory()->public()->create();

        $this->post('/login', [
            'email' => $user->email,
            'password' => 'password123',
        ]);

        $response = $this->postJson('/api/favorites/toggle', [
            'type' => 'soundscape',
            'id' => $soundscape->id,
        ]);

        $response->assertStatus(201)
            ->assertJsonFragment(['favorited' => true]);
    }

    public function test_session_authenticated_user_can_clone_soundscape_via_api(): void
    {
        $user = User::factory()->create(['password' => bcrypt('password123')]);
        $soundscape = Soundscape::factory()->public()->create();

        $this->post('/login', [
            'email' => $user->email,
            'password' => 'password123',
        ]);

        $response = $this->postJson("/api/soundscapes/{$soundscape->slug}/clone");

        $response->assertStatus(201);
    }

    public function test_unauthenticated_api_call_returns_401(): void
    {
        $this->postJson('/api/stem-packs', ['name' => 'Nope'])
            ->assertStatus(401);
    }
}
