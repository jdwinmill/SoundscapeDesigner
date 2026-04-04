<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('soundscape_stem', function (Blueprint $table) {
            $table->id();
            $table->foreignId('soundscape_id')->constrained()->cascadeOnDelete();
            $table->foreignId('stem_id')->constrained()->cascadeOnDelete();
            $table->json('bpm_range');
            $table->float('fade_in')->default(5.0);
            $table->float('fade_out')->default(5.0);
            $table->float('volume')->default(1.0);
            $table->float('speed')->default(1.0);
            $table->json('speed_curve')->nullable();
            $table->integer('sort_order')->default(0);
            $table->timestamps();

            $table->unique(['soundscape_id', 'stem_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('soundscape_stem');
    }
};
