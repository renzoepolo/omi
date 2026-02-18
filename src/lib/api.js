const API_URL = import.meta.env.VITE_API_URL || '';

const DEMO_USER = { email: 'admin@omi.local', password: 'admin123', token: 'demo-jwt-token' };

export async function loginRequest(email, password) {
  if (!API_URL) {
    if (email === DEMO_USER.email && password === DEMO_USER.password) {
      return { token: DEMO_USER.token, name: 'Administrador Demo' };
    }
    throw new Error('Credenciales inválidas');
  }

  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error('No se pudo iniciar sesión');
  }

  const payload = await response.json();
  return { token: payload.access_token, tokenType: payload.token_type };
}

export async function getProjects(token) {
  if (!API_URL) {
    return [
      { id: 'p1', name: 'Proyecto Norte', center: [-74.1, 4.65], zoom: 12 },
      { id: 'p2', name: 'Proyecto Sur', center: [-74.18, 4.58], zoom: 12 },
    ];
  }

  const response = await fetch(`${API_URL}/projects`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) throw new Error('No se pudieron cargar proyectos');
  return response.json();
}

export async function getPoints(token, projectId) {
  const key = `points:${projectId}`;
  const raw = localStorage.getItem(key);
  if (raw) return JSON.parse(raw);
  return [];
}

export async function savePoints(token, projectId, points) {
  localStorage.setItem(`points:${projectId}`, JSON.stringify(points));
  return { ok: true };
}
