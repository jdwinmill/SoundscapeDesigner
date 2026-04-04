<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('stems', function (Blueprint $table) {
            $table->id();
            $table->foreignId('stem_pack_id')->constrained()->cascadeOnDelete();
            $table->string('name');
            $table->string('file_path');
            $table->float('duration_s')->default(0.0);
            $table->boolean('loopable')->default(true);

            // Musical info
            $table->string('key')->default('none');
            $table->float('bpm')->default(150.0);
            $table->string('scale')->default('chromatic');
            $table->string('time_signature')->default('4/4');
            $table->float('key_confidence')->default(1.0);

            // Role
            $table->string('role_type')->default('textural');
            $table->string('role_layer')->default('mid');
            $table->string('role_function')->default('atmosphere');

            // Energy
            $table->float('intensity')->default(0.5);
            $table->float('drive')->default(0.5);
            $table->float('groove')->default(0.5);

            // Mood
            $table->json('mood_tags')->nullable();
            $table->float('valence')->default(0.5);
            $table->float('arousal')->default(0.5);

            // Sonic
            $table->float('brightness')->default(0.5);
            $table->float('density')->default(0.5);
            $table->float('space')->default(0.5);
            $table->float('warmth')->default(0.5);

            // Mix hints
            $table->json('pairs_well_with')->nullable();
            $table->json('conflicts_with')->nullable();
            $table->boolean('solo_capable')->default(false);
            $table->boolean('intro_suitable')->default(false);
            $table->boolean('climax_suitable')->default(false);

            // Transition hints
            $table->integer('fade_in_beats')->default(8);
            $table->integer('fade_out_beats')->default(4);
            $table->string('entry_point')->default('downbeat');
            $table->string('exit_style')->default('fade');

            // Listener context
            $table->json('best_for')->nullable();
            $table->json('avoid_for')->nullable();

            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('stems');
    }
};
