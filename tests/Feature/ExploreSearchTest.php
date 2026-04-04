<?php

namespace Tests\Feature;

use App\Models\Soundscape;
use App\Models\StemPack;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ExploreSearchTest extends TestCase
{
    use RefreshDatabase;

    public function test_explore_filters_soundscapes_by_search(): void
    {
        Soundscape::factory()->public()->create(['name' => 'Morning Tempo Run']);
        Soundscape::factory()->public()->create(['name' => 'Chill Evening']);

        $response = $this->get('/explore?search=Morning');

        $response->assertOk();
        $response->assertInertia(fn ($page) =>
            $page->component('Explore')
                ->has('soundscapes.data', 1)
                ->where('soundscapes.data.0.name', 'Morning Tempo Run')
        );
    }

    public function test_explore_filters_packs_by_search(): void
    {
        StemPack::factory()->public()->create(['name' => 'Deep Ambient']);
        StemPack::factory()->public()->create(['name' => 'Hard Techno', 'genre' => 'techno', 'mood_summary' => 'intense energy']);

        $response = $this->get('/explore?search=Ambient');

        $response->assertOk();
        $response->assertInertia(fn ($page) =>
            $page->component('Explore')
                ->has('packs.data', 1)
                ->where('packs.data.0.name', 'Deep Ambient')
        );
    }

    public function test_explore_search_does_not_return_private(): void
    {
        Soundscape::factory()->create(['name' => 'Secret Mix', 'is_public' => false]);
        StemPack::factory()->create(['name' => 'Secret Pack', 'is_public' => false]);

        $response = $this->get('/explore?search=Secret');

        $response->assertInertia(fn ($page) =>
            $page->has('soundscapes.data', 0)
                ->has('packs.data', 0)
        );
    }

    public function test_explore_without_search_returns_all_public(): void
    {
        Soundscape::factory()->public()->count(3)->create();
        StemPack::factory()->public()->count(2)->create();

        $response = $this->get('/explore');

        $response->assertInertia(fn ($page) =>
            $page->has('soundscapes.data', 3)
                ->has('packs.data', 2)
        );
    }
}
