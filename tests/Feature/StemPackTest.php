<?php

namespace Tests\Feature;

use App\Models\Stem;
use App\Models\StemPack;
use App\Models\Tag;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class StemPackTest extends TestCase
{
    use RefreshDatabase;

    // --- Index / Visibility ---

    public function test_index_returns_public_packs_to_guests(): void
    {
        StemPack::factory()->public()->create(['name' => 'Public Pack']);
        StemPack::factory()->create(['name' => 'Private Pack']);

        $response = $this->getJson('/api/stem-packs');

        $response->assertOk();

        $names = collect($response->json('data'))->pluck('name');
        $this->assertContains('Public Pack', $names);
        $this->assertNotContains('Private Pack', $names);
    }

    public function test_index_returns_own_private_packs_to_owner(): void
    {
        $user = User::factory()->create();
        StemPack::factory()->create(['user_id' => $user->id, 'name' => 'My Private']);
        StemPack::factory()->create(['name' => 'Other Private']);

        $response = $this->actingAs($user, 'sanctum')->getJson('/api/stem-packs');

        $names = collect($response->json('data'))->pluck('name');
        $this->assertContains('My Private', $names);
        $this->assertNotContains('Other Private', $names);
    }

    public function test_index_search_does_not_leak_private_packs(): void
    {
        $other = User::factory()->create();
        StemPack::factory()->create([
            'user_id' => $other->id,
            'name' => 'Secret Electronic Pack',
            'genre' => 'electronic',
            'is_public' => false,
        ]);

        $me = User::factory()->create();

        $response = $this->actingAs($me, 'sanctum')
            ->getJson('/api/stem-packs?search=Electronic');

        $this->assertCount(0, $response->json('data'));
    }

    public function test_index_tag_filter_does_not_leak_private_packs(): void
    {
        $other = User::factory()->create();
        $pack = StemPack::factory()->create([
            'user_id' => $other->id,
            'is_public' => false,
        ]);
        $tag = Tag::factory()->create(['name' => 'chill', 'slug' => 'chill']);
        $pack->tags()->attach($tag);

        $me = User::factory()->create();

        $response = $this->actingAs($me, 'sanctum')
            ->getJson('/api/stem-packs?tag=chill');

        $this->assertCount(0, $response->json('data'));
    }

    public function test_index_search_returns_matching_public_packs(): void
    {
        StemPack::factory()->public()->create(['name' => 'Chill Vibes']);
        StemPack::factory()->public()->create(['name' => 'High Energy']);

        $response = $this->getJson('/api/stem-packs?search=Chill');

        $names = collect($response->json('data'))->pluck('name');
        $this->assertContains('Chill Vibes', $names);
        $this->assertNotContains('High Energy', $names);
    }

    // --- Show ---

    public function test_show_public_pack_as_guest(): void
    {
        $pack = StemPack::factory()->public()->create();

        $this->getJson("/api/stem-packs/{$pack->slug}")
            ->assertOk()
            ->assertJsonFragment(['name' => $pack->name]);
    }

    public function test_show_private_pack_as_owner(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user, 'sanctum')
            ->getJson("/api/stem-packs/{$pack->slug}")
            ->assertOk();
    }

    public function test_show_private_pack_as_other_user_forbidden(): void
    {
        $pack = StemPack::factory()->create();
        $other = User::factory()->create();

        $this->actingAs($other, 'sanctum')
            ->getJson("/api/stem-packs/{$pack->slug}")
            ->assertStatus(403);
    }

    public function test_show_private_pack_as_guest_forbidden(): void
    {
        $pack = StemPack::factory()->create();

        $this->getJson("/api/stem-packs/{$pack->slug}")
            ->assertStatus(403);
    }

    // --- Create ---

    public function test_create_pack_requires_auth(): void
    {
        $this->postJson('/api/stem-packs', ['name' => 'Test'])
            ->assertStatus(401);
    }

    public function test_create_pack_with_tags(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user, 'sanctum')->postJson('/api/stem-packs', [
            'name' => 'My Pack',
            'genre' => 'ambient',
            'bpm_center' => 120,
            'tags' => ['running', 'chill'],
        ]);

        $response->assertStatus(201);
        $this->assertDatabaseHas('stem_packs', ['name' => 'My Pack', 'user_id' => $user->id]);
        $this->assertCount(2, $response->json('tags'));
        $this->assertDatabaseHas('tags', ['slug' => 'running']);
        $this->assertDatabaseHas('tags', ['slug' => 'chill']);
    }

    public function test_create_pack_auto_generates_slug(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user, 'sanctum')->postJson('/api/stem-packs', [
            'name' => 'My Cool Pack',
        ]);

        $response->assertStatus(201);
        $slug = $response->json('slug');
        $this->assertStringStartsWith('my-cool-pack-', $slug);
    }

    // --- Update ---

    public function test_update_own_pack(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user, 'sanctum')
            ->putJson("/api/stem-packs/{$pack->slug}", ['name' => 'Updated'])
            ->assertOk()
            ->assertJsonFragment(['name' => 'Updated']);
    }

    public function test_update_other_users_pack_forbidden(): void
    {
        $pack = StemPack::factory()->create();
        $other = User::factory()->create();

        $this->actingAs($other, 'sanctum')
            ->putJson("/api/stem-packs/{$pack->slug}", ['name' => 'Hacked'])
            ->assertStatus(403);
    }

    // --- Delete ---

    public function test_delete_own_pack(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user, 'sanctum')
            ->deleteJson("/api/stem-packs/{$pack->slug}")
            ->assertStatus(204);

        $this->assertDatabaseMissing('stem_packs', ['id' => $pack->id]);
    }

    public function test_delete_other_users_pack_forbidden(): void
    {
        $pack = StemPack::factory()->create();
        $other = User::factory()->create();

        $this->actingAs($other, 'sanctum')
            ->deleteJson("/api/stem-packs/{$pack->slug}")
            ->assertStatus(403);
    }

    public function test_delete_pack_cascades_to_stems(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);
        $stem = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        $this->actingAs($user, 'sanctum')
            ->deleteJson("/api/stem-packs/{$pack->slug}")
            ->assertStatus(204);

        $this->assertDatabaseMissing('stems', ['id' => $stem->id]);
    }
}
