const STATUS_OPTIONS = [
  { value: 'nuevo', label: 'Nuevo' },
  { value: 'en_proceso', label: 'En proceso' },
  { value: 'resuelto', label: 'Resuelto' },
  { value: 'descartado', label: 'Descartado' },
];

export default function PointPanel({ selectedPoint, onUpdate, onDelete, onSave, saving }) {
  if (!selectedPoint) {
    return (
      <aside className="panel card">
        <h2>Punto</h2>
        <p>Selecciona un punto del mapa o crea uno tocando/clicando en el mapa.</p>
      </aside>
    );
  }

  return (
    <aside className="panel card">
      <h2>Editar punto</h2>
      <label>
        Nombre
        <input
          value={selectedPoint.name ?? ''}
          onChange={(e) => onUpdate({ ...selectedPoint, name: e.target.value })}
        />
      </label>
      <label>
        Descripción
        <textarea
          rows={3}
          value={selectedPoint.description ?? ''}
          onChange={(e) => onUpdate({ ...selectedPoint, description: e.target.value })}
        />
      </label>
      <label>
        Estado
        <select
          value={selectedPoint.status}
          onChange={(e) => onUpdate({ ...selectedPoint, status: e.target.value })}
        >
          {STATUS_OPTIONS.map((status) => (
            <option key={status.value} value={status.value}>
              {status.label}
            </option>
          ))}
        </select>
      </label>
      <p className="coords">
        Lon: {selectedPoint.coordinates[0].toFixed(5)} · Lat: {selectedPoint.coordinates[1].toFixed(5)}
      </p>
      <div className="actions">
        <button onClick={onSave} disabled={saving}>{saving ? 'Guardando...' : 'Guardar cambios'}</button>
        <button className="ghost" onClick={() => onDelete(selectedPoint.id)}>
          Eliminar punto
        </button>
      </div>
    </aside>
  );
}
