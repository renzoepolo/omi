import { useEffect, useRef, useState } from 'react';

export default function UserMenu({ onLogout }) {
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
          <button type="button" onClick={() => setOpen(false)}>
            Administracion
          </button>
          <button type="button" onClick={() => setOpen(false)}>
            Mi perfil
          </button>
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
