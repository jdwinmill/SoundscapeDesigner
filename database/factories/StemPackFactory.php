<?php

namespace Database\Factories;

use App\Models\StemPack;
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;

/**
 * @extends Factory<StemPack>
 */
class StemPackFactory extends Factory
{
    public function definition(): array
    {
        $name = fake()->words(3, true);

        return [
            'user_id' => User::factory(),
            'name' => $name,
            'slug' => Str::slug($name) . '-' . Str::random(6),
            'genre' => fake()->randomElement(['electronic', 'ambient', 'hip-hop', 'rock', 'lo-fi']),
            'mood_summary' => fake()->sentence(),
            'key_center' => fake()->randomElement(['Cm', 'Am', 'F#m', 'Dm', 'Em']),
            'bpm_center' => fake()->randomFloat(1, 80, 200),
            'energy_range' => [fake()->randomFloat(2, 0, 0.4), fake()->randomFloat(2, 0.6, 1.0)],
            'best_for_phases' => fake()->randomElements(['warmup', 'easy_run', 'tempo', 'interval_peak', 'cooldown', 'sprint'], 2),
            'is_public' => false,
        ];
    }

    public function public(): static
    {
        return $this->state(['is_public' => true]);
    }
}
