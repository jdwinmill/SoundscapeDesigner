<?php

namespace Tests\Feature;

use App\Models\Soundscape;
use App\Models\Stem;
use App\Models\StemPack;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class SoundscapeEditPageTest extends TestCase
{
    use RefreshDatabase;

    public function test_owner_can_access_edit_page(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user)
            ->get("/soundscapes/{$soundscape->slug}/edit")
            ->assertOk()
            ->assertInertia(fn ($page) =>
                $page->component('Soundscapes/Edit')
                    ->has('soundscape')
                    ->where('soundscape.name', $soundscape->name)
            );
    }

    public function test_edit_page_includes_stems_with_pivot_data(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->create(['user_id' => $user->id]);
        $stem = Stem::factory()->create();

        $soundscape->stems()->attach($stem->id, [
            'bpm_range' => json_encode([120, 170]),
            'fade_in' => 8,
            'fade_out' => 12,
            'volume' => 0.7,
            'speed' => 1.0,
            'sort_order' => 0,
        ]);

        $response = $this->actingAs($user)
            ->get("/soundscapes/{$soundscape->slug}/edit");

        $response->assertOk();
        $response->assertInertia(fn ($page) =>
            $page->has('soundscape.stems', 1)
                ->has('soundscape.stems.0.pivot')
        );
    }

    public function test_other_user_cannot_access_edit_page(): void
    {
        $owner = User::factory()->create();
        $other = User::factory()->create();
        $soundscape = Soundscape::factory()->create(['user_id' => $owner->id]);

        $this->actingAs($other)
            ->get("/soundscapes/{$soundscape->slug}/edit")
            ->assertStatus(403);
    }

    public function test_guest_cannot_access_edit_page(): void
    {
        $soundscape = Soundscape::factory()->create();

        $this->get("/soundscapes/{$soundscape->slug}/edit")
            ->assertRedirect('/login');
    }

    public function test_edit_page_includes_tags(): void
    {
        $user = User::factory()->create();
        $soundscape = Soundscape::factory()->create(['user_id' => $user->id]);
        $tag = \App\Models\Tag::factory()->create(['name' => 'running']);
        $soundscape->tags()->attach($tag);

        $response = $this->actingAs($user)
            ->get("/soundscapes/{$soundscape->slug}/edit");

        $response->assertInertia(fn ($page) =>
            $page->has('soundscape.tags', 1)
                ->where('soundscape.tags.0.name', 'running')
        );
    }

    public function test_update_soundscape_via_api_from_edit(): void
    {
        $user = User::factory()->create(['password' => bcrypt('password123')]);
        $soundscape = Soundscape::factory()->create(['user_id' => $user->id, 'name' => 'Original']);
        $stem = Stem::factory()->create();

        $soundscape->stems()->attach($stem->id, [
            'bpm_range' => json_encode([120, 170]),
            'fade_in' => 5, 'fade_out' => 5, 'volume' => 1.0,
            'speed' => 1.0, 'sort_order' => 0,
        ]);

        // Login via session
        $this->post('/login', ['email' => $user->email, 'password' => 'password123']);

        // PUT update
        $response = $this->putJson("/api/soundscapes/{$soundscape->slug}", [
            'name' => 'Updated Name',
            'stems' => [
                [
                    'stem_id' => $stem->id,
                    'bpm_range' => [100, 180],
                    'fade_in' => 10,
                    'fade_out' => 10,
                    'volume' => 0.6,
                    'speed' => 1.0,
                    'speed_curve' => null,
                    'sort_order' => 0,
                ],
            ],
        ]);

        $response->assertOk();
        $this->assertDatabaseHas('soundscapes', ['id' => $soundscape->id, 'name' => 'Updated Name']);
    }
}
