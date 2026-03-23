export default function MapCard({ title, children, className = '' }) {
  return (
    <section className={`map-card ${className}`}>
      {title && <h3 className="map-card-title">{title}</h3>}
      <div className="map-card-body">{children}</div>
    </section>
  );
}
