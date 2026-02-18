const STATUS_OPTIONS = [
  { value: 'cargado', label: 'Cargado' },
  { value: 'posicionado', label: 'Posicionado' },
  { value: 'revision', label: 'Revision' },
  { value: 'completado', label: 'Completado' },
  { value: 'outlier', label: 'Outlier' },
  { value: 'eliminado', label: 'Eliminado' },
];

const PROPERTY_TYPE_OPTIONS = [
  { value: 'urbano_baldio', label: 'Urbano Baldio' },
  { value: 'urbano_edificado', label: 'Urbano Edificado' },
  { value: 'rural', label: 'Rural' },
];

const CURRENCY_OPTIONS = [
  { value: '', label: 'Sin moneda' },
  { value: 'ARS', label: 'ARS' },
  { value: 'USD', label: 'USD' },
];

function Row({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value || '-'}</strong>
    </div>
  );
}

function PointFields({ point }) {
  return (
    <div className="point-fields">
      <Row label="Nombre" value={point.name || 'Sin nombre'} />
      <Row label="Descripcion" value={point.description || 'Sin descripcion'} />
      <Row label="Estado" value={point.status} />
      <Row label="Tipo inmueble" value={point.property_type} />
      <Row label="Precio" value={point.price ? `${point.price} ${point.currency || ''}`.trim() : '-'} />
      <Row label="Padron" value={point.location?.padron || '-'} />
      <Row label="Longitud" value={point.coordinates?.[0]?.toFixed?.(5)} />
      <Row label="Latitud" value={point.coordinates?.[1]?.toFixed?.(5)} />

      {point.property_type === 'rural' && (
        <>
          <Row label="Uso principal" value={point.rural?.main_use_code || '-'} />
          <Row label="Superficie regada" value={point.rural?.irrigated_surface || '-'} />
        </>
      )}

      {point.property_type !== 'rural' && (
        <>
          <Row label="Dormitorios" value={point.building?.bedrooms_count ?? '-'} />
          <Row label="Banos" value={point.building?.bathrooms_count ?? '-'} />
          <Row label="Cocheras" value={point.building?.garage_count ?? '-'} />
        </>
      )}
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
  const isRural = point?.property_type === 'rural';

  function patch(partial) {
    onDraftChange({ ...point, ...partial });
  }

  return (
    <aside className={`right-panel ${open ? 'open' : ''}`} aria-hidden={!open}>
      <div className="right-panel-head">
        <div>
          <h2>{isEditing ? (mode === 'create' ? 'Crear observacion' : 'Editar observacion') : 'Consulta'}</h2>
          <p>{isEditing ? 'Completa los datos de la observacion.' : 'Atributos de la observacion seleccionada.'}</p>
        </div>
        <button type="button" className="ghost" onClick={onClose}>
          Cerrar
        </button>
      </div>

      {!point && (
        <div className="right-panel-empty">
          <p>No hay observacion seleccionada.</p>
        </div>
      )}

      {point && !isEditing && <PointFields point={point} />}

      {point && isEditing && (
        <div className="right-panel-form">
          <label>
            Nombre
            <input value={point.name ?? ''} onChange={(event) => patch({ name: event.target.value })} />
          </label>

          <label>
            Descripcion
            <textarea
              rows={3}
              value={point.description ?? ''}
              onChange={(event) => patch({ description: event.target.value })}
            />
          </label>

          <label>
            Tipo de inmueble
            <select
              value={point.property_type ?? 'urbano_baldio'}
              onChange={(event) =>
                patch({
                  property_type: event.target.value,
                  building: event.target.value === 'rural' ? null : point.building || {},
                  rural: event.target.value === 'rural' ? point.rural || {} : null,
                })
              }
            >
              {PROPERTY_TYPE_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Estado
            <select value={point.status ?? 'cargado'} onChange={(event) => patch({ status: event.target.value })}>
              {STATUS_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Precio
            <input
              type="number"
              min="0"
              step="0.01"
              value={point.price ?? ''}
              onChange={(event) => patch({ price: event.target.value })}
            />
          </label>

          <label>
            Moneda
            <select value={point.currency ?? ''} onChange={(event) => patch({ currency: event.target.value })}>
              {CURRENCY_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Padron
            <input
              value={point.location?.padron ?? ''}
              onChange={(event) =>
                patch({
                  location: {
                    ...(point.location || {}),
                    padron: event.target.value,
                  },
                })
              }
            />
          </label>

          {!isRural && (
            <>
              <label>
                Dormitorios
                <input
                  type="number"
                  min="0"
                  value={point.building?.bedrooms_count ?? ''}
                  onChange={(event) =>
                    patch({
                      building: {
                        ...(point.building || {}),
                        bedrooms_count: event.target.value === '' ? null : Number(event.target.value),
                      },
                    })
                  }
                />
              </label>
              <label>
                Banos
                <input
                  type="number"
                  min="0"
                  value={point.building?.bathrooms_count ?? ''}
                  onChange={(event) =>
                    patch({
                      building: {
                        ...(point.building || {}),
                        bathrooms_count: event.target.value === '' ? null : Number(event.target.value),
                      },
                    })
                  }
                />
              </label>
            </>
          )}

          {isRural && (
            <>
              <label>
                Uso principal
                <input
                  value={point.rural?.main_use_code ?? ''}
                  onChange={(event) =>
                    patch({
                      rural: {
                        ...(point.rural || {}),
                        main_use_code: event.target.value,
                      },
                    })
                  }
                />
              </label>
              <label>
                Superficie regada
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={point.rural?.irrigated_surface ?? ''}
                  onChange={(event) =>
                    patch({
                      rural: {
                        ...(point.rural || {}),
                        irrigated_surface: event.target.value,
                      },
                    })
                  }
                />
              </label>
            </>
          )}

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
