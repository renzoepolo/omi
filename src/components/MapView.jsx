import { useEffect, useMemo, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const STATUS_COLOR = {
  nuevo: '#2f80ed',
  en_proceso: '#f2994a',
  resuelto: '#27ae60',
  descartado: '#eb5757',
};

const BASEMAPS = {
  osm: {
    id: 'osm',
    name: 'OpenStreetMap',
    style: {
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
    },
  },
  sat: {
    id: 'sat',
    name: 'Satélite',
    style: {
      version: 8,
      sources: {
        sat: {
          type: 'raster',
          tiles: ['https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
          tileSize: 256,
          attribution: 'Esri',
        },
      },
      layers: [{ id: 'sat', type: 'raster', source: 'sat' }],
    },
  },
};

function toFeatureCollection(points) {
  return {
    type: 'FeatureCollection',
    features: points.map((point) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: point.coordinates },
      properties: {
        id: point.id,
        name: point.name || 'Sin nombre',
        status: point.status,
      },
    })),
  };
}

export default function MapView({ project, points, onCreatePoint, onMovePoint, onSelectPoint, selectedId }) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const draggingIdRef = useRef(null);
  const [basemap, setBasemap] = useState('osm');

  const features = useMemo(() => toFeatureCollection(points), [points]);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: BASEMAPS[basemap].style,
      center: project.center,
      zoom: project.zoom,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    mapRef.current = map;

    map.on('load', () => {
      map.addSource('properties-wms', {
        type: 'raster',
        tiles: [
          `${import.meta.env.VITE_GEOSERVER_WMS || 'https://ahocevar.com/geoserver/wms'}?service=WMS&version=1.1.1&request=GetMap&layers=${import.meta.env.VITE_GEOSERVER_LAYER || 'topp:states'}&styles=&bbox={bbox-epsg-3857}&width=256&height=256&srs=EPSG:3857&format=image/png&transparent=true`,
        ],
        tileSize: 256,
      });

      map.addLayer({
        id: 'properties-layer',
        type: 'raster',
        source: 'properties-wms',
        paint: { 'raster-opacity': 0.7 },
      });

      map.addSource('points-source', {
        type: 'geojson',
        data: features,
      });

      map.addLayer({
        id: 'points-layer',
        type: 'circle',
        source: 'points-source',
        paint: {
          'circle-radius': ['case', ['==', ['get', 'id'], selectedId], 9, 7],
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
            '#7f8c8d',
          ],
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 1.5,
        },
      });

      map.on('click', 'points-layer', (event) => {
        const feature = event.features?.[0];
        if (feature?.properties?.id) {
          onSelectPoint(feature.properties.id);
        }
      });

      map.on('mousedown', 'points-layer', (event) => {
        map.getCanvas().style.cursor = 'grabbing';
        draggingIdRef.current = event.features?.[0]?.properties?.id || null;
      });

      map.on('click', (event) => {
        if (event.defaultPrevented || draggingIdRef.current) return;
        onCreatePoint([event.lngLat.lng, event.lngLat.lat]);
      });

      map.on('mousemove', (event) => {
        if (!draggingIdRef.current) return;
        onMovePoint(draggingIdRef.current, [event.lngLat.lng, event.lngLat.lat]);
      });

      map.on('mouseup', () => {
        map.getCanvas().style.cursor = '';
        draggingIdRef.current = null;
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [project.center, project.zoom, basemap, features, onCreatePoint, onMovePoint, onSelectPoint, selectedId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    map.setStyle(BASEMAPS[basemap].style);

    map.once('style.load', () => {
      map.addSource('properties-wms', {
        type: 'raster',
        tiles: [
          `${import.meta.env.VITE_GEOSERVER_WMS || 'https://ahocevar.com/geoserver/wms'}?service=WMS&version=1.1.1&request=GetMap&layers=${import.meta.env.VITE_GEOSERVER_LAYER || 'topp:states'}&styles=&bbox={bbox-epsg-3857}&width=256&height=256&srs=EPSG:3857&format=image/png&transparent=true`,
        ],
        tileSize: 256,
      });
      map.addLayer({ id: 'properties-layer', type: 'raster', source: 'properties-wms', paint: { 'raster-opacity': 0.7 } });
      map.addSource('points-source', { type: 'geojson', data: features });
      map.addLayer({
        id: 'points-layer',
        type: 'circle',
        source: 'points-source',
        paint: {
          'circle-radius': ['case', ['==', ['get', 'id'], selectedId], 9, 7],
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
            '#7f8c8d',
          ],
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 1.5,
        },
      });
    });
  }, [basemap]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const source = map.getSource('points-source');
    if (source) source.setData(features);

    if (map.getLayer('points-layer')) {
      map.setPaintProperty('points-layer', 'circle-radius', ['case', ['==', ['get', 'id'], selectedId], 9, 7]);
    }
  }, [features, selectedId]);

  useEffect(() => {
    mapRef.current?.flyTo({ center: project.center, zoom: project.zoom });
  }, [project]);

  return (
    <section className="map-shell">
      <div className="map-toolbar card">
        <label>
          Capa base
          <select value={basemap} onChange={(e) => setBasemap(e.target.value)}>
            {Object.values(BASEMAPS).map((layer) => (
              <option key={layer.id} value={layer.id}>
                {layer.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div ref={mapContainerRef} className="map-container" />
      <div className="legend card">
        <strong>Estados</strong>
        {Object.entries(STATUS_COLOR).map(([status, color]) => (
          <span key={status}><i style={{ background: color }} /> {status.replace('_', ' ')}</span>
        ))}
      </div>
    </section>
  );
}
