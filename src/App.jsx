import { useEffect, useMemo, useState } from 'react';
import LoginForm from './components/LoginForm';
import MapView from './components/MapView';
import ProjectSelector from './components/ProjectSelector';
import PointPanel from './components/PointPanel';
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

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === projectId) || projects[0],
    [projects, projectId],
  );

  useEffect(() => {
    if (!token) return;
    getProjects(token).then((projectList) => {
      setProjects(projectList);
      if (projectList.length > 0) setProjectId((prev) => prev || projectList[0].id);
    });
  }, [token]);

  useEffect(() => {
    if (!token || !projectId) return;
    getPoints(token, projectId).then((items) => {
      setPoints(items);
      setSelectedId(items[0]?.id ?? null);
    });
  }, [token, projectId]);

  async function handleLogin(email, password) {
    const payload = await loginRequest(email, password);
    setToken(payload.token);
    localStorage.setItem('token', payload.token);
  }

  function updatePoint(updated) {
    setPoints((current) => current.map((point) => (point.id === updated.id ? updated : point)));
  }

  function deletePoint(id) {
    setPoints((current) => current.filter((point) => point.id !== id));
    setSelectedId(null);
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

  if (!token) {
    return <LoginForm onLogin={handleLogin} />;
  }

  if (!selectedProject) {
    return <main className="loading">Cargando proyectos...</main>;
  }

  return (
    <main className="layout">
      <header className="topbar card">
        <ProjectSelector projects={projects} selectedId={selectedProject.id} onChange={setProjectId} />
        <button
          className="ghost"
          onClick={() => {
            localStorage.removeItem('token');
            setToken(null);
          }}
        >
          Cerrar sesión
        </button>
      </header>

      <MapView
        project={selectedProject}
        points={points}
        selectedId={selectedId}
        onSelectPoint={setSelectedId}
        onCreatePoint={(coords) => {
          const point = buildPoint(coords);
          setPoints((current) => [...current, point]);
          setSelectedId(point.id);
        }}
        onMovePoint={(id, coords) => {
          setPoints((current) =>
            current.map((point) => (point.id === id ? { ...point, coordinates: coords } : point)),
          );
          setSelectedId(id);
        }}
      />

      <PointPanel
        selectedPoint={points.find((point) => point.id === selectedId)}
        onUpdate={updatePoint}
        onDelete={deletePoint}
        onSave={persist}
        saving={saving}
      />
    </main>
  );
}
