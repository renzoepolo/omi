import { useEffect, useRef, useState } from 'react';

export default function UserMenu({ canAccessAdmin, onGoAdmin, onLogout }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    function handleOutside(event) {
      if (!containerRef.current?.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  return (
    <div className="user-menu" ref={containerRef}>
      <button className="user-trigger" onClick={() => setOpen((current) => !current)} type="button">
        <span className="avatar">R</span>
        <span>Renzo</span>
      </button>

      {open && (
        <div className="user-dropdown card">
          {canAccessAdmin && (
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                onGoAdmin();
              }}
            >
              Administracion
            </button>
          )}
          <button
            type="button"
            className="danger"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
          >
            Cerrar sesion
          </button>
        </div>
      )}
    </div>
  );
}
