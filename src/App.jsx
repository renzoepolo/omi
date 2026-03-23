import { useCallback, useEffect, useMemo, useState } from 'react';
import AdminPage from './components/AdminPage';
import AppHeader from './components/AppHeader';
import FAB from './components/FAB';
import LoginForm from './components/LoginForm';
import MapView from './components/MapView';
import RightPanel from './components/RightPanel';
import { getPoints, getProjects, loginRequest, savePoints } from './lib/api';

function buildPoint(coords) {
  return {
    id: crypto.randomUUID(),
    status: 'cargado',
    coordinates: coords,
    property_type: 'urbano_baldio',
    price: '',
    currency: '',
    valuation_date: '',
    surface_total: '',
    surface_unit: 'm2',
    value_origin_code: '',
    ovi_urbano_baldio: {
      TIPO_INMUEBLE: 0,
      ORIGEN_VALOR: '',
      SUPERFICIE: '',
      UNI_SUP: 0,
      MONEDA: '',
      VALOR_TOTAL: '',
      NOMENCLATURA: '',
      AFECTACION: '',
      FRENTE: '',
      FORMA: '',
      UBIC_CUADRA: '',
      TIPO_BARRIO: '',
      SIT_JURIDICA: '',
      FECHA_VALOR: '',
      PROCEDENCIA: '',
      TELEFONO: '',
      FOTO_FACHADA: '',
      FOTO_CARTEL: '',
      LINK: '',
    },
    location: {},
    building: {},
    rural: {},
    persisted: false,
  };
}

