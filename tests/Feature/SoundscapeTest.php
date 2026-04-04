<?php

namespace Tests\Feature;

use App\Models\Soundscape;
use App\Models\Stem;
use App\Models\StemPack;
use App\Models\Tag;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class SoundscapeTest extends TestCase
{
    use RefreshDatabase;

    // --- Index / Visibility ---

    public function test_index_returns_public_soundscapes_to_guests(): void
    {
        Soundscape::factory()->public()->create(['name' => 'Public Run']);
        Soundscape::factory()->create(['name' => 'Private Run']);

        $response = $this->getJson('/api/soundscapes');

        $names = collect($response->json('data'))->pluck('name');
        $this->assertContains('Public Run', $names);
        $this->assertNotContains('Private Run', $names);
    }

    public function test_index_returns_own_private_soundscapes(): void
    {
        $user = User::factory()->create();
        Soundscape::factory()->create(['user_id' => $user->id, 'name' => 'My Private']);
        Soundscape::factory()->create(['name' => 'Other Private']);

        $response = $this->actingAs($user, 'sanctum')->getJson('/api/soundscapes');

        $names = collect($response->json('data'))->pluck('name');
        $this->assertContains('My Private', $names);
        $this->assertNotContains('Other Private', $names);
    }

    public function test_index_search_does_not_leak_private_soundscapes(): void
    {
        $other = User::factory()->create();
        Soundscape::factory()->create([
            'user_id' => $other->id,
            'name' => 'Secret Tempo Run',
            'is_public' => false,
        ]);

        $me = User::factory()->create();

        $response = $this->actingAs($me, 'sanctum')
            ->getJson('/api/soundscapes?search=Tempo');

        $this->assertCount(0, $response->json('data'));
    }

    public function test_index_tag_filter_does_not_leak_private_soundscapes(): void
    {
        $other = User::factory()->create();
        $soundscape = Soundscape::factory()->create([
            'user_id' => $other->id,
            'is_public' => false,
        ]);
        $tag = Tag::factory()->create(['slug' => 'running']);
        $soundscape->tags()->attach($tag);

        $me = User::factory()->create();

        $response = $this->actingAs($me, 'sanctum')
            ->getJson('/api/soundscapes?tag=running');

        $this->assertCount(0, $response->json('data'));
    }

    // --- Show ---

    public function test_show_public_soundscape(): void
    {
        $soundscape = Soundscape::factory()->public()->create();

        $this->getJson("/api/soundscapes/{$soundscape->slug}")
            ->assertOk()
            ->assertJsonFragment(['name' => $soundscape->name]);
    }

    public function test_show_private_soundscape_as_owner(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user, 'sanctum')
            ->getJson("/api/soundscapes/{$soundscape->slug}")
            ->assertOk();
    }

    public function test_show_private_soundscape_as_other_user_forbidden(): void
    {
        $soundscape = Soundscape::factory()->create();
        $other = User::factory()->create();

        $this->actingAs($other, 'sanctum')
            ->getJson("/api/soundscapes/{$soundscape->slug}")
            ->assertStatus(403);
    }

    // --- Create with Stems ---

    public function test_create_soundscape_with_stems_and_tags(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);
        $stem1 = Stem::factory()->create(['stem_pack_id' => $pack->id]);
        $stem2 = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        $response = $this->actingAs($user, 'sanctum')->postJson('/api/soundscapes', [
            'name' => 'Morning Run',
            'base_bpm' => 160,
            'stems' => [
                [
                    'stem_id' => $stem1->id,
                    'bpm_range' => [120, 160],
                    'fade_in' => 5,
                    'fade_out' => 10,
                    'volume' => 0.8,
                    'speed' => 1.0,
                ],
                [
                    'stem_id' => $stem2->id,
                    'bpm_range' => [140, 180],
                    'fade_in' => 3,
                    'fade_out' => 5,
                    'volume' => 0.6,
                    'speed' => 1.2,
                ],
            ],
            'tags' => ['morning', 'tempo'],
        ]);

        $response->assertStatus(201);
        $this->assertDatabaseHas('soundscapes', ['name' => 'Morning Run', 'user_id' => $user->id]);
        $this->assertDatabaseCount('soundscape_stem', 2);
        $this->assertCount(2, $response->json('tags'));
    }

    public function test_create_soundscape_requires_stems(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user, 'sanctum')
            ->postJson('/api/soundscapes', [
                'name' => 'Empty',
                'base_bpm' => 150,
                'stems' => [],
            ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('stems');
    }

    // --- Config Accessor ---

    public function test_config_accessor_computes_from_pivot(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->create(['user_id' => $user->id, 'base_bpm' => 150]);
        $stem = Stem::factory()->create(['file_path' => 'stems/1/kick.wav']);

        $soundscape->stems()->attach($stem->id, [
            'bpm_range' => json_encode([100, 160]),
            'fade_in' => 5,
            'fade_out' => 10,
            'volume' => 0.8,
            'speed' => 1.0,
            'sort_order' => 0,
        ]);

        $response = $this->actingAs($user, 'sanctum')
            ->getJson("/api/soundscapes/{$soundscape->slug}");

        $config = $response->json('config');
        $this->assertEquals(150, $config['baseBPM']);
        $this->assertCount(1, $config['stems']);
        $this->assertEquals('kick.wav', $config['stems'][0]['file']);
        $this->assertEquals([100, 160], $config['stems'][0]['bpmRange']);
        $this->assertEquals(0.8, $config['stems'][0]['volume']);
    }

    // --- Update ---

    public function test_update_soundscape_syncs_stems(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);
        $stem1 = Stem::factory()->create(['stem_pack_id' => $pack->id]);
        $stem2 = Stem::factory()->create(['stem_pack_id' => $pack->id]);
        $stem3 = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        $soundscape = Soundscape::factory()->create(['user_id' => $user->id]);
        $soundscape->stems()->attach($stem1->id, [
            'bpm_range' => json_encode([100, 160]),
            'fade_in' => 5, 'fade_out' => 5, 'volume' => 1, 'speed' => 1, 'sort_order' => 0,
        ]);

        // Update to use stem2 and stem3 instead
        $this->actingAs($user, 'sanctum')
            ->putJson("/api/soundscapes/{$soundscape->slug}", [
                'stems' => [
                    ['stem_id' => $stem2->id, 'bpm_range' => [120, 170], 'volume' => 0.5],
                    ['stem_id' => $stem3->id, 'bpm_range' => [130, 180], 'volume' => 0.7],
                ],
            ])
            ->assertOk();

        $soundscape->refresh();
        $stemIds = $soundscape->stems->pluck('id')->all();
        $this->assertContains($stem2->id, $stemIds);
        $this->assertContains($stem3->id, $stemIds);
        $this->assertNotContains($stem1->id, $stemIds);
    }

    public function test_update_other_users_soundscape_forbidden(): void
    {
        $soundscape = Soundscape::factory()->create();
        $other = User::factory()->create();

        $this->actingAs($other, 'sanctum')
            ->putJson("/api/soundscapes/{$soundscape->slug}", ['name' => 'Hacked'])
            ->assertStatus(403);
    }

    // --- Delete ---

    public function test_delete_own_soundscape(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user, 'sanctum')
            ->deleteJson("/api/soundscapes/{$soundscape->slug}")
            ->assertStatus(204);

        $this->assertDatabaseMissing('soundscapes', ['id' => $soundscape->id]);
    }

    public function test_delete_other_users_soundscape_forbidden(): void
    {
        $soundscape = Soundscape::factory()->create();
        $other = User::factory()->create();

        $this->actingAs($other, 'sanctum')
            ->deleteJson("/api/soundscapes/{$soundscape->slug}")
            ->assertStatus(403);
    }

    // --- Clone ---

    public function test_clone_public_soundscape(): void
    {
        $owner = User::factory()->create();
        $soundscape = Soundscape::factory()->public()->create([
            'user_id' => $owner->id,
            'name' => 'Original',
        ]);
        $stem = Stem::factory()->create();
        $soundscape->stems()->attach($stem->id, [
            'bpm_range' => json_encode([100, 160]),
            'fade_in' => 5, 'fade_out' => 10, 'volume' => 0.8,
            'speed' => 1.0, 'sort_order' => 0,
        ]);
        $tag = Tag::factory()->create();
        $soundscape->tags()->attach($tag);

        $cloner = User::factory()->create();

        $response = $this->actingAs($cloner, 'sanctum')
            ->postJson("/api/soundscapes/{$soundscape->slug}/clone");

        $response->assertStatus(201);
        $this->assertEquals('Original (copy)', $response->json('name'));
        $this->assertEquals($cloner->id, $response->json('user_id'));
        $this->assertFalse($response->json('is_public'));

        // Stem pivot data was copied
        $this->assertCount(1, $response->json('stems'));

        // Tags were copied
        $this->assertCount(1, $response->json('tags'));

        // Original is untouched
        $this->assertDatabaseHas('soundscapes', ['id' => $soundscape->id, 'name' => 'Original']);
    }

    public function test_clone_private_soundscape_by_non_owner_forbidden(): void
    {
        $soundscape = Soundscape::factory()->create(['is_public' => false]);
        $other = User::factory()->create();

        $this->actingAs($other, 'sanctum')
            ->postJson("/api/soundscapes/{$soundscape->slug}/clone")
            ->assertStatus(403);
    }

    public function test_clone_own_private_soundscape(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->create([
            'user_id' => $user->id,
            'is_public' => false,
        ]);

        $this->actingAs($user, 'sanctum')
            ->postJson("/api/soundscapes/{$soundscape->slug}/clone")
            ->assertStatus(201);

        // Now there are 2 soundscapes for this user
        $this->assertEquals(2, Soundscape::where('user_id', $user->id)->count());
    }

    public function test_clone_requires_auth(): void
    {
        $soundscape = Soundscape::factory()->public()->create();

        $this->postJson("/api/soundscapes/{$soundscape->slug}/clone")
            ->assertStatus(401);
    }
}
