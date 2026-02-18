import { useEffect, useMemo, useState } from 'react';
import AppHeader from './components/AppHeader';
import FAB from './components/FAB';
import LoginForm from './components/LoginForm';
import MapView from './components/MapView';
import RightPanel from './components/RightPanel';
import { getPoints, getProjects, loginRequest, savePoints } from './lib/api';

function buildPoint(coords) {
  return {
    id: crypto.randomUUID(),
    name: 'Punto nuevo',
    description: '',
    status: 'nuevo',
    coordinates: coords,
  };
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState(null);
  const [points, setPoints] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [saving, setSaving] = useState(false);

  const [fabOpen, setFabOpen] = useState(false);
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

  useEffect(() => {
    if (!token) return;
    getProjects(token).then((projectList) => {
      setProjects(projectList);
      if (projectList.length > 0) {
        setProjectId((prev) => prev || projectList[0].id);
      }
    });
  }, [token]);

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

  async function persist() {
    if (!projectId) return;
    setSaving(true);
    try {
      await savePoints(token, projectId, points);
    } finally {
      setSaving(false);
    }
  }

  async function saveDraft() {
    if (!draftPoint) return;
    if (panelMode === 'create') {
      setPoints((current) => [...current, draftPoint]);
      setSelectedId(draftPoint.id);
    } else if (panelMode === 'edit') {
      updatePoint(draftPoint);
      setSelectedId(draftPoint.id);
    }
    setDraftPoint(null);
    setPanelMode('query');
    setTool('query');
    await persist();
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

  return (
    <main className="app-shell">
      <AppHeader
        projects={projects}
        selectedProjectId={selectedProject.id}
        onProjectChange={setProjectId}
        onLogout={handleLogout}
      />

      <div className="viewer-area">
        <MapView
          project={selectedProject}
          points={points}
          selectedId={selectedId}
          draftPoint={draftPoint}
          mode={tool}
          onMapQuery={() => {
            setPanelMode('query');
            setPanelOpen(true);
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
          open={fabOpen}
          onToggleOpen={() => setFabOpen((current) => !current)}
          editEnabled={editEnabled}
          onToggleEditEnabled={handleToggleEditEnabled}
          activeTool={tool}
          onSelectTool={handleSelectTool}
        />
      </div>
    </main>
  );
}
