export default function MapControlButton({ label, icon, onClick, disabled = false, className = '', ariaControls, ariaExpanded }) {
  return (
    <button
      type="button"
      className={`map-control-btn ${className}`}
      onClick={onClick}
      disabled={disabled}
      title={label}
      aria-label={label}
      aria-controls={ariaControls}
      aria-expanded={ariaExpanded}
    >
      <span aria-hidden="true">{icon}</span>
    </button>
  );
}
