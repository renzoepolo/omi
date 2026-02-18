export default function ProjectSelector({ projects, selectedId, onChange }) {
  return (
    <label className="project-selector">
      Proyecto
      <select value={selectedId ?? ''} onChange={(e) => onChange(e.target.value)}>
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>
    </label>
  );
}
