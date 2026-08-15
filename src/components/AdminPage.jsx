import { useEffect, useMemo, useState } from 'react';
import {
  adminAssignUserProject,
  adminAttachLayerToProject,
  adminCreateLayer,
  adminCreateProject,
  adminCreateUser,
  adminDetachLayerFromProject,
  adminListGeoServerLayerStyles,
  adminListGeoServerWorkspaceLayers,
  adminListGeoServerWorkspaceStyles,
  adminListGeoServerWorkspaces,
  adminListLayers,
  adminListProjects,
  adminListUsers,
  adminReplaceFormFields,
  adminUnassignUserProject,
  adminUpdateProject,
  adminUpdateUser,
} from '../lib/api';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Select } from './ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';

const PROPERTY_TYPES = ['urbano_baldio', 'urbano_edificado', 'rural'];
const PROJECT_ROLES = ['SuperAdmin', 'ProjectAdmin', 'Editor', 'Viewer'];

function emptyProjectForm() {
  return {
    id: null,
    name: '',
    description: '',
    centerLng: -77.0428,
    centerLat: -12.0464,
    zoom: 13,
  };
}

function emptyLayerForm() {
  return {
    id: null,
    name: '',
    geoserver_workspace: '',
    geoserver_layer_name: '',
    style_name: '',
    type: 'WMS',
    default_visible: true,
    z_index: 0,
  };
}

function emptyUserCreateForm() {
  return { email: '', password: '', is_active: true };
}

function parseMapViewFromStorage() {
  try {
    const raw = localStorage.getItem('omi:lastMapView');
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed.center) || parsed.center.length !== 2) return null;
    return {
      centerLng: Number(parsed.center[0]),
      centerLat: Number(parsed.center[1]),
      zoom: Number(parsed.zoom),
    };
  } catch {
    return null;
  }
}

function normalizeZoom(value) {
  const parsed = Number(value);
  if (Number.isNaN(parsed)) return 13;
  return Math.max(0, Math.round(parsed));
}

function moveItem(list, fromIndex, toIndex) {
  if (fromIndex < 0 || toIndex < 0 || fromIndex >= list.length || toIndex >= list.length) return list;
  const clone = [...list];
  const [moved] = clone.splice(fromIndex, 1);
  clone.splice(toIndex, 0, moved);
  return clone;
}

function parseFieldFromApi(field) {
  return {
    field_key: field.field_key,
    label: field.label,
    field_type: field.field_type,
    required: Boolean(field.required),
    visible_types: field.config?.visible_for_property_types || [...PROPERTY_TYPES],
    coded_pairs: (field.config?.coded_values || []).map((item) => ({
      value: item.value || '',
      label: item.label || '',
    })),
  };
}

