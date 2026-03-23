import { useEffect, useRef, useState } from 'react';
import MapControlButton from './MapControlButton';

export default function FAB({
  panelOpen,
  editEnabled,
  onToggleEditEnabled,
  activeTool,
  onSelectTool,
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(event.target)) setOpen(false);
    }

    function handleEsc(event) {
      if (event.key === 'Escape') setOpen(false);
    }

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEsc);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEsc);
    };
  }, []);

  return (
    <div ref={rootRef} className={`fab-wrapper ${panelOpen ? 'panel-open' : ''}`}>
      <div id="map-fab-menu" className={`fab-vertical-menu ${open ? 'open' : ''}`}>
        <div className="fab-label-wrap">
          <span className="fab-label">Modo edición</span>
          <button
            type="button"
            className={`fab-edit-toggle ${editEnabled ? 'on' : ''}`}
            onClick={() => onToggleEditEnabled(!editEnabled)}
            aria-pressed={editEnabled}
          >
            {editEnabled ? 'On' : 'Off'}
          </button>
        </div>
        <div className="fab-action-row">
          <span className="fab-label">Crear punto</span>
          <MapControlButton
            label="Crear punto"
            icon="+"
            onClick={() => {
              onSelectTool('create');
              setOpen(false);
            }}
            disabled={!editEnabled}
            className={activeTool === 'create' ? 'active' : ''}
          />
        </div>
        <div className="fab-action-row">
          <span className="fab-label">Editar punto</span>
          <MapControlButton
            label="Editar punto"
            icon="✎"
            onClick={() => {
              onSelectTool('edit');
              setOpen(false);
            }}
            disabled={!editEnabled}
            className={activeTool === 'edit' ? 'active' : ''}
          />
        </div>
      </div>

      <MapControlButton
        label="Controles de edición"
        icon="☰"
        onClick={() => setOpen((current) => !current)}
        ariaControls="map-fab-menu"
        ariaExpanded={open}
        className="fab-main-btn"
      />
    </div>
  );
}
