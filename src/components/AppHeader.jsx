import ProjectSelector from './ProjectSelector';
import UserMenu from './UserMenu';

export default function AppHeader({ projects, selectedProjectId, onProjectChange, onLogout }) {
  return (
    <header className="app-header">
      <div className="brand-block">
        <div className="logo-placeholder" aria-hidden>
          O
        </div>
        <span className="brand-name">OMI Visor</span>
      </div>

      <ProjectSelector projects={projects} selectedId={selectedProjectId} onChange={onProjectChange} />

      <UserMenu onLogout={onLogout} />
    </header>
  );
}
