<?php

namespace Database\Factories;

use App\Models\Soundscape;
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;

/**
 * @extends Factory<Soundscape>
 */
class SoundscapeFactory extends Factory
{
    public function definition(): array
    {
        $name = fake()->words(3, true);

        return [
            'user_id' => User::factory(),
            'name' => $name,
            'slug' => Str::slug($name) . '-' . Str::random(6),
            'description' => fake()->sentence(),
            'base_bpm' => fake()->randomFloat(1, 100, 180),
            'is_public' => false,
        ];
    }

    public function public(): static
    {
        return $this->state(['is_public' => true]);
    }
}
