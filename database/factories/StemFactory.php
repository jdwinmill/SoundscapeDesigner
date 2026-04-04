<?php

namespace Database\Factories;

use App\Models\Stem;
use App\Models\StemPack;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Stem>
 */
class StemFactory extends Factory
{
    public function definition(): array
    {
        return [
            'stem_pack_id' => StemPack::factory(),
            'name' => fake()->words(2, true),
            'file_path' => 'stems/' . fake()->numberBetween(1, 100) . '/' . fake()->uuid() . '.wav',
            'duration_s' => fake()->randomFloat(1, 5, 120),
            'loopable' => true,
            'key' => fake()->randomElement(['Cm', 'Am', 'none']),
            'bpm' => fake()->randomFloat(1, 80, 200),
            'scale' => 'chromatic',
            'time_signature' => '4/4',
            'key_confidence' => fake()->randomFloat(2, 0.5, 1.0),
            'role_type' => fake()->randomElement(['rhythmic', 'melodic', 'textural', 'harmonic', 'percussive']),
            'role_layer' => fake()->randomElement(['low', 'mid', 'high', 'full']),
            'role_function' => fake()->randomElement(['foundation', 'hook', 'fill', 'accent', 'atmosphere', 'drive']),
            'intensity' => fake()->randomFloat(2, 0, 1),
            'drive' => fake()->randomFloat(2, 0, 1),
            'groove' => fake()->randomFloat(2, 0, 1),
            'mood_tags' => ['energetic', 'upbeat'],
            'valence' => fake()->randomFloat(2, 0, 1),
            'arousal' => fake()->randomFloat(2, 0, 1),
            'brightness' => fake()->randomFloat(2, 0, 1),
            'density' => fake()->randomFloat(2, 0, 1),
            'space' => fake()->randomFloat(2, 0, 1),
            'warmth' => fake()->randomFloat(2, 0, 1),
            'solo_capable' => false,
            'intro_suitable' => false,
            'climax_suitable' => false,
            'fade_in_beats' => 8,
            'fade_out_beats' => 4,
            'entry_point' => 'downbeat',
            'exit_style' => 'fade',
            'best_for' => ['tempo', 'interval_peak'],
            'avoid_for' => ['cooldown'],
        ];
    }
}
