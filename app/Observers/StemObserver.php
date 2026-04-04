<?php

namespace App\Observers;

use App\Models\Stem;
use Illuminate\Support\Facades\Storage;

class StemObserver
{
    public function deleting(Stem $stem): void
    {
        if ($stem->file_path) {
            Storage::disk('public')->delete($stem->file_path);
        }
    }
}
