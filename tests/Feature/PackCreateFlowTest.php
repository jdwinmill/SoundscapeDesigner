<?php

namespace Tests\Feature;

use App\Models\StemPack;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class PackCreateFlowTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake('public');
    }

    // --- Page loads ---

    public function test_create_pack_page_loads(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)->get('/packs/create')->assertOk();
    }

    // --- Create pack (minimal — just a name) ---

    public function test_create_pack_with_just_a_name(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user);

        $response = $this->postJson('/api/stem-packs', [
            'name' => 'My Loops',
        ]);

        $response->assertStatus(201);
        $this->assertDatabaseHas('stem_packs', [
            'name' => 'My Loops',
            'user_id' => $user->id,
        ]);
    }

    // --- Upload stems to the pack ---

    public function test_upload_multiple_stems_to_pack(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user, 'sanctum');

        // Upload first stem
        $this->postJson("/api/stem-packs/{$pack->slug}/stems", [
            'file' => UploadedFile::fake()->create('kick.wav', 1024, 'audio/wav'),
            'name' => 'Kick',
        ])->assertStatus(201);

        // Upload second stem
        $this->postJson("/api/stem-packs/{$pack->slug}/stems", [
            'file' => UploadedFile::fake()->create('snare.wav', 1024, 'audio/wav'),
            'name' => 'Snare',
        ])->assertStatus(201);

        // Upload third stem
        $this->postJson("/api/stem-packs/{$pack->slug}/stems", [
            'file' => UploadedFile::fake()->create('pad.wav', 2048, 'audio/wav'),
            'name' => 'Pad',
        ])->assertStatus(201);

        $this->assertDatabaseCount('stems', 3);
        $this->assertEquals(3, $pack->stems()->count());
    }

    // --- Pack name is required ---

    public function test_create_pack_requires_name(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user, 'sanctum')
            ->postJson('/api/stem-packs', [])
            ->assertStatus(422)
            ->assertJsonValidationErrors('name');
    }

    // --- Optional metadata can be added ---

    public function test_create_pack_with_optional_metadata(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user, 'sanctum');

        $response = $this->postJson('/api/stem-packs', [
            'name' => 'Chill Vibes',
            'genre' => 'lo-fi',
            'tags' => ['chill', 'running'],
        ]);

        $response->assertStatus(201);
        $this->assertEquals('lo-fi', $response->json('genre'));
        $this->assertCount(2, $response->json('tags'));
    }

    // --- Full flow: create pack then upload stems (simulating the single-page experience) ---

    public function test_full_create_flow_pack_then_stems(): void
    {
        $user = User::factory()->create(['password' => bcrypt('password123')]);

        // Login via web session
        $this->post('/login', [
            'email' => $user->email,
            'password' => 'password123',
        ]);

        // Step 1: Create the pack via API
        $packResponse = $this->postJson('/api/stem-packs', [
            'name' => 'Morning Run Kit',
        ]);

        $packResponse->assertStatus(201);
        $slug = $packResponse->json('slug');

        // Step 2: Upload stems to it
        $this->postJson("/api/stem-packs/{$slug}/stems", [
            'file' => UploadedFile::fake()->create('beat.wav', 1024, 'audio/wav'),
            'name' => 'Beat',
        ])->assertStatus(201);

        $this->postJson("/api/stem-packs/{$slug}/stems", [
            'file' => UploadedFile::fake()->create('ambient.wav', 2048, 'audio/wav'),
            'name' => 'Ambient Pad',
        ])->assertStatus(201);

        // Verify the pack has 2 stems
        $pack = StemPack::where('slug', $slug)->first();
        $this->assertEquals(2, $pack->stems()->count());

        // Step 3: Pack detail page shows both stems
        $this->get("/packs/{$slug}")
            ->assertOk()
            ->assertInertia(fn ($page) =>
                $page->component('Packs/Show')
                    ->has('pack.stems', 2)
            );
    }

    // --- Stem name auto-derived from filename ---

    public function test_stem_name_is_required(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user, 'sanctum')
            ->postJson("/api/stem-packs/{$pack->slug}/stems", [
                'file' => UploadedFile::fake()->create('kick.wav', 1024, 'audio/wav'),
            ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('name');
    }

    // --- Delete stem from pack ---

    public function test_owner_can_delete_stem_from_pack(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user, 'sanctum');

        $upload = $this->postJson("/api/stem-packs/{$pack->slug}/stems", [
            'file' => UploadedFile::fake()->create('kick.wav', 1024, 'audio/wav'),
            'name' => 'Kick',
        ]);

        $stemId = $upload->json('id');

        $this->deleteJson("/api/stem-packs/{$pack->slug}/stems/{$stemId}")
            ->assertStatus(204);

        $this->assertDatabaseMissing('stems', ['id' => $stemId]);
    }
}
