<?php

namespace Tests\Feature;

use App\Models\Soundscape;
use App\Models\StemPack;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class FavoriteTest extends TestCase
{
    use RefreshDatabase;

    public function test_toggle_favorite_on_soundscape(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->public()->create();

        // Favorite it
        $response = $this->actingAs($user, 'sanctum')
            ->postJson('/api/favorites/toggle', [
                'type' => 'soundscape',
                'id' => $soundscape->id,
            ]);

        $response->assertStatus(201)
            ->assertJsonFragment(['favorited' => true]);

        $this->assertDatabaseHas('favorites', [
            'user_id' => $user->id,
            'favorable_type' => Soundscape::class,
            'favorable_id' => $soundscape->id,
        ]);

        // Unfavorite it
        $response = $this->actingAs($user, 'sanctum')
            ->postJson('/api/favorites/toggle', [
                'type' => 'soundscape',
                'id' => $soundscape->id,
            ]);

        $response->assertOk()
            ->assertJsonFragment(['favorited' => false]);

        $this->assertDatabaseMissing('favorites', [
            'user_id' => $user->id,
            'favorable_type' => Soundscape::class,
            'favorable_id' => $soundscape->id,
        ]);
    }

    public function test_toggle_favorite_on_stem_pack(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->public()->create();

        $this->actingAs($user, 'sanctum')
            ->postJson('/api/favorites/toggle', [
                'type' => 'stem_pack',
                'id' => $pack->id,
            ])
            ->assertStatus(201)
            ->assertJsonFragment(['favorited' => true]);

        $this->assertDatabaseHas('favorites', [
            'user_id' => $user->id,
            'favorable_type' => StemPack::class,
            'favorable_id' => $pack->id,
        ]);
    }

    public function test_cannot_favorite_private_resource_of_other_user(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->create(['is_public' => false]);

        $this->actingAs($user, 'sanctum')
            ->postJson('/api/favorites/toggle', [
                'type' => 'soundscape',
                'id' => $soundscape->id,
            ])
            ->assertStatus(403);
    }

    public function test_can_favorite_own_private_resource(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->create([
            'user_id' => $user->id,
            'is_public' => false,
        ]);

        $this->actingAs($user, 'sanctum')
            ->postJson('/api/favorites/toggle', [
                'type' => 'soundscape',
                'id' => $soundscape->id,
            ])
            ->assertStatus(201);
    }

    public function test_list_favorites(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->public()->create();
        $pack = StemPack::factory()->public()->create();

        // Favorite both
        $this->actingAs($user, 'sanctum')
            ->postJson('/api/favorites/toggle', ['type' => 'soundscape', 'id' => $soundscape->id]);
        $this->actingAs($user, 'sanctum')
            ->postJson('/api/favorites/toggle', ['type' => 'stem_pack', 'id' => $pack->id]);

        $response = $this->actingAs($user, 'sanctum')
            ->getJson('/api/favorites');

        $response->assertOk();
        $this->assertCount(2, $response->json('data'));
    }

    public function test_favorites_require_auth(): void
    {
        $this->getJson('/api/favorites')->assertStatus(401);
        $this->postJson('/api/favorites/toggle', [
            'type' => 'soundscape',
            'id' => 1,
        ])->assertStatus(401);
    }

    public function test_toggle_validates_type(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user, 'sanctum')
            ->postJson('/api/favorites/toggle', [
                'type' => 'invalid',
                'id' => 1,
            ])
            ->assertStatus(422)
            ->assertJsonValidationErrors('type');
    }
}
