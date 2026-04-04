<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('stem_packs', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('name');
            $table->string('genre')->nullable();
            $table->string('mood_summary')->nullable();
            $table->string('key_center')->nullable();
            $table->float('bpm_center')->default(150.0);
            $table->json('energy_range')->nullable();
            $table->json('best_for_phases')->nullable();
            $table->json('cross_pack_compatible_with')->nullable();
            $table->boolean('is_public')->default(false);
            $table->timestamps();

            $table->index(['user_id', 'is_public']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('stem_packs');
    }
};
