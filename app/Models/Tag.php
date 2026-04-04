<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\MorphToMany;

#[Fillable(['name', 'slug', 'type'])]
class Tag extends Model
{
    use HasFactory;
    public function stemPacks(): MorphToMany
    {
        return $this->morphedByMany(StemPack::class, 'taggable');
    }

    public function soundscapes(): MorphToMany
    {
        return $this->morphedByMany(Soundscape::class, 'taggable');
    }
}
