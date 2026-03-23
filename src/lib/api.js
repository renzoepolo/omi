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
    status: item.status || 'cargado',
    coordinates: item.extras?.coordinates || [-77.0428, -12.0464],
    property_type: item.property_type || 'urbano_baldio',
    price: item.price ?? '',
    currency: item.currency ?? '',
    valuation_date: item.valuation_date ?? '',
    surface_total: item.surface_total ?? '',
    surface_unit: item.surface_unit ?? 'm2',
    value_origin_code: item.value_origin_code ?? '',
    ovi_urbano_baldio: item.ovi_urbano_baldio ?? null,
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
    const ovi = point.ovi_urbano_baldio || null;
    const mappedCurrency =
      ovi && (ovi.MONEDA === 0 || ovi.MONEDA === '0' || ovi.MONEDA === 1 || ovi.MONEDA === '1')
        ? Number(ovi.MONEDA) === 0
          ? 'ARS'
          : 'USD'
        : null;

    const payload = {
      project_id: Number(projectId),
      property_type: point.property_type || 'urbano_baldio',
      status: point.status || 'cargado',
      price: ovi ? toNumberOrNull(ovi.VALOR_TOTAL) : toNumberOrNull(point.price),
      currency: mappedCurrency || point.currency || null,
      valuation_date: ovi ? ovi.FECHA_VALOR || null : point.valuation_date || null,
      surface_total: ovi ? toNumberOrNull(ovi.SUPERFICIE) : toNumberOrNull(point.surface_total),
      surface_unit: ovi ? 'm2' : point.surface_unit || 'm2',
      value_origin_code: point.value_origin_code || null,
      ovi_urbano_baldio: ovi
        ? {
            ...ovi,
            TIPO_INMUEBLE: Number(ovi.TIPO_INMUEBLE),
            ORIGEN_VALOR: Number(ovi.ORIGEN_VALOR),
            SUPERFICIE: Number(ovi.SUPERFICIE),
            UNI_SUP: Number(ovi.UNI_SUP),
            MONEDA: Number(ovi.MONEDA),
            VALOR_TOTAL: toNumberOrNull(ovi.VALOR_TOTAL),
            AFECTACION: Number(ovi.AFECTACION),
            FRENTE: Number(ovi.FRENTE),
            FORMA: Number(ovi.FORMA),
            UBIC_CUADRA: Number(ovi.UBIC_CUADRA),
            TIPO_BARRIO: Number(ovi.TIPO_BARRIO),
            SIT_JURIDICA: Number(ovi.SIT_JURIDICA),
            PROCEDENCIA: Number(ovi.PROCEDENCIA),
            TELEFONO: ovi.TELEFONO || null,
            FOTO_FACHADA: ovi.FOTO_FACHADA || null,
            FOTO_CARTEL: ovi.FOTO_CARTEL || null,
            LINK: ovi.LINK || null,
          }
        : null,
      extras: {
        ...(point.extras || {}),
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

    if (method === 'PATCH') {
      delete payload.project_id;
    }

    console.info('[savePoints] sending', { method, target, pointId: point.id, persisted: point.persisted });

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
      console.error('[savePoints] request failed', {
        method,
        target,
        pointId: point.id,
        status: response.status,
        message,
      });
      throw new Error(`No se pudieron guardar observaciones: ${message}`);
    }
    console.info('[savePoints] request ok', { method, target, pointId: point.id, status: response.status });
  }

  console.info('[savePoints] refreshing observations list');
  return getPoints(token, projectId);
}

async function readError(response) {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === 'string') return payload.detail;
    return JSON.stringify(payload);
  } catch {
    return response.statusText || 'Error inesperado';
  }
}

async function adminRequest(token, scopeProjectId, path, options = {}) {
  if (!API_URL) {
    throw new Error('El panel admin requiere backend configurado (VITE_API_URL)');
  }

  const headers = {
    Authorization: `Bearer ${token}`,
    'X-Project-Id': String(scopeProjectId),
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_URL}${path}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }
  if (response.status === 204) return null;
  return response.json();
}

