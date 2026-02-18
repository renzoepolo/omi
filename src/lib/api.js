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
  if (!API_URL) {
    const key = `points:${projectId}`;
    const raw = localStorage.getItem(key);
    if (raw) return JSON.parse(raw);
    return [];
  }

  const response = await fetch(`${API_URL}/projects/${projectId}/observations`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Project-Id': String(projectId),
    },
  });
  if (!response.ok) throw new Error('No se pudieron cargar observaciones');

  const observations = await response.json();
  return observations.map((item) => ({
    id: item.id,
    name: item.extras?.name || 'Sin nombre',
    description: item.extras?.description || '',
    status: item.status || 'cargado',
    coordinates: item.extras?.coordinates || [-77.0428, -12.0464],
    property_type: item.property_type || 'urbano_baldio',
    price: item.price ?? '',
    currency: item.currency ?? '',
    valuation_date: item.valuation_date ?? '',
    surface_total: item.surface_total ?? '',
    surface_unit: item.surface_unit ?? 'm2',
    value_origin_code: item.value_origin_code ?? '',
    location: item.location ?? {},
    building: item.building ?? {},
    rural: item.rural ?? {},
    persisted: true,
  }));
}

export async function savePoints(token, projectId, points) {
  if (!API_URL) {
    localStorage.setItem(`points:${projectId}`, JSON.stringify(points));
    return points;
  }

  function toNumberOrNull(value) {
    if (value === '' || value === null || value === undefined) return null;
    const parsed = Number(value);
    return Number.isNaN(parsed) ? null : parsed;
  }

  function toPayload(point) {
    const payload = {
      project_id: Number(projectId),
      property_type: point.property_type || 'urbano_baldio',
      status: point.status || 'cargado',
      price: toNumberOrNull(point.price),
      currency: point.currency || null,
      valuation_date: point.valuation_date || null,
      surface_total: toNumberOrNull(point.surface_total),
      surface_unit: point.surface_unit || 'm2',
      value_origin_code: point.value_origin_code || null,
      extras: {
        ...(point.extras || {}),
        name: point.name || '',
        description: point.description || '',
        coordinates: point.coordinates,
      },
      location: point.location || null,
      building: point.property_type === 'rural' ? null : point.building || null,
      rural: point.property_type === 'rural' ? point.rural || null : null,
    };

    if (!payload.price) payload.currency = null;
    return payload;
  }

  for (const point of points) {
    const payload = toPayload(point);
    const method = point.persisted ? 'PATCH' : 'POST';
    const target = point.persisted
      ? `${API_URL}/projects/${projectId}/observations/${point.id}`
      : `${API_URL}/projects/${projectId}/observations`;

    const response = await fetch(target, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        'X-Project-Id': String(projectId),
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const message = await response.text();
      throw new Error(`No se pudieron guardar observaciones: ${message}`);
    }
  }

  return getPoints(token, projectId);
}
