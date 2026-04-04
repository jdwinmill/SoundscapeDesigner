<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Casts\Attribute;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\MorphMany;
use Illuminate\Database\Eloquent\Relations\MorphToMany;
use Illuminate\Support\Str;

#[Fillable([
    'name',
    'slug',
    'description',
    'base_bpm',
    'is_public',
])]
class Soundscape extends Model
{
    use HasFactory;

    protected $appends = ['config'];

    public function getRouteKeyName(): string
    {
        return 'slug';
    }

    protected static function booted(): void
    {
        static::creating(function (Soundscape $soundscape) {
            if (empty($soundscape->slug)) {
                $soundscape->slug = Str::slug($soundscape->name) . '-' . Str::random(6);
            }
        });
    }

    protected function casts(): array
    {
        return [
            'base_bpm' => 'float',
            'is_public' => 'boolean',
        ];
    }

    protected function config(): Attribute
    {
        return Attribute::get(function () {
            $this->loadMissing('stems');

            return [
                'baseBPM' => $this->base_bpm,
                'stems' => $this->stems->map(fn ($stem) => [
                    'stemId' => $stem->id,
                    'file' => basename($stem->file_path),
                    'bpmRange' => json_decode($stem->pivot->bpm_range, true),
                    'fadeIn' => (float) $stem->pivot->fade_in,
                    'fadeOut' => (float) $stem->pivot->fade_out,
                    'volume' => (float) $stem->pivot->volume,
                    'speed' => (float) $stem->pivot->speed,
                    'speedCurve' => $stem->pivot->speed_curve
                        ? json_decode($stem->pivot->speed_curve, true)
                        : null,
                ])->values()->all(),
            ];
        });
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function stems(): BelongsToMany
    {
        return $this->belongsToMany(Stem::class, 'soundscape_stem')
            ->withPivot(['bpm_range', 'fade_in', 'fade_out', 'volume', 'speed', 'speed_curve', 'sort_order'])
            ->withTimestamps()
            ->orderByPivot('sort_order');
    }

    public function tags(): MorphToMany
    {
        return $this->morphToMany(Tag::class, 'taggable');
    }

    public function favorites(): MorphMany
    {
        return $this->morphMany(Favorite::class, 'favorable');
    }

    public function clone(User $user): static
    {
        $copy = $this->replicate(['id', 'slug', 'created_at', 'updated_at']);
        $copy->user_id = $user->id;
        $copy->name = $this->name . ' (copy)';
        $copy->is_public = false;
        $copy->save();

        foreach ($this->stems as $stem) {
            $copy->stems()->attach($stem->id, [
                'bpm_range' => $stem->pivot->bpm_range,
                'fade_in' => $stem->pivot->fade_in,
                'fade_out' => $stem->pivot->fade_out,
                'volume' => $stem->pivot->volume,
                'speed' => $stem->pivot->speed,
                'speed_curve' => $stem->pivot->speed_curve,
                'sort_order' => $stem->pivot->sort_order,
            ]);
        }

        $copy->tags()->sync($this->tags->pluck('id'));

        return $copy->load('stems', 'tags');
    }
}