export default function AdminPage({ token, memberships, selectedProjectId, onDataChanged, onBack }) {
  const [tab, setTab] = useState('projects');
  const [scopeProjectId, setScopeProjectId] = useState(String(selectedProjectId || memberships[0]?.id || ''));
  const [activeProjectId, setActiveProjectId] = useState(String(selectedProjectId || ''));

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const [projects, setProjects] = useState([]);
  const [layers, setLayers] = useState([]);
  const [users, setUsers] = useState([]);

  const [projectForm, setProjectForm] = useState(emptyProjectForm());

  const [layerForm, setLayerForm] = useState(emptyLayerForm());
  const [layerAssignments, setLayerAssignments] = useState({});
  const [layerOrder, setLayerOrder] = useState([]);
  const [draggingLayerId, setDraggingLayerId] = useState(null);

  const [gsWorkspaces, setGsWorkspaces] = useState([]);
  const [gsWorkspace, setGsWorkspace] = useState('');
  const [gsLayers, setGsLayers] = useState([]);
  const [gsStyles, setGsStyles] = useState([]);
  const [gsLayerStyles, setGsLayerStyles] = useState([]);

  const [formFields, setFormFields] = useState([]);
  const [draggingFieldIndex, setDraggingFieldIndex] = useState(null);

  const [createUserForm, setCreateUserForm] = useState(emptyUserCreateForm());
  const [assignForm, setAssignForm] = useState({ userId: '', projectId: '', role: 'Viewer' });

  const activeMembership = useMemo(
    () => memberships.find((membership) => String(membership.id) === String(scopeProjectId)) || memberships[0],
    [memberships, scopeProjectId],
  );

  const canCreateProject = activeMembership?.role === 'SuperAdmin';

  const activeProject = useMemo(
    () => projects.find((project) => String(project.id) === String(activeProjectId)),
    [projects, activeProjectId],
  );

  const attachedLayerIds = useMemo(
    () => layerOrder.filter((id) => layerAssignments[id]?.attached),
    [layerAssignments, layerOrder],
  );

  useEffect(() => {
    if (!scopeProjectId && memberships[0]?.id) {
      setScopeProjectId(String(memberships[0].id));
    }
  }, [scopeProjectId, memberships]);

  useEffect(() => {
    setActiveProjectId(String(selectedProjectId || ''));
  }, [selectedProjectId]);

  async function refreshAdminData() {
    const [projectData, layerData, userData] = await Promise.all([
      adminListProjects(token, scopeProjectId),
      adminListLayers(token, scopeProjectId),
      adminListUsers(token, scopeProjectId),
    ]);
    setProjects(projectData);
    setLayers(layerData);
    setUsers(userData);

    if (!activeProjectId && projectData[0]?.id) {
      setActiveProjectId(String(projectData[0].id));
    }
    if (!assignForm.projectId && projectData[0]?.id) {
      setAssignForm((current) => ({ ...current, projectId: String(projectData[0].id) }));
    }
    if (!assignForm.userId && userData[0]?.id) {
      setAssignForm((current) => ({ ...current, userId: String(userData[0].id) }));
    }
  }

  useEffect(() => {
    if (!scopeProjectId) return;

    async function loadAll() {
      setLoading(true);
      setError('');
      try {
        await refreshAdminData();
        const workspaces = await adminListGeoServerWorkspaces(token, scopeProjectId);
        setGsWorkspaces(workspaces);
        if (!gsWorkspace && workspaces[0]?.name) {
          setGsWorkspace(workspaces[0].name);
        }
      } catch (err) {
        setError(err.message || 'No se pudo cargar administración');
      } finally {
        setLoading(false);
      }
    }

    loadAll();
  }, [token, scopeProjectId]);

  useEffect(() => {
    if (!gsWorkspace) {
      setGsLayers([]);
      setGsStyles([]);
      return;
    }

    async function loadWorkspaceCatalog() {
      try {
        const [workspaceLayers, workspaceStyles] = await Promise.all([
          adminListGeoServerWorkspaceLayers(token, scopeProjectId, gsWorkspace),
          adminListGeoServerWorkspaceStyles(token, scopeProjectId, gsWorkspace),
        ]);
        setGsLayers(workspaceLayers);
        setGsStyles(workspaceStyles);
      } catch (err) {
        setError(err.message || 'No se pudo cargar catálogo GeoServer');
      }
    }

    loadWorkspaceCatalog();
  }, [token, scopeProjectId, gsWorkspace]);

  useEffect(() => {
    if (!layerForm.geoserver_workspace || !layerForm.geoserver_layer_name) {
      setGsLayerStyles([]);
      return;
    }

    async function loadLayerStyles() {
      try {
        const styles = await adminListGeoServerLayerStyles(
          token,
          scopeProjectId,
          layerForm.geoserver_workspace,
          layerForm.geoserver_layer_name,
        );
        setGsLayerStyles(styles);
      } catch {
        setGsLayerStyles([]);
      }
    }

    loadLayerStyles();
  }, [token, scopeProjectId, layerForm.geoserver_workspace, layerForm.geoserver_layer_name]);

  useEffect(() => {
    if (!activeProject) {
      setLayerAssignments({});
      setLayerOrder([]);
      setFormFields([]);
      setProjectForm(emptyProjectForm());
      return;
    }

    setProjectForm({
      id: activeProject.id,
      name: activeProject.name,
      description: activeProject.description || '',
      centerLng: Number(activeProject.default_map_center?.[0] ?? -77.0428),
      centerLat: Number(activeProject.default_map_center?.[1] ?? -12.0464),
      zoom: Number(activeProject.default_zoom ?? 13),
    });

    const sortedProjectLayers = [...(activeProject.default_base_layers || [])].sort(
      (a, b) => (a.z_index_override ?? 0) - (b.z_index_override ?? 0),
    );

    const assignmentMap = {};
    for (const row of sortedProjectLayers) {
      assignmentMap[String(row.layer_id)] = {
        attached: true,
        available_override: row.available_override !== false,
        visible_override: row.visible_override !== false,
        delete_mark: false,
      };
    }
    setLayerAssignments(assignmentMap);
    setLayerOrder(sortedProjectLayers.map((row) => String(row.layer_id)));

    setFormFields((activeProject.form_configuration || []).map(parseFieldFromApi));
  }, [activeProject]);

  async function withAction(action) {
    setError('');
    setMessage('');
    setLoading(true);
    try {
      await action();
      await refreshAdminData();
      await onDataChanged?.();
      setMessage('Cambios guardados');
    } catch (err) {
      setError(err.message || 'No se pudo completar la acción');
    } finally {
      setLoading(false);
    }
  }

  function useCurrentViewerCenter() {
    const view = parseMapViewFromStorage();
    if (!view) {
      setError('No hay vista actual del mapa para reutilizar');
      return;
    }
    setProjectForm((current) => ({
      ...current,
      centerLng: view.centerLng,
      centerLat: view.centerLat,
      zoom: normalizeZoom(view.zoom),
    }));
    setMessage('Centro y zoom tomados del visor');
  }

  async function handleCreateProject() {
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const created = await adminCreateProject(token, scopeProjectId, {
        name: projectForm.name,
        description: projectForm.description,
        default_map_center: [Number(projectForm.centerLng), Number(projectForm.centerLat)],
        default_zoom: normalizeZoom(projectForm.zoom),
      });
      await refreshAdminData();
      setActiveProjectId(String(created.id));
      await onDataChanged?.();
      setMessage('Proyecto creado');
    } catch (err) {
      setError(err.message || 'No se pudo crear el proyecto');
    } finally {
      setLoading(false);
    }
  }

  function handleFieldDrop(targetIndex) {
    if (draggingFieldIndex === null || draggingFieldIndex === targetIndex) return;
    setFormFields((current) => moveItem(current, draggingFieldIndex, targetIndex));
    setDraggingFieldIndex(null);
  }

  function handleLayerDrop(targetLayerId) {
    if (!draggingLayerId || draggingLayerId === targetLayerId) return;
    const fromIndex = attachedLayerIds.findIndex((id) => id === draggingLayerId);
    const toIndex = attachedLayerIds.findIndex((id) => id === targetLayerId);
    if (fromIndex === -1 || toIndex === -1) return;

    const reorderedAttached = moveItem(attachedLayerIds, fromIndex, toIndex);
    const remaining = layerOrder.filter((id) => !layerAssignments[id]?.attached);
    setLayerOrder([...reorderedAttached, ...remaining]);
    setDraggingLayerId(null);
  }

  return (
    <main className="admin-shell">
      <Card className="admin-topbar">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Administración</h1>
          <p>Gestiona proyectos, capas, formularios y usuarios.</p>
        </div>
        <div className="admin-toolbar">
          <label>
            Contexto
            <Select value={scopeProjectId} onChange={(event) => setScopeProjectId(event.target.value)}>
              {memberships.map((membership) => (
                <option key={membership.id} value={membership.id}>
                  {membership.name} ({membership.role})
                </option>
              ))}
            </Select>
          </label>
          <Button type="button" variant="outline" onClick={onBack}>
            Volver al visor
          </Button>
        </div>
      </Card>

      <section className="admin-tabs">
        {[
          ['projects', 'Proyectos'],
          ['layers', 'Capas'],
          ['fields', 'Campos'],
          ['users', 'Usuarios'],
        ].map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? 'active' : ''}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </section>

      {(error || message) && (
        <Card className="admin-feedback">
          {error && <p className="error">{error}</p>}
          {!error && message && <p className="ok">{message}</p>}
        </Card>
      )}
      {loading && (
        <Card className="admin-feedback animate-pulse">
          <div className="h-3 w-1/3 rounded bg-zinc-200" />
          <div className="mt-2 h-3 w-2/3 rounded bg-zinc-200" />
        </Card>
      )}

      {tab === 'projects' && (
        <section className="admin-grid one-col">
          <Card className="admin-card">
            <CardHeader>
              <CardTitle>Editar proyecto activo</CardTitle>
              <CardDescription>Configura nombre, centro y zoom del proyecto seleccionado.</CardDescription>
            </CardHeader>
            <CardContent>
            {!activeProject && <p>No se encontró proyecto activo en el contexto actual.</p>}
            {activeProject && (
              <form
                className="admin-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  withAction(async () => {
                    await adminUpdateProject(token, scopeProjectId, activeProject.id, {
                      name: projectForm.name,
                      description: projectForm.description,
                      default_map_center: [Number(projectForm.centerLng), Number(projectForm.centerLat)],
                      default_zoom: normalizeZoom(projectForm.zoom),
                    });
                  });
                }}
              >
                <label>
                  Nombre
                  <Input
                    value={projectForm.name}
                    onChange={(event) => setProjectForm((current) => ({ ...current, name: event.target.value }))}
                    required
                  />
                </label>
                <label>
                  Descripción
                  <textarea
                    className="min-h-[88px] rounded-md border border-input bg-white px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={projectForm.description}
                    onChange={(event) =>
                      setProjectForm((current) => ({ ...current, description: event.target.value }))
                    }
                  />
                </label>
                <div className="inline-fields">
                  <label>
                    Centro LNG
                    <Input
                      type="number"
                      value={projectForm.centerLng}
                      onChange={(event) =>
                        setProjectForm((current) => ({ ...current, centerLng: event.target.value }))
                      }
                    />
                  </label>
                  <label>
                    Centro LAT
                    <Input
                      type="number"
                      value={projectForm.centerLat}
                      onChange={(event) =>
                        setProjectForm((current) => ({ ...current, centerLat: event.target.value }))
                      }
                    />
                  </label>
                  <label>
                    Zoom
                    <Input
                      type="number"
                      step="1"
                      value={projectForm.zoom}
                      onChange={(event) => setProjectForm((current) => ({ ...current, zoom: event.target.value }))}
                    />
                  </label>
                </div>
                <div className="actions">
                  <Button type="button" variant="outline" onClick={useCurrentViewerCenter} disabled={loading}>
                    Centrar desde visor
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCreateProject}
                    disabled={loading || !canCreateProject || !projectForm.name}
                    title={canCreateProject ? '' : 'Solo SuperAdmin puede crear proyectos'}
                  >
                    Crear proyecto
                  </Button>
                  <Button type="submit" disabled={loading}>
                    Guardar proyecto
                  </Button>
                </div>
              </form>
            )}
            </CardContent>
          </Card>
        </section>
      )}

      {tab === 'layers' && (
        <section className="admin-grid two-col">
          <Card className="admin-card">
            <CardHeader>
              <CardTitle>Catálogo de GeoServer</CardTitle>
              <CardDescription>Selecciona workspace, layer, estilo y nombre interno.</CardDescription>
            </CardHeader>
            <CardContent>
            <form
              className="admin-form"
              onSubmit={(event) => {
                event.preventDefault();
                withAction(async () => {
                  if (!activeProject) return;
                  const selectedWorkspace = layerForm.geoserver_workspace || gsWorkspace;
                  const payload = {
                    name: layerForm.name,
                    geoserver_workspace: selectedWorkspace,
                    geoserver_layer_name: layerForm.geoserver_layer_name,
                    style_name: layerForm.style_name || null,
                    type: 'WMS',
                    default_visible: Boolean(layerForm.default_visible),
                    z_index: Number(layerForm.z_index || 0),
                  };
                  const created = await adminCreateLayer(token, scopeProjectId, payload);
                  await adminAttachLayerToProject(token, scopeProjectId, activeProject.id, {
                    layer_id: Number(created.id),
                    available_override: true,
                    visible_override: Boolean(layerForm.default_visible),
                    z_index_override: (attachedLayerIds.length + 1) * 10,
                  });
                  setLayerForm(emptyLayerForm());
                });
              }}
            >
              <div className="inline-fields">
                <label>
                  Workspace
                  <Select
                    value={layerForm.geoserver_workspace || gsWorkspace}
                    onChange={(event) => {
                      const workspace = event.target.value;
                      setGsWorkspace(workspace);
                      setLayerForm((current) => ({
                        ...current,
                        geoserver_workspace: workspace,
                        geoserver_layer_name: '',
                        style_name: '',
                      }));
                    }}
                  >
                    <option value="">Seleccionar workspace</option>
                    {gsWorkspaces.map((workspace) => (
                      <option key={workspace.name} value={workspace.name}>
                        {workspace.name}
                      </option>
                    ))}
                  </Select>
                </label>

                <label>
                  Layer
                  <Select
                    value={layerForm.geoserver_layer_name}
                    onChange={(event) => {
                      const layerName = event.target.value;
                      setLayerForm((current) => ({
                        ...current,
                        geoserver_workspace: current.geoserver_workspace || gsWorkspace,
                        geoserver_layer_name: layerName,
                        name: current.name || layerName,
                      }));
                    }}
                  >
                    <option value="">Seleccionar layer</option>
                    {gsLayers.map((layer) => (
                      <option key={layer.name} value={layer.name}>
                        {layer.name}
                      </option>
                    ))}
                  </Select>
                </label>
              </div>

              <div className="inline-fields">
                <label>
                  Estilo
                  <Select
                    value={layerForm.style_name || ''}
                    onChange={(event) =>
                      setLayerForm((current) => ({ ...current, style_name: event.target.value }))
                    }
                  >
                    <option value="">Sin estilo explícito</option>
                    {[...gsLayerStyles, ...gsStyles]
                      .filter((style, index, list) => list.findIndex((item) => item.name === style.name) === index)
                      .map((style) => (
                        <option key={style.name} value={style.name}>
                          {style.name}
                        </option>
                      ))}
                  </Select>
                </label>
                <label>
                  Nombre (interno)
                  <Input
                    value={layerForm.name}
                    onChange={(event) => setLayerForm((current) => ({ ...current, name: event.target.value }))}
                    required
                  />
                </label>
              </div>

              <div className="actions">
                <Button
                  type="submit"
                  disabled={
                    loading ||
                    !activeProject ||
                    !(layerForm.geoserver_workspace || gsWorkspace) ||
                    !layerForm.geoserver_layer_name ||
                    !layerForm.name
                  }
                >
                  Añadir capa
                </Button>
              </div>
            </form>
            </CardContent>
          </Card>

          <Card className="admin-card">
            <CardHeader>
              <CardTitle>Capas del proyecto</CardTitle>
              <CardDescription>
                Arrastra para ordenar. Marca Disponible o Por defecto, usa Eliminar y guarda los cambios.
              </CardDescription>
            </CardHeader>
            <CardContent>
            <div className="admin-list compact">
              {attachedLayerIds.map((layerId, index) => {
                const layer = layers.find((row) => String(row.id) === layerId);
                if (!layer) return null;
                const assignment = layerAssignments[layerId] || {
                  attached: true,
                  available_override: true,
                  visible_override: true,
                  delete_mark: false,
                };
                return (
                  <div
                    key={layerId}
                    className="layer-row card draggable"
                    draggable
                    onDragStart={() => setDraggingLayerId(layerId)}
                    onDragOver={(event) => event.preventDefault()}
                    onDrop={() => handleLayerDrop(layerId)}
                  >
                    <div>
                      <strong>
                        {index + 1}. {layer.name}
                      </strong>
                      <small>
                        {layer.geoserver_workspace}:{layer.geoserver_layer_name}
                      </small>
                    </div>
                    <div className="inline-fields">
                      <label className="check-inline">
                        <input
                          type="checkbox"
                          checked={assignment.available_override !== false}
                          onChange={(event) =>
                            setLayerAssignments((current) => ({
                              ...current,
                              [layerId]: {
                                ...(current[layerId] || {}),
                                attached: true,
                                available_override: event.target.checked,
                              },
                            }))
                          }
                        />
                        Disponible
                      </label>
                      <label className="check-inline">
                        <input
                          type="checkbox"
                          checked={assignment.visible_override !== false}
                          onChange={(event) =>
                            setLayerAssignments((current) => ({
                              ...current,
                              [layerId]: {
                                ...(current[layerId] || {}),
                                attached: true,
                                visible_override: event.target.checked,
                              },
                            }))
                          }
                        />
                        Por defecto
                      </label>
                      <Button
                        type="button"
                        variant={assignment.delete_mark ? 'destructive' : 'outline'}
                        onClick={() =>
                          setLayerAssignments((current) => ({
                            ...current,
                            [layerId]: {
                              ...(current[layerId] || {}),
                              attached: true,
                              delete_mark: !assignment.delete_mark,
                            },
                          }))
                        }
                      >
                        {assignment.delete_mark ? 'Deshacer' : 'Eliminar'}
                      </Button>
                    </div>
                  </div>
                );
              })}
              {attachedLayerIds.length === 0 && <p>No hay capas añadidas al proyecto.</p>}
            </div>

            <div className="actions">
              <Button
                type="button"
                disabled={loading || !activeProject}
                onClick={() => {
                  withAction(async () => {
                    if (!activeProject) return;

                    const keptIds = attachedLayerIds.filter((layerId) => !layerAssignments[layerId]?.delete_mark);
                    const keptSet = new Set(keptIds);

                    for (let index = 0; index < keptIds.length; index += 1) {
                      const layerId = keptIds[index];
                      const assignment = layerAssignments[layerId] || {};
                      await adminAttachLayerToProject(token, scopeProjectId, activeProject.id, {
                        layer_id: Number(layerId),
                        available_override: assignment.available_override !== false,
                        visible_override: assignment.visible_override !== false,
                        z_index_override: (index + 1) * 10,
                      });
                    }

                    for (const row of activeProject.default_base_layers || []) {
                      if (keptSet.has(String(row.layer_id))) continue;
                      await adminDetachLayerFromProject(token, scopeProjectId, activeProject.id, row.layer_id);
                    }
                  });
                }}
              >
                Guardar
              </Button>
            </div>
            </CardContent>
          </Card>
        </section>
      )}

      {tab === 'fields' && (
        <section className="admin-grid one-col">
          <Card className="admin-card">
            <CardHeader>
              <CardTitle>Campos del formulario del proyecto activo</CardTitle>
              <CardDescription>Arrastra para ordenar el formulario final.</CardDescription>
            </CardHeader>
            <CardContent>
            <Accordion type="single" collapsible defaultValue="campos">
              <AccordionItem value="campos">
                <AccordionTrigger>Editor de campos</AccordionTrigger>
                <AccordionContent>

            <div className="admin-list compact fields-scroll">
              {!formFields.length && (
                <Card className="p-6 text-sm text-zinc-500">
                  No hay campos configurados. Usa "Agregar campo" para comenzar.
                </Card>
              )}
              {formFields.map((field, index) => (
                <div
                  className="card field-row draggable field-card"
                  key={`${field.field_key}-${index}`}
                  draggable
                  onDragStart={() => setDraggingFieldIndex(index)}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={() => handleFieldDrop(index)}
                >
                  <div className="field-header-row">
                    <strong>{field.label || 'Campo sin alias'}</strong>
                    <small>{field.field_key || 'field_key vacío'}</small>
                  </div>

                  <div className="inline-fields field-meta-grid">
                    <label>
                      Nombre de campo
                      <Input
                        value={field.field_key}
                        onChange={(event) =>
                          setFormFields((current) =>
                            current.map((item, idx) =>
                              idx === index ? { ...item, field_key: event.target.value } : item,
                            ),
                          )
                        }
                      />
                    </label>
                    <label>
                      Alias
                      <Input
                        value={field.label}
                        onChange={(event) =>
                          setFormFields((current) =>
                            current.map((item, idx) =>
                              idx === index ? { ...item, label: event.target.value } : item,
                            ),
                          )
                        }
                      />
                    </label>
                    <label>
                      Tipo
                      <Input
                        value={field.field_type}
                        onChange={(event) =>
                          setFormFields((current) =>
                            current.map((item, idx) =>
                              idx === index ? { ...item, field_type: event.target.value } : item,
                            ),
                          )
                        }
                      />
                    </label>
                    <div className="toggle-row">
                      <span>Requerido</span>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={Boolean(field.required)}
                        className={`toggle-switch ${field.required ? 'on' : ''}`}
                        onClick={() =>
                          setFormFields((current) =>
                            current.map((item, idx) =>
                              idx === index ? { ...item, required: !item.required } : item,
                            ),
                          )
                        }
                      >
                        <span className="toggle-knob" />
                      </button>
                    </div>
                    <Button
                      type="button"
                      variant="destructive"
                      onClick={() => setFormFields((current) => current.filter((_, idx) => idx !== index))}
                    >
                      Quitar
                    </Button>
                  </div>

                  <div className="config-table-grid">
                    <Card className="config-table subtle-table">
                      <strong>Visible por tipo_inmueble</strong>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Tipo inmueble</TableHead>
                            <TableHead>Visible</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {PROPERTY_TYPES.map((propertyType) => (
                            <TableRow key={propertyType}>
                              <TableCell>{propertyType}</TableCell>
                              <TableCell>
                                <input
                                  type="checkbox"
                                  checked={field.visible_types.includes(propertyType)}
                                  onChange={(event) =>
                                    setFormFields((current) =>
                                      current.map((item, idx) => {
                                        if (idx !== index) return item;
                                        const visibleSet = new Set(item.visible_types || []);
                                        if (event.target.checked) visibleSet.add(propertyType);
                                        else visibleSet.delete(propertyType);
                                        return { ...item, visible_types: [...visibleSet] };
                                      }),
                                    )
                                  }
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Card>

                    <Card className="config-table subtle-table">
                      <strong>Valores codificados</strong>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Valor</TableHead>
                            <TableHead>Etiqueta</TableHead>
                            <TableHead />
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {(field.coded_pairs || []).map((pair, pairIndex) => (
                            <TableRow key={`${pair.value}-${pairIndex}`}>
                              <TableCell>
                                <Input
                                  value={pair.value}
                                  onChange={(event) =>
                                    setFormFields((current) =>
                                      current.map((item, idx) => {
                                        if (idx !== index) return item;
                                        const nextPairs = [...(item.coded_pairs || [])];
                                        nextPairs[pairIndex] = {
                                          ...nextPairs[pairIndex],
                                          value: event.target.value,
                                        };
                                        return { ...item, coded_pairs: nextPairs };
                                      }),
                                    )
                                  }
                                />
                              </TableCell>
                              <TableCell>
                                <Input
                                  value={pair.label}
                                  onChange={(event) =>
                                    setFormFields((current) =>
                                      current.map((item, idx) => {
                                        if (idx !== index) return item;
                                        const nextPairs = [...(item.coded_pairs || [])];
                                        nextPairs[pairIndex] = {
                                          ...nextPairs[pairIndex],
                                          label: event.target.value,
                                        };
                                        return { ...item, coded_pairs: nextPairs };
                                      }),
                                    )
                                  }
                                />
                              </TableCell>
                              <TableCell>
                                <Button
                                  type="button"
                                  variant="destructive"
                                  size="sm"
                                  onClick={() =>
                                    setFormFields((current) =>
                                      current.map((item, idx) => {
                                        if (idx !== index) return item;
                                        return {
                                          ...item,
                                          coded_pairs: (item.coded_pairs || []).filter(
                                            (_, idxPair) => idxPair !== pairIndex,
                                          ),
                                        };
                                      }),
                                    )
                                  }
                                >
                                  x
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() =>
                          setFormFields((current) =>
                            current.map((item, idx) => {
                              if (idx !== index) return item;
                              return {
                                ...item,
                                coded_pairs: [...(item.coded_pairs || []), { value: '', label: '' }],
                              };
                            }),
                          )
                        }
                      >
                        Añadir fila
                      </Button>
                    </Card>
                  </div>
                </div>
              ))}
            </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>

            <div className="actions">
              <Button
                type="button"
                onClick={() =>
                  setFormFields((current) => [
                    ...current,
                    {
                      field_key: '',
                      label: '',
                      field_type: 'text',
                      required: false,
                      visible_types: [...PROPERTY_TYPES],
                      coded_pairs: [],
                    },
                  ])
                }
              >
                Agregar campo
              </Button>
              <Button
                type="button"
                disabled={loading || !activeProject}
                onClick={() => {
                  withAction(async () => {
                    if (!activeProject) return;
                    await adminReplaceFormFields(
                      token,
                      scopeProjectId,
                      activeProject.id,
                      formFields.map((field, index) => ({
                        field_key: field.field_key.trim(),
                        label: field.label.trim(),
                        field_type: field.field_type.trim(),
                        required: Boolean(field.required),
                        order_index: (index + 1) * 10,
                        config: {
                          visible_for_property_types: field.visible_types || [],
                          coded_values: (field.coded_pairs || []).filter(
                            (pair) => pair.value.trim() && pair.label.trim(),
                          ),
                        },
                      })),
                    );
                  });
                }}
              >
                Guardar campos
              </Button>
            </div>
            </CardContent>
          </Card>
        </section>
      )}

      {tab === 'users' && (
        <section className="admin-grid two-col">
          <Card className="admin-card">
            <CardHeader>
              <CardTitle>Usuarios</CardTitle>
            </CardHeader>
            <CardContent>
            <div className="admin-list compact">
              {users.map((user) => (
                <Card className="user-row" key={user.id}>
                  <strong>{user.email}</strong>
                  <small>{user.is_active ? 'Activo' : 'Inactivo'}</small>
                  <div className="chips">
                    {(user.projects || []).map((link) => (
                      <span key={`${user.id}-${link.project_id}`}>
                        P{link.project_id}: {link.role}
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            withAction(async () =>
                              adminUnassignUserProject(token, scopeProjectId, user.id, link.project_id),
                            )
                          }
                        >
                          x
                        </Button>
                      </span>
                    ))}
                  </div>
                  <div className="inline-fields">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() =>
                        withAction(async () =>
                          adminUpdateUser(token, scopeProjectId, user.id, {
                            is_active: !user.is_active,
                          }),
                        )
                      }
                    >
                      {user.is_active ? 'Desactivar' : 'Activar'}
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
            </CardContent>
          </Card>

          <Card className="admin-card">
            <CardHeader>
              <CardTitle>Alta y asignación</CardTitle>
            </CardHeader>
            <CardContent>
            <Accordion type="single" collapsible defaultValue="alta">
              <AccordionItem value="alta">
                <AccordionTrigger>Crear usuario</AccordionTrigger>
                <AccordionContent>
            <form
              className="admin-form"
              onSubmit={(event) => {
                event.preventDefault();
                withAction(async () => {
                  await adminCreateUser(token, scopeProjectId, createUserForm);
                  setCreateUserForm(emptyUserCreateForm());
                });
              }}
            >
              <label>
                Email
                <Input
                  type="email"
                  value={createUserForm.email}
                  onChange={(event) =>
                    setCreateUserForm((current) => ({ ...current, email: event.target.value }))
                  }
                  required
                />
              </label>
              <label>
                Contraseña
                <Input
                  type="password"
                  value={createUserForm.password}
                  onChange={(event) =>
                    setCreateUserForm((current) => ({ ...current, password: event.target.value }))
                  }
                  required
                />
              </label>
              <label className="check-inline">
                <input
                  type="checkbox"
                  checked={Boolean(createUserForm.is_active)}
                  onChange={(event) =>
                    setCreateUserForm((current) => ({ ...current, is_active: event.target.checked }))
                  }
                />
                Activo
              </label>
              <Button type="submit" disabled={loading}>
                Crear usuario
              </Button>
            </form>
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="asignacion">
                <AccordionTrigger>Asignar proyecto y rol</AccordionTrigger>
                <AccordionContent>

            <form
              className="admin-form"
              onSubmit={(event) => {
                event.preventDefault();
                withAction(async () => {
                  await adminAssignUserProject(token, scopeProjectId, assignForm.userId, {
                    project_id: Number(assignForm.projectId),
                    role: assignForm.role,
                  });
                });
              }}
            >
              <label>
                Usuario
                <Select
                  value={assignForm.userId}
                  onChange={(event) =>
                    setAssignForm((current) => ({ ...current, userId: event.target.value }))
                  }
                >
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.email}
                    </option>
                  ))}
                </Select>
              </label>
              <label>
                Proyecto
                <Select
                  value={assignForm.projectId}
                  onChange={(event) =>
                    setAssignForm((current) => ({ ...current, projectId: event.target.value }))
                  }
                >
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </Select>
              </label>
              <label>
                Rol
                <Select
                  value={assignForm.role}
                  onChange={(event) =>
                    setAssignForm((current) => ({ ...current, role: event.target.value }))
                  }
                >
                  {PROJECT_ROLES.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </Select>
              </label>
              <Button type="submit" disabled={loading || !assignForm.userId || !assignForm.projectId}>
                Asignar
              </Button>
            </form>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
            </CardContent>
          </Card>
        </section>
      )}
    </main>
  );
}
