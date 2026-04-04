<?php

namespace Tests\Feature;

use App\Models\Soundscape;
use App\Models\Stem;
use App\Models\StemPack;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class WebPageTest extends TestCase
{
    use RefreshDatabase;

    // --- Public pages ---

    public function test_home_page_loads(): void
    {
        $this->get('/')->assertOk();
    }

    public function test_explore_page_loads_with_data(): void
    {
        StemPack::factory()->public()->create();
        Soundscape::factory()->public()->create();

        $this->get('/explore')->assertOk();
    }

    public function test_design_tokens_page_loads(): void
    {
        $this->get('/design-tokens')->assertOk();
    }

    // --- Public pack detail ---

    public function test_guest_can_view_public_pack(): void
    {
        $pack = StemPack::factory()->public()->create();

        $this->get("/packs/{$pack->slug}")->assertOk();
    }

    public function test_guest_cannot_view_private_pack(): void
    {
        $pack = StemPack::factory()->create(['is_public' => false]);

        $this->get("/packs/{$pack->slug}")->assertStatus(403);
    }

    public function test_owner_can_view_own_private_pack(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id, 'is_public' => false]);

        $this->actingAs($user)->get("/packs/{$pack->slug}")->assertOk();
    }

    // --- Public soundscape detail ---

    public function test_guest_can_view_public_soundscape(): void
    {
        $soundscape = Soundscape::factory()->public()->create();

        $this->get("/s/{$soundscape->slug}")->assertOk();
    }

    public function test_guest_cannot_view_private_soundscape(): void
    {
        $soundscape = Soundscape::factory()->create(['is_public' => false]);

        $this->get("/s/{$soundscape->slug}")->assertStatus(403);
    }

    // --- Public user profile ---

    public function test_guest_can_view_user_profile(): void
    {
        $user = User::factory()->create(['username' => 'runner42']);
        StemPack::factory()->public()->create(['user_id' => $user->id]);

        $this->get('/u/runner42')->assertOk();
    }

    public function test_nonexistent_user_profile_returns_404(): void
    {
        $this->get('/u/nobody_here')->assertStatus(404);
    }

    // --- Auth-required pages ---

    public function test_dashboard_requires_auth(): void
    {
        $this->get('/dashboard')->assertRedirect('/login');
    }

    public function test_dashboard_loads_for_authenticated_user(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)->get('/dashboard')->assertOk();
    }

    public function test_dashboard_includes_user_data(): void
    {
        $user = User::factory()->create();
        StemPack::factory()->create(['user_id' => $user->id, 'name' => 'My Pack']);
        Soundscape::factory()->create(['user_id' => $user->id, 'name' => 'My Scape']);

        $response = $this->actingAs($user)->get('/dashboard');

        $response->assertOk();
        $response->assertInertia(fn ($page) =>
            $page->component('Dashboard')
                ->has('packs', 1)
                ->has('soundscapes', 1)
        );
    }

    public function test_dashboard_does_not_include_other_users_private_data(): void
    {
        $user = User::factory()->create();
        $other = User::factory()->create();
        StemPack::factory()->create(['user_id' => $other->id, 'is_public' => false]);

        $response = $this->actingAs($user)->get('/dashboard');

        $response->assertInertia(fn ($page) =>
            $page->component('Dashboard')
                ->has('packs', 0)
        );
    }

    public function test_pack_create_requires_auth(): void
    {
        $this->get('/packs/create')->assertRedirect('/login');
    }

    public function test_soundscape_create_requires_auth(): void
    {
        $this->get('/soundscapes/create')->assertRedirect('/login');
    }

    // --- Explore with server props ---

    public function test_explore_includes_public_soundscapes_and_packs(): void
    {
        StemPack::factory()->public()->create(['name' => 'Public Pack']);
        StemPack::factory()->create(['name' => 'Private Pack']);
        Soundscape::factory()->public()->create(['name' => 'Public Scape']);
        Soundscape::factory()->create(['name' => 'Private Scape']);

        $response = $this->get('/explore');

        $response->assertInertia(fn ($page) =>
            $page->component('Explore')
                ->has('soundscapes.data', 1)
                ->has('packs.data', 1)
        );
    }

    // --- Flash messages ---

    public function test_successful_login_sets_flash_message(): void
    {
        $user = User::factory()->create(['password' => bcrypt('password123')]);

        $this->post('/login', [
            'email' => $user->email,
            'password' => 'password123',
        ])->assertRedirect('/dashboard')
          ->assertSessionHas('success');
    }
}
