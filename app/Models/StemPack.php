<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\MorphMany;
use Illuminate\Database\Eloquent\Relations\MorphToMany;
use Illuminate\Support\Str;

#[Fillable([
    'name',
    'slug',
    'genre',
    'mood_summary',
    'key_center',
    'bpm_center',
    'energy_range',
    'best_for_phases',
    'cross_pack_compatible_with',
    'is_public',
])]
class StemPack extends Model
{
    use HasFactory;

    public function getRouteKeyName(): string
    {
        return 'slug';
    }

    protected static function booted(): void
    {
        static::creating(function (StemPack $pack) {
            if (empty($pack->slug)) {
                $pack->slug = Str::slug($pack->name) . '-' . Str::random(6);
            }
        });

        static::deleting(function (StemPack $pack) {
            $pack->stems->each->delete();
        });
    }

    protected function casts(): array
    {
        return [
            'bpm_center' => 'float',
            'energy_range' => 'array',
            'best_for_phases' => 'array',
            'cross_pack_compatible_with' => 'array',
            'is_public' => 'boolean',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function stems(): HasMany
    {
        return $this->hasMany(Stem::class);
    }

    public function tags(): MorphToMany
    {
        return $this->morphToMany(Tag::class, 'taggable');
    }

    public function favorites(): MorphMany
    {
        return $this->morphMany(Favorite::class, 'favorable');
    }
}
