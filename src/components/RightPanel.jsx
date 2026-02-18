const STATUS_OPTIONS = [
  { value: 'nuevo', label: 'Nuevo' },
  { value: 'en_proceso', label: 'En proceso' },
  { value: 'resuelto', label: 'Resuelto' },
  { value: 'descartado', label: 'Descartado' },
];

function PointFields({ point }) {
  return (
    <div className="point-fields">
      <div>
        <span>Nombre</span>
        <strong>{point.name || 'Sin nombre'}</strong>
      </div>
      <div>
        <span>Descripcion</span>
        <strong>{point.description || 'Sin descripcion'}</strong>
      </div>
      <div>
        <span>Estado</span>
        <strong>{point.status || '-'}</strong>
      </div>
      <div>
        <span>Longitud</span>
        <strong>{point.coordinates[0].toFixed(5)}</strong>
      </div>
      <div>
        <span>Latitud</span>
        <strong>{point.coordinates[1].toFixed(5)}</strong>
      </div>
    </div>
  );
}

export default function RightPanel({
  open,
  mode,
  point,
  onClose,
  onDraftChange,
  onSaveDraft,
  onCancelDraft,
  saving,
}) {
  const isEditing = mode === 'create' || mode === 'edit';

  return (
    <aside className={`right-panel ${open ? 'open' : ''}`} aria-hidden={!open}>
      <div className="right-panel-head">
        <div>
          <h2>{isEditing ? (mode === 'create' ? 'Crear punto' : 'Editar punto') : 'Consulta'}</h2>
          <p>{isEditing ? 'Completa los atributos del punto.' : 'Atributos del punto seleccionado.'}</p>
        </div>
        <button type="button" className="ghost" onClick={onClose}>
          Cerrar
        </button>
      </div>

      {!point && (
        <div className="right-panel-empty">
          <p>No hay punto seleccionado.</p>
        </div>
      )}

      {point && !isEditing && <PointFields point={point} />}

      {point && isEditing && (
        <div className="right-panel-form">
          <label>
            Nombre
            <input
              value={point.name ?? ''}
              onChange={(event) => onDraftChange({ ...point, name: event.target.value })}
            />
          </label>

          <label>
            Descripcion
            <textarea
              rows={4}
              value={point.description ?? ''}
              onChange={(event) => onDraftChange({ ...point, description: event.target.value })}
            />
          </label>

          <label>
            Estado
            <select
              value={point.status ?? 'nuevo'}
              onChange={(event) => onDraftChange({ ...point, status: event.target.value })}
            >
              {STATUS_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <p className="coords">
            Lon: {point.coordinates[0].toFixed(5)} · Lat: {point.coordinates[1].toFixed(5)}
          </p>

          <div className="actions">
            <button type="button" onClick={onSaveDraft} disabled={saving}>
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
            <button type="button" className="ghost" onClick={onCancelDraft}>
              Cancelar
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
