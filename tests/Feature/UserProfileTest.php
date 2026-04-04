<?php

namespace Tests\Feature;

use App\Models\Soundscape;
use App\Models\StemPack;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class UserProfileTest extends TestCase
{
    use RefreshDatabase;

    public function test_public_profile_shows_public_content(): void
    {
        $user = User::factory()->create(['username' => 'runner42']);

        StemPack::factory()->public()->create(['user_id' => $user->id, 'name' => 'Public Pack']);
        StemPack::factory()->create(['user_id' => $user->id, 'name' => 'Private Pack']);

        Soundscape::factory()->public()->create(['user_id' => $user->id, 'name' => 'Public Scape']);
        Soundscape::factory()->create(['user_id' => $user->id, 'name' => 'Private Scape']);

        $response = $this->getJson('/api/users/runner42');

        $response->assertOk();
        $this->assertEquals('runner42', $response->json('user.username'));

        $packNames = collect($response->json('stem_packs'))->pluck('name');
        $this->assertContains('Public Pack', $packNames);
        $this->assertNotContains('Private Pack', $packNames);

        $scapeNames = collect($response->json('soundscapes'))->pluck('name');
        $this->assertContains('Public Scape', $scapeNames);
        $this->assertNotContains('Private Scape', $scapeNames);
    }

    public function test_profile_does_not_expose_email(): void
    {
        $user = User::factory()->create(['username' => 'secureguy']);

        $response = $this->getJson('/api/users/secureguy');

        $response->assertOk();
        $this->assertArrayNotHasKey('email', $response->json('user'));
        $this->assertArrayNotHasKey('id', $response->json('user'));
    }

    public function test_nonexistent_user_returns_404(): void
    {
        $this->getJson('/api/users/nobody_here')
            ->assertStatus(404);
    }

    public function test_profile_includes_join_date(): void
    {
        $user = User::factory()->create(['username' => 'newbie']);

        $response = $this->getJson('/api/users/newbie');

        $response->assertOk();
        $this->assertArrayHasKey('joined', $response->json('user'));
    }
}