export default function App() {
  const [route, setRoute] = useState(() =>
    window.location.pathname.startsWith('/admin') ? '/admin' : '/',
  );
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState(null);
  const [points, setPoints] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [saving, setSaving] = useState(false);

  const [editEnabled, setEditEnabled] = useState(false);
  const [tool, setTool] = useState('query');
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelMode, setPanelMode] = useState('query');
  const [draftPoint, setDraftPoint] = useState(null);

  const selectedProject = useMemo(
    () => projects.find((project) => String(project.id) === String(projectId)) || projects[0],
    [projects, projectId],
  );

  const selectedPoint = useMemo(
    () => points.find((point) => String(point.id) === String(selectedId)),
    [points, selectedId],
  );

  const canAccessAdmin = useMemo(
    () =>
      projects.some((project) =>
        ['SuperAdmin', 'ProjectAdmin'].includes(project.role),
      ),
    [projects],
  );

  useEffect(() => {
    function syncRoute() {
      setRoute(window.location.pathname.startsWith('/admin') ? '/admin' : '/');
    }
    window.addEventListener('popstate', syncRoute);
    return () => window.removeEventListener('popstate', syncRoute);
  }, []);

  function navigate(nextRoute) {
    if (nextRoute === route) return;
    const target = nextRoute === '/admin' ? '/admin' : '/';
    window.history.pushState({}, '', target);
    setRoute(target);
  }

  const refreshProjects = useCallback(async () => {
    if (!token) return;
    const projectList = await getProjects(token);
    setProjects(projectList);
    if (projectList.length === 0) {
      setProjectId(null);
      return;
    }
    setProjectId((prev) => {
      const exists = projectList.some((project) => String(project.id) === String(prev));
      return exists ? prev : projectList[0].id;
    });
  }, [token]);

  useEffect(() => {
    refreshProjects();
  }, [refreshProjects]);

  useEffect(() => {
    if (!token || !projectId) return;
    getPoints(token, projectId).then((items) => {
      setPoints(items);
      setSelectedId(items[0]?.id ?? null);
      setDraftPoint(null);
      setPanelOpen(false);
      setPanelMode('query');
    });
  }, [token, projectId]);

  useEffect(() => {
    if (!selectedProject) return;
    localStorage.setItem(
      'omi:lastMapView',
      JSON.stringify({ center: selectedProject.center, zoom: selectedProject.zoom }),
    );
  }, [selectedProject]);

  async function handleLogin(email, password) {
    const payload = await loginRequest(email, password);
    setToken(payload.token);
    localStorage.setItem('token', payload.token);
  }

  function handleLogout() {
    localStorage.removeItem('token');
    setToken(null);
    setProjects([]);
    setProjectId(null);
    setPoints([]);
    setSelectedId(null);
    setPanelOpen(false);
    setDraftPoint(null);
    setTool('query');
    setEditEnabled(false);
    navigate('/');
  }

  function handleSelectTool(nextTool) {
    setTool(nextTool);
    if (nextTool === 'query') {
      setDraftPoint(null);
      setPanelMode('query');
    }
  }

  function handleToggleEditEnabled(enabled) {
    setEditEnabled(enabled);
    if (!enabled) {
      setTool('query');
      setDraftPoint(null);
      setPanelMode('query');
    }
  }

  function updatePoint(updated) {
    setPoints((current) =>
      current.map((point) => (String(point.id) === String(updated.id) ? updated : point)),
    );
  }

  async function persist(pointsToPersist = points) {
    if (!projectId) return [];
    console.info('[persist] start', { projectId, totalPoints: pointsToPersist.length });
    setSaving(true);
    try {
      const updated = await savePoints(token, projectId, pointsToPersist);
      setPoints(updated);
      console.info('[persist] done', { projectId, persistedCount: updated.length });
      return updated;
    } finally {
      setSaving(false);
    }
  }

  async function saveDraft() {
    if (!draftPoint) return;
    let nextPoints = points;
    if (panelMode === 'create') {
      nextPoints = [...points, { ...draftPoint, persisted: false }];
    } else if (panelMode === 'edit') {
      nextPoints = points.map((point) =>
        String(point.id) === String(draftPoint.id) ? { ...draftPoint, persisted: true } : point,
      );
    }

    try {
      const updated = await persist(nextPoints);
      if (panelMode === 'create') {
        setSelectedId(updated[0]?.id ?? null);
      } else {
        const stillExists = updated.some((point) => String(point.id) === String(draftPoint.id));
        setSelectedId(stillExists ? draftPoint.id : updated[0]?.id ?? null);
      }
      setDraftPoint(null);
      setPanelMode('query');
      setTool('query');
      setPanelOpen(true);
    } catch (error) {
      console.error('Error al guardar observacion', error);
    }
  }

  function cancelDraft() {
    setDraftPoint(null);
    setPanelMode('query');
    setTool('query');
    setPanelOpen(Boolean(selectedPoint));
  }

  if (!token) {
    return <LoginForm onLogin={handleLogin} />;
  }

  if (!selectedProject) {
    return <main className="loading">Cargando proyectos...</main>;
  }

  if (route === '/admin') {
    if (!canAccessAdmin) {
      return (
        <main className="loading">
          <div>
            <p>Esta cuenta no tiene permisos de administración.</p>
            <button type="button" onClick={() => navigate('/')}>
              Volver al visor
            </button>
          </div>
        </main>
      );
    }

    return (
      <AdminPage
        token={token}
        memberships={projects}
        selectedProjectId={selectedProject.id}
        onDataChanged={refreshProjects}
        onBack={async () => {
          await refreshProjects();
          navigate('/');
        }}
      />
    );
  }

  return (
    <main className="app-shell">
      <AppHeader
        projects={projects}
        selectedProjectId={selectedProject.id}
        onProjectChange={setProjectId}
        canAccessAdmin={canAccessAdmin}
        onGoAdmin={() => navigate('/admin')}
        onLogout={handleLogout}
      />

      <div className="viewer-area">
        <MapView
          project={selectedProject}
          points={points}
          selectedId={selectedId}
          draftPoint={draftPoint}
          mode={tool}
          panelOpen={panelOpen}
          onMapQuery={() => {
            setSelectedId(null);
            setDraftPoint(null);
            setPanelMode('query');
            setPanelOpen(false);
          }}
          onPointQuery={(id) => {
            setSelectedId(id);
            setPanelMode('query');
            setPanelOpen(true);
          }}
          onCreatePointFromMap={(coords) => {
            if (tool !== 'create') return;
            setDraftPoint(buildPoint(coords));
            setPanelMode('create');
            setPanelOpen(true);
          }}
          onPickPointToEdit={(id) => {
            if (tool !== 'edit') return;
            const point = points.find((item) => String(item.id) === String(id));
            if (!point) return;
            setSelectedId(id);
            setDraftPoint({ ...point });
            setPanelMode('edit');
            setPanelOpen(true);
          }}
          onMovePoint={(id, coords) => {
            if (tool !== 'edit') return;
            if (draftPoint && String(draftPoint.id) === String(id)) {
              setDraftPoint((current) => ({ ...current, coordinates: coords }));
              return;
            }
            updatePoint({
              ...(points.find((item) => String(item.id) === String(id)) || buildPoint(coords)),
              id,
              coordinates: coords,
            });
          }}
          onViewChange={(center, zoom) => {
            localStorage.setItem('omi:lastMapView', JSON.stringify({ center, zoom }));
          }}
        />

        <RightPanel
          open={panelOpen}
          mode={panelMode}
          point={panelMode === 'query' ? selectedPoint : draftPoint}
          onClose={() => setPanelOpen(false)}
          onDraftChange={setDraftPoint}
          onSaveDraft={saveDraft}
          onCancelDraft={cancelDraft}
          saving={saving}
        />

        <FAB
          panelOpen={panelOpen}
          editEnabled={editEnabled}
          onToggleEditEnabled={handleToggleEditEnabled}
          activeTool={tool}
          onSelectTool={handleSelectTool}
        />
      </div>
    </main>
  );
}
