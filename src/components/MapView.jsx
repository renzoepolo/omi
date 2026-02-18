import { useEffect, useMemo, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const STATUS_COLOR = {
  nuevo: '#2f80ed',
  en_proceso: '#f2994a',
  resuelto: '#27ae60',
  descartado: '#eb5757',
};

const BASEMAP_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
};

function toFeatureCollection(points, selectedId, draftPoint) {
  const base = points.map((point) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: point.coordinates },
    properties: {
      id: point.id,
      name: point.name || 'Sin nombre',
      status: point.status,
      isDraft: false,
      isSelected: point.id === selectedId,
    },
  }));

  if (draftPoint) {
    base.push({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: draftPoint.coordinates },
      properties: {
        id: draftPoint.id,
        name: draftPoint.name || 'Nuevo punto',
        status: draftPoint.status || 'nuevo',
        isDraft: true,
        isSelected: true,
      },
    });
  }

  return { type: 'FeatureCollection', features: base };
}

export default function MapView({
  project,
  points,
  selectedId,
  draftPoint,
  mode,
  onMapQuery,
  onPointQuery,
  onCreatePointFromMap,
  onPickPointToEdit,
  onMovePoint,
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const draggingIdRef = useRef(null);
  const modeRef = useRef(mode);
  const pointClickRef = useRef(false);
  const [mapReady, setMapReady] = useState(false);

  const features = useMemo(
    () => toFeatureCollection(points, selectedId, draftPoint),
    [points, selectedId, draftPoint],
  );

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: BASEMAP_STYLE,
      center: project.center,
      zoom: project.zoom,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    mapRef.current = map;

    map.on('load', () => {
      map.addSource('points-source', { type: 'geojson', data: features });
      map.addLayer({
        id: 'points-layer',
        type: 'circle',
        source: 'points-source',
        paint: {
          'circle-radius': [
            'case',
            ['==', ['get', 'isSelected'], true],
            9,
            ['==', ['get', 'isDraft'], true],
            9,
            7,
          ],
          'circle-color': [
            'match',
            ['get', 'status'],
            'nuevo',
            STATUS_COLOR.nuevo,
            'en_proceso',
            STATUS_COLOR.en_proceso,
            'resuelto',
            STATUS_COLOR.resuelto,
            'descartado',
            STATUS_COLOR.descartado,
            '#6f7f94',
          ],
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': ['case', ['==', ['get', 'isSelected'], true], 2.2, 1.2],
          'circle-opacity': ['case', ['==', ['get', 'isDraft'], true], 0.8, 1],
        },
      });

      map.on('mouseenter', 'points-layer', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'points-layer', () => {
        map.getCanvas().style.cursor = '';
      });

      map.on('click', 'points-layer', (event) => {
        const feature = event.features?.[0];
        const pointId = feature?.properties?.id;
        if (!pointId) return;
        pointClickRef.current = true;

        if (modeRef.current === 'edit') {
          onPickPointToEdit(pointId);
          return;
        }
        onPointQuery(pointId);
      });

      map.on('click', (event) => {
        if (pointClickRef.current) {
          pointClickRef.current = false;
          return;
        }
        const coords = [event.lngLat.lng, event.lngLat.lat];
        if (modeRef.current === 'create') {
          onCreatePointFromMap(coords);
          return;
        }
        onMapQuery(coords);
      });

      map.on('mousedown', 'points-layer', (event) => {
        if (modeRef.current !== 'edit') return;
        const pointId = event.features?.[0]?.properties?.id;
        if (!pointId) return;
        draggingIdRef.current = pointId;
      });

      map.on('mousemove', (event) => {
        if (modeRef.current !== 'edit') return;
        if (!draggingIdRef.current) return;
        onMovePoint(draggingIdRef.current, [event.lngLat.lng, event.lngLat.lat]);
      });

      map.on('mouseup', () => {
        draggingIdRef.current = null;
      });

      setMapReady(true);
    });

    return () => {
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, [
    features,
    onCreatePointFromMap,
    onMapQuery,
    onMovePoint,
    onPickPointToEdit,
    onPointQuery,
    project.center,
    project.zoom,
  ]);

  useEffect(() => {
    if (!mapReady) return;
    const source = mapRef.current?.getSource('points-source');
    if (source) source.setData(features);
  }, [features, mapReady]);

  useEffect(() => {
    mapRef.current?.flyTo({ center: project.center, zoom: project.zoom });
  }, [project]);

  return (
    <section className="map-shell">
      <div ref={mapContainerRef} className="map-container" />
      <div className="legend card">
        <strong>Estados</strong>
        {Object.entries(STATUS_COLOR).map(([status, color]) => (
          <span key={status}>
            <i style={{ background: color }} />
            {status.replace('_', ' ')}
          </span>
        ))}
      </div>
    </section>
  );
}
