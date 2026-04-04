<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('stem_packs', function (Blueprint $table) {
            $table->string('slug')->unique()->after('name');
        });

        Schema::table('soundscapes', function (Blueprint $table) {
            $table->string('slug')->unique()->after('name');
        });
    }

    public function down(): void
    {
        Schema::table('stem_packs', function (Blueprint $table) {
            $table->dropColumn('slug');
        });

        Schema::table('soundscapes', function (Blueprint $table) {
            $table->dropColumn('slug');
        });
    }
};
