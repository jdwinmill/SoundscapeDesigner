<?php

namespace Tests\Feature;

use App\Models\Stem;
use App\Models\StemPack;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

/**
 * Tests that the payload format from the frontend's buildSavePayload()
 * passes the API validation on SoundscapeController@store.
 */
class SoundscapeSavePayloadTest extends TestCase
{
    use RefreshDatabase;

    public function test_designer_save_payload_passes_validation(): void
    {
        $user = User::factory()->create();
        $pack = StemPack::factory()->create(['user_id' => $user->id]);
        $stem1 = Stem::factory()->create(['stem_pack_id' => $pack->id]);
        $stem2 = Stem::factory()->create(['stem_pack_id' => $pack->id]);

        // This matches exactly what buildSavePayload() outputs
        $payload = [
            'name' => 'Morning Run',
            'description' => 'A chill mix for morning runs',
            'base_bpm' => 160,
            'is_public' => false,
            'tags' => ['running', 'morning'],
            'stems' => [
                [
                    'stem_id' => $stem1->id,
                    'bpm_range' => [120, 170],
                    'fade_in' => 10,
                    'fade_out' => 10,
                    'volume' => 0.8,
                    'speed' => 1.0,
                    'speed_curve' => null,
                    'sort_order' => 0,
                ],
                [
                    'stem_id' => $stem2->id,
                    'bpm_range' => [100, 200],
                    'fade_in' => 15,
                    'fade_out' => 15,
                    'volume' => 0.5,
                    'speed' => 1.2,
                    'speed_curve' => [[100, 0.9], [200, 1.1]],
                    'sort_order' => 1,
                ],
            ],
        ];

        $response = $this->actingAs($user, 'sanctum')
            ->postJson('/api/soundscapes', $payload);

        $response->assertStatus(201);
        $this->assertDatabaseHas('soundscapes', [
            'name' => 'Morning Run',
            'user_id' => $user->id,
            'base_bpm' => 160,
        ]);
        $this->assertDatabaseCount('soundscape_stem', 2);
    }

    public function test_payload_without_description_passes(): void
    {
        $user = User::factory()->create();
        $stem = Stem::factory()->create();

        $payload = [
            'name' => 'Quick Mix',
            'description' => null,
            'base_bpm' => 150,
            'is_public' => true,
            'tags' => [],
            'stems' => [
                [
                    'stem_id' => $stem->id,
                    'bpm_range' => [120, 170],
                    'fade_in' => 5,
                    'fade_out' => 5,
                    'volume' => 1.0,
                    'speed' => 1.0,
                    'speed_curve' => null,
                    'sort_order' => 0,
                ],
            ],
        ];

        $this->actingAs($user, 'sanctum')
            ->postJson('/api/soundscapes', $payload)
            ->assertStatus(201);
    }

    public function test_payload_with_speed_curve_saves_correctly(): void
    {
        $user = User::factory()->create();
        $stem = Stem::factory()->create();

        $speedCurve = [[100, 0.8], [150, 1.0], [200, 1.3]];

        $payload = [
            'name' => 'Speed Test',
            'base_bpm' => 150,
            'stems' => [
                [
                    'stem_id' => $stem->id,
                    'bpm_range' => [100, 200],
                    'fade_in' => 10,
                    'fade_out' => 10,
                    'volume' => 0.7,
                    'speed' => 1.0,
                    'speed_curve' => $speedCurve,
                    'sort_order' => 0,
                ],
            ],
        ];

        $response = $this->actingAs($user, 'sanctum')
            ->postJson('/api/soundscapes', $payload);

        $response->assertStatus(201);

        // Verify the config accessor returns the speed curve
        $slug = $response->json('slug');
        $showResponse = $this->actingAs($user, 'sanctum')
            ->getJson("/api/soundscapes/{$slug}");

        $stems = $showResponse->json('config.stems');
        $this->assertEquals($speedCurve, $stems[0]['speedCurve']);
    }
}
