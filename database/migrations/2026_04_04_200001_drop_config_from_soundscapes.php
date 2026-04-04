<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('soundscapes', function (Blueprint $table) {
            $table->dropColumn('config');
        });
    }

    public function down(): void
    {
        Schema::table('soundscapes', function (Blueprint $table) {
            $table->json('config')->after('base_bpm');
        });
    }
};
