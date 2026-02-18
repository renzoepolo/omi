const API_URL = import.meta.env.VITE_API_URL || '';

const DEMO_USER = { username: 'admin', password: 'admin123', token: 'demo-jwt-token' };

export async function loginRequest(username, password) {
  if (!API_URL) {
    if (username === DEMO_USER.username && password === DEMO_USER.password) {
      return { token: DEMO_USER.token, name: 'Administrador Demo' };
    }
    throw new Error('Credenciales inválidas');
  }

  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error('No se pudo iniciar sesión');
  }

  return response.json();
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
  if (!API_URL) {
    const key = `points:${projectId}`;
    const raw = localStorage.getItem(key);
    if (raw) return JSON.parse(raw);
    return [];
  }

  const response = await fetch(`${API_URL}/projects/${projectId}/points`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('No se pudieron cargar puntos');
  return response.json();
}

export async function savePoints(token, projectId, points) {
  if (!API_URL) {
    localStorage.setItem(`points:${projectId}`, JSON.stringify(points));
    return { ok: true };
  }

  const response = await fetch(`${API_URL}/projects/${projectId}/points`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(points),
  });

  if (!response.ok) throw new Error('No se pudieron guardar cambios');
  return response.json();
}
