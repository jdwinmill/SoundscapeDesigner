<?php

namespace App\Models;

use App\Observers\StemObserver;
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Attributes\ObservedBy;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;

#[ObservedBy(StemObserver::class)]
#[Fillable([
    'name',
    'file_path',
    'duration_s',
    'loopable',
    'key',
    'bpm',
    'scale',
    'time_signature',
    'key_confidence',
    'role_type',
    'role_layer',
    'role_function',
    'intensity',
    'drive',
    'groove',
    'mood_tags',
    'valence',
    'arousal',
    'brightness',
    'density',
    'space',
    'warmth',
    'pairs_well_with',
    'conflicts_with',
    'solo_capable',
    'intro_suitable',
    'climax_suitable',
    'fade_in_beats',
    'fade_out_beats',
    'entry_point',
    'exit_style',
    'best_for',
    'avoid_for',
])]
class Stem extends Model
{
    use HasFactory;

    protected function casts(): array
    {
        return [
            'duration_s' => 'float',
            'loopable' => 'boolean',
            'bpm' => 'float',
            'key_confidence' => 'float',
            'intensity' => 'float',
            'drive' => 'float',
            'groove' => 'float',
            'mood_tags' => 'array',
            'valence' => 'float',
            'arousal' => 'float',
            'brightness' => 'float',
            'density' => 'float',
            'space' => 'float',
            'warmth' => 'float',
            'pairs_well_with' => 'array',
            'conflicts_with' => 'array',
            'solo_capable' => 'boolean',
            'intro_suitable' => 'boolean',
            'climax_suitable' => 'boolean',
            'best_for' => 'array',
            'avoid_for' => 'array',
        ];
    }

    public function stemPack(): BelongsTo
    {
        return $this->belongsTo(StemPack::class);
    }

    public function soundscapes(): BelongsToMany
    {
        return $this->belongsToMany(Soundscape::class, 'soundscape_stem');
    }

    public function isInPublicSoundscape(): bool
    {
        return $this->soundscapes()->where('is_public', true)->exists();
    }
}