export function adminListProjects(token, scopeProjectId) {
  return adminRequest(token, scopeProjectId, '/admin/projects');
}

export function adminCreateProject(token, scopeProjectId, payload) {
  return adminRequest(token, scopeProjectId, '/admin/projects', { method: 'POST', body: payload });
}

export function adminUpdateProject(token, scopeProjectId, projectId, payload) {
  return adminRequest(token, scopeProjectId, `/admin/projects/${projectId}`, {
    method: 'PUT',
    body: payload,
  });
}

export function adminListLayers(token, scopeProjectId) {
  return adminRequest(token, scopeProjectId, '/admin/layers');
}

export function adminCreateLayer(token, scopeProjectId, payload) {
  return adminRequest(token, scopeProjectId, '/admin/layers', { method: 'POST', body: payload });
}

export function adminUpdateLayer(token, scopeProjectId, layerId, payload) {
  return adminRequest(token, scopeProjectId, `/admin/layers/${layerId}`, {
    method: 'PUT',
    body: payload,
  });
}

export function adminDeleteLayer(token, scopeProjectId, layerId) {
  return adminRequest(token, scopeProjectId, `/admin/layers/${layerId}`, { method: 'DELETE' });
}

export function adminAttachLayerToProject(token, scopeProjectId, projectId, payload) {
  return adminRequest(token, scopeProjectId, `/admin/projects/${projectId}/layers`, {
    method: 'POST',
    body: payload,
  });
}

export function adminDetachLayerFromProject(token, scopeProjectId, projectId, layerId) {
  return adminRequest(token, scopeProjectId, `/admin/projects/${projectId}/layers/${layerId}`, {
    method: 'DELETE',
  });
}

export function adminReplaceFormFields(token, scopeProjectId, projectId, payload) {
  return adminRequest(token, scopeProjectId, `/admin/projects/${projectId}/form-fields`, {
    method: 'PUT',
    body: payload,
  });
}

export function adminListUsers(token, scopeProjectId) {
  return adminRequest(token, scopeProjectId, '/admin/users');
}

export function adminCreateUser(token, scopeProjectId, payload) {
  return adminRequest(token, scopeProjectId, '/admin/users', { method: 'POST', body: payload });
}

export function adminUpdateUser(token, scopeProjectId, userId, payload) {
  return adminRequest(token, scopeProjectId, `/admin/users/${userId}`, { method: 'PUT', body: payload });
}

export function adminAssignUserProject(token, scopeProjectId, userId, payload) {
  return adminRequest(token, scopeProjectId, `/admin/users/${userId}/projects`, {
    method: 'POST',
    body: payload,
  });
}

export function adminUnassignUserProject(token, scopeProjectId, userId, projectId) {
  return adminRequest(token, scopeProjectId, `/admin/users/${userId}/projects/${projectId}`, {
    method: 'DELETE',
  });
}

export function adminListGeoServerWorkspaces(token, scopeProjectId) {
  return adminRequest(token, scopeProjectId, '/admin/geoserver/workspaces');
}

export function adminListGeoServerWorkspaceLayers(token, scopeProjectId, workspace) {
  return adminRequest(token, scopeProjectId, `/admin/geoserver/workspaces/${encodeURIComponent(workspace)}/layers`);
}

export function adminListGeoServerWorkspaceStyles(token, scopeProjectId, workspace) {
  return adminRequest(token, scopeProjectId, `/admin/geoserver/workspaces/${encodeURIComponent(workspace)}/styles`);
}

export function adminListGeoServerLayerStyles(token, scopeProjectId, workspace, layerName) {
  return adminRequest(
    token,
    scopeProjectId,
    `/admin/geoserver/workspaces/${encodeURIComponent(workspace)}/layers/${encodeURIComponent(layerName)}/styles`,
  );
}
