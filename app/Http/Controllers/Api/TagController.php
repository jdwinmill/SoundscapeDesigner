<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Tag;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class TagController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $query = Tag::query();

        if ($type = $request->query('type')) {
            $query->where('type', $type);
        }

        return response()->json($query->orderBy('name')->get());
    }
}
