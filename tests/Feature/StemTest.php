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

class StemTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake('public');
    }

    // --- Upload ---

    public function test_upload_stem_to_own_pack(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        $response = $this->actingAs($user, 'sanctum')
            ->postJson("/api/stem-packs/{$pack->slug}/stems", [
                'file' => UploadedFile::fake()->create('kick.wav', 1024, 'audio/wav'),
                'name' => 'Kick Drum',
                'bpm' => 120,
                'role_type' => 'percussive',
                'role_layer' => 'low',
                'role_function' => 'foundation',
            ]);

        $response->assertStatus(201)
            ->assertJsonFragment(['name' => 'Kick Drum']);

        $this->assertDatabaseHas('stems', ['name' => 'Kick Drum', 'stem_pack_id' => $pack->id]);

        // File was stored
        Storage::disk('public')->assertExists($response->json('file_path'));
    }

    public function test_upload_stem_to_other_users_pack_forbidden(): void
    {
        $pack = StemPack::factory()->create();
        $other = User::factory()->create();

        $this->actingAs($other, 'sanctum')
            ->postJson("/api/stem-packs/{$pack->slug}/stems", [
                'file' => UploadedFile::fake()->create('kick.wav', 1024, 'audio/wav'),
                'name' => 'Kick',
            ])
            ->assertStatus(403);
    }

    public function test_upload_requires_auth(): void
    {
        $pack = StemPack::factory()->create();

        $this->postJson("/api/stem-packs/{$pack->slug}/stems", [
            'file' => UploadedFile::fake()->create('kick.wav', 1024, 'audio/wav'),
            'name' => 'Kick',
        ])->assertStatus(401);
    }

    public function test_upload_validates_file_type(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user, 'sanctum')
            ->postJson("/api/stem-packs/{$pack->slug}/stems", [
                'file' => UploadedFile::fake()->create('malware.exe', 1024),
                'name' => 'Bad File',
            ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('file');
    }

    // --- Update ---

    public function test_update_stem_metadata(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);
        $stem = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        $this->actingAs($user, 'sanctum')
            ->putJson("/api/stem-packs/{$pack->slug}/stems/{$stem->id}", [
                'name' => 'Updated Name',
                'intensity' => 0.9,
            ])
            ->assertOk()
            ->assertJsonFragment(['name' => 'Updated Name']);
    }

    // --- Scoping ---

    public function test_update_stem_from_wrong_pack_returns_404(): void
    {
        $user = User::factory()->create();
        $pack1 = StemPack::factory()->create(['user_id' => $user->id]);
        $pack2 = StemPack::factory()->create(['user_id' => $user->id]);
        $stem = Stem::factory()->create(['stem_pack_id' => $pack2->id]);

        $this->actingAs($user, 'sanctum')
            ->putJson("/api/stem-packs/{$pack1->slug}/stems/{$stem->id}", [
                'name' => 'Cross Pack',
            ])
            ->assertStatus(404);
    }

    public function test_delete_stem_from_wrong_pack_returns_404(): void
    {
        $user = User::factory()->create();
        $pack1 = StemPack::factory()->create(['user_id' => $user->id]);
        $pack2 = StemPack::factory()->create(['user_id' => $user->id]);
        $stem = Stem::factory()->create(['stem_pack_id' => $pack2->id]);

        $this->actingAs($user, 'sanctum')
            ->deleteJson("/api/stem-packs/{$pack1->slug}/stems/{$stem->id}")
            ->assertStatus(404);
    }

    // --- Delete / File Cleanup ---

    public function test_delete_stem_removes_file(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        // Upload a real file
        $uploadResponse = $this->actingAs($user, 'sanctum')
            ->postJson("/api/stem-packs/{$pack->slug}/stems", [
                'file' => UploadedFile::fake()->create('kick.wav', 1024, 'audio/wav'),
                'name' => 'Kick',
            ]);

        $filePath = $uploadResponse->json('file_path');
        $stemId = $uploadResponse->json('id');

        Storage::disk('public')->assertExists($filePath);

        // Delete the stem
        $this->actingAs($user, 'sanctum')
            ->deleteJson("/api/stem-packs/{$pack->slug}/stems/{$stemId}")
            ->assertStatus(204);

        Storage::disk('public')->assertMissing($filePath);
    }

    // --- Download Access ---

    public function test_download_from_public_pack_as_guest(): void
    {
        $pack = StemPack::factory()->public()->create();
        $stem = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        // Create a fake file at the stem's path
        Storage::disk('public')->put($stem->file_path, 'fake audio data');

        $this->get("/api/stem-packs/{$pack->slug}/stems/{$stem->id}/download")
            ->assertOk();
    }

    public function test_download_from_private_pack_as_guest_forbidden(): void
    {
        $pack = StemPack::factory()->create(['is_public' => false]);
        $stem = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        Storage::disk('public')->put($stem->file_path, 'fake audio data');

        $this->get("/api/stem-packs/{$pack->slug}/stems/{$stem->id}/download")
            ->assertStatus(403);
    }

    public function test_download_from_private_pack_as_owner(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id, 'is_public' => false]);
        $stem = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        Storage::disk('public')->put($stem->file_path, 'fake audio data');

        $this->actingAs($user, 'sanctum')
            ->get("/api/stem-packs/{$pack->slug}/stems/{$stem->id}/download")
            ->assertOk();
    }

    public function test_download_from_private_pack_when_in_public_soundscape(): void
    {
        $owner = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $owner->id, 'is_public' => false]);
        $stem = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        Storage::disk('public')->put($stem->file_path, 'fake audio data');

        // Attach stem to a public soundscape
        $soundscape = Soundscape::factory()->public()->create(['user_id' => $owner->id]);
        $soundscape->stems()->attach($stem->id, [
            'bpm_range' => json_encode([100, 160]),
            'fade_in' => 5,
            'fade_out' => 5,
            'volume' => 1.0,
            'speed' => 1.0,
            'sort_order' => 0,
        ]);

        // A different user (guest) can download it
        $this->get("/api/stem-packs/{$pack->slug}/stems/{$stem->id}/download")
            ->assertOk();
    }

    public function test_download_from_private_pack_not_in_any_public_soundscape_forbidden(): void
    {
        $owner = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $owner->id, 'is_public' => false]);
        $stem = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        Storage::disk('public')->put($stem->file_path, 'fake audio data');

        // Stem is in a PRIVATE soundscape only
        $soundscape = Soundscape::factory()->create(['user_id' => $owner->id, 'is_public' => false]);
        $soundscape->stems()->attach($stem->id, [
            'bpm_range' => json_encode([100, 160]),
            'fade_in' => 5,
            'fade_out' => 5,
            'volume' => 1.0,
            'speed' => 1.0,
            'sort_order' => 0,
        ]);

        $other = User::factory()->create();
        $this->actingAs($other, 'sanctum')
            ->get("/api/stem-packs/{$pack->slug}/stems/{$stem->id}/download")
            ->assertStatus(403);
    }

    public function test_download_stem_from_wrong_pack_returns_404(): void
    {
        $pack1 = StemPack::factory()->public()->create();
        $pack2 = StemPack::factory()->public()->create();
        $stem = Stem::factory()->create(['stem_pack_id' => $pack2->id]);

        Storage::disk('public')->put($stem->file_path, 'fake audio data');

        $this->get("/api/stem-packs/{$pack1->slug}/stems/{$stem->id}/download")
            ->assertStatus(404);
    }
}
