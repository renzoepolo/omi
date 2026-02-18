export default function FAB({
  open,
  onToggleOpen,
  editEnabled,
  onToggleEditEnabled,
  activeTool,
  onSelectTool,
}) {
  return (
    <div className="fab-wrapper">
      {open && (
        <div className="fab-menu card">
          <label className="fab-switch">
            <input
              type="checkbox"
              checked={editEnabled}
              onChange={(event) => onToggleEditEnabled(event.target.checked)}
            />
            <span>Modo edicion</span>
          </label>

          <button
            type="button"
            disabled={!editEnabled}
            className={activeTool === 'create' ? 'active' : ''}
            onClick={() => onSelectTool('create')}
          >
            Crear punto
          </button>
          <button
            type="button"
            disabled={!editEnabled}
            className={activeTool === 'edit' ? 'active' : ''}
            onClick={() => onSelectTool('edit')}
          >
            Editar punto
          </button>
        </div>
      )}

      <button className="fab-trigger" type="button" onClick={onToggleOpen} aria-label="Acciones de edicion">
        ✎
      </button>
    </div>
  );
}
