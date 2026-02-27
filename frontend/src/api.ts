/**
 * API client for communicating with the PhysicsLens backend.
 */

const API_BASE = 'http://localhost:8000';

export interface ParsedData {
  objects: Array<{
    id: string;
    type: string;
    mass: number | null;
  }>;
  surfaces: Array<{
    id: string;
    type: string;
    angle: number | null;
    friction_coefficient: number | null;
  }>;
  placements: Array<{
    object_id: string;
    surface_id: string;
  }>;
  forces: Array<{
    type: string;
    magnitude: number | null;
    direction: string;
    object_id: string;
  }>;
  friction: {
    object_id: string;
    coefficient: number | null;
  } | null;
  constants: {
    gravity: number;
  };
}

export interface ParseResponse {
  status: 'success' | 'error';
  data: ParsedData;
}

/**
 * Parse a text physics problem via the API.
 */
export async function parseTextProblem(problem: string): Promise<ParseResponse> {
  const res = await fetch(`${API_BASE}/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problem }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail?.message || `Server error: ${res.status}`);
  }

  return res.json();
}

/**
 * Parse a physics problem from an uploaded image via the API.
 */
export async function parseImageProblem(file: File): Promise<ParseResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/parse-image`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail?.message || `Server error: ${res.status}`);
  }

  return res.json();
}

/**
 * Generate an SVG diagram from parsed physics data.
 */
export async function generateDiagram(data: ParsedData): Promise<string> {
  const res = await fetch(`${API_BASE}/diagram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data }),
  });

  if (!res.ok) {
    throw new Error(`Diagram generation failed: ${res.status}`);
  }

  return res.text();
}
