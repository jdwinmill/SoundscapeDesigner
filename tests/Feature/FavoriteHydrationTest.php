<?php

namespace Tests\Feature;

use App\Models\Favorite;
use App\Models\Soundscape;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class FavoriteHydrationTest extends TestCase
{
    use RefreshDatabase;

    public function test_soundscape_detail_shows_favorited_true_when_user_has_favorited(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->public()->create();

        Favorite::create([
            'user_id' => $user->id,
            'favorable_type' => Soundscape::class,
            'favorable_id' => $soundscape->id,
        ]);

        $response = $this->actingAs($user)->get("/s/{$soundscape->slug}");

        $response->assertOk();
        $response->assertInertia(fn ($page) =>
            $page->component('Soundscapes/Show')
                ->where('isFavorited', true)
        );
    }

    public function test_soundscape_detail_shows_favorited_false_when_not_favorited(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->public()->create();

        $response = $this->actingAs($user)->get("/s/{$soundscape->slug}");

        $response->assertInertia(fn ($page) =>
            $page->where('isFavorited', false)
        );
    }

    public function test_soundscape_detail_shows_favorited_false_for_guests(): void
    {
        $soundscape = Soundscape::factory()->public()->create();

        $response = $this->get("/s/{$soundscape->slug}");

        $response->assertInertia(fn ($page) =>
            $page->where('isFavorited', false)
        );
    }
}
