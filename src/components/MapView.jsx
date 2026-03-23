import { useEffect, useMemo, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import '../styles/maplibre-controls.css';
import MapCard from './MapCard';

const STATUS_COLOR = {
  cargado: '#2f80ed',
  posicionado: '#49a5ff',
  revision: '#f2994a',
  completado: '#27ae60',
  outlier: '#eb5757',
  eliminado: '#777777',
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
    bing_satellite: {
      type: 'raster',
      tiles: ['https://ecn.t3.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=1'],
      tileSize: 256,
      attribution: '© Microsoft Bing',
    },
  },
  layers: [
    { id: 'base-osm', type: 'raster', source: 'osm', layout: { visibility: 'visible' } },
    { id: 'base-bing', type: 'raster', source: 'bing_satellite', layout: { visibility: 'none' } },
  ],
};

const GEOSERVER_URL = (import.meta.env.VITE_GEOSERVER_URL || '').replace(/\/$/, '');

function toFeatureCollection(points, selectedId, draftPoint) {
  const base = points.map((point) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: point.coordinates },
    properties: {
      id: point.id,
      name: `Obs ${String(point.id).slice(0, 8)}`,
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
        name: `Obs ${String(draftPoint.id).slice(0, 8)}`,
        status: draftPoint.status || 'nuevo',
        isDraft: true,
        isSelected: true,
      },
    });
  }

  return { type: 'FeatureCollection', features: base };
}

function normalizeThematicLayers(project) {
  return (project.default_base_layers || [])
    .filter((item) => item.available_override !== false)
    .filter((item) => item.type === 'WMS')
    .sort((a, b) => (a.z_index || 0) - (b.z_index || 0))
    .map((item) => ({
      ...item,
      mapSourceId: `thematic-source-${item.layer_id}`,
      mapLayerId: `thematic-layer-${item.layer_id}`,
    }));
}

export default function MapView({
  project,
  points,
  selectedId,
  draftPoint,
  mode,
  panelOpen,
  onMapQuery,
  onPointQuery,
  onCreatePointFromMap,
  onPickPointToEdit,
  onMovePoint,
  onViewChange,
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const draggingIdRef = useRef(null);
  const modeRef = useRef(mode);
  const handlersRef = useRef({
    onMapQuery,
    onPointQuery,
    onCreatePointFromMap,
    onPickPointToEdit,
    onMovePoint,
    onViewChange,
  });
  const pointClickRef = useRef(false);
  const thematicRegistryRef = useRef([]);

  const [mapReady, setMapReady] = useState(false);
  const [activeBaseMap, setActiveBaseMap] = useState('osm');
  const [observationsVisible, setObservationsVisible] = useState(true);
  const [thematicVisibility, setThematicVisibility] = useState({});
  const [legendCollapsed, setLegendCollapsed] = useState(false);

  const thematicLayers = useMemo(() => normalizeThematicLayers(project), [project]);
  const emptyFeatureCollection = useMemo(() => ({ type: 'FeatureCollection', features: [] }), []);
  const features = useMemo(
    () => toFeatureCollection(points, selectedId, draftPoint),
    [points, selectedId, draftPoint],
  );

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    handlersRef.current = {
      onMapQuery,
      onPointQuery,
      onCreatePointFromMap,
      onPickPointToEdit,
      onMovePoint,
      onViewChange,
    };
  }, [onCreatePointFromMap, onMapQuery, onMovePoint, onPickPointToEdit, onPointQuery, onViewChange]);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: BASEMAP_STYLE,
      center: project.center,
      zoom: project.zoom,
    });
    map.getCanvas().style.cursor = 'default';

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    mapRef.current = map;

    map.on('load', () => {
      map.addSource('points-source', { type: 'geojson', data: emptyFeatureCollection });
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
            'cargado',
            STATUS_COLOR.cargado,
            'posicionado',
            STATUS_COLOR.posicionado,
            'revision',
            STATUS_COLOR.revision,
            'completado',
            STATUS_COLOR.completado,
            'outlier',
            STATUS_COLOR.outlier,
            'eliminado',
            STATUS_COLOR.eliminado,
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
        map.getCanvas().style.cursor = 'default';
      });

      map.on('click', 'points-layer', (event) => {
        const feature = event.features?.[0];
        const pointId = feature?.properties?.id;
        if (!pointId) return;
        pointClickRef.current = true;

        if (modeRef.current === 'edit') {
          handlersRef.current.onPickPointToEdit(pointId);
          return;
        }
        handlersRef.current.onPointQuery(pointId);
      });

      map.on('click', (event) => {
        if (pointClickRef.current) {
          pointClickRef.current = false;
          return;
        }
        const coords = [event.lngLat.lng, event.lngLat.lat];
        if (modeRef.current === 'create') {
          handlersRef.current.onCreatePointFromMap(coords);
          return;
        }
        handlersRef.current.onMapQuery(coords);
      });

      map.on('mousedown', 'points-layer', (event) => {
        if (modeRef.current !== 'edit') return;
        const pointId = event.features?.[0]?.properties?.id;
        if (!pointId) return;
        map.dragPan.disable();
        draggingIdRef.current = pointId;
      });

      map.on('mousemove', (event) => {
        if (modeRef.current !== 'edit') return;
        if (!draggingIdRef.current) return;
        handlersRef.current.onMovePoint(draggingIdRef.current, [event.lngLat.lng, event.lngLat.lat]);
      });

      map.on('mouseup', () => {
        map.dragPan.enable();
        draggingIdRef.current = null;
      });

      map.on('moveend', () => {
        const center = map.getCenter();
        handlersRef.current.onViewChange?.([center.lng, center.lat], map.getZoom());
      });

      setMapReady(true);
    });

    return () => {
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, [emptyFeatureCollection, project.center, project.zoom]);

  useEffect(() => {
    if (!mapReady) return;
    const source = mapRef.current?.getSource('points-source');
    if (source) source.setData(features);
  }, [features, mapReady]);

  useEffect(() => {
    if (!mapReady || !mapRef.current) return;

    const map = mapRef.current;
    for (const entry of thematicRegistryRef.current) {
      if (map.getLayer(entry.mapLayerId)) map.removeLayer(entry.mapLayerId);
      if (map.getSource(entry.mapSourceId)) map.removeSource(entry.mapSourceId);
    }

    const nextVisibility = {};
    const nextRegistry = [];

    for (const layer of thematicLayers) {
      if (!GEOSERVER_URL) continue;

      const sourceId = layer.mapSourceId;
      const layerId = layer.mapLayerId;
      const wmsUrl = `${GEOSERVER_URL}/${layer.geoserver_workspace}/wms`;
      const visible = layer.default_visible !== false;
      const styleParam = layer.style_name ? encodeURIComponent(layer.style_name) : '';

      map.addSource(sourceId, {
        type: 'raster',
        tiles: [
          `${wmsUrl}?service=WMS&request=GetMap&version=1.1.1&layers=${layer.geoserver_workspace}:${layer.geoserver_layer_name}&styles=${styleParam}&format=image/png&transparent=true&srs=EPSG:3857&bbox={bbox-epsg-3857}&width=256&height=256`,
        ],
        tileSize: 256,
      });

      map.addLayer(
        {
          id: layerId,
          type: 'raster',
          source: sourceId,
          layout: { visibility: visible ? 'visible' : 'none' },
        },
        'points-layer',
      );

      nextVisibility[layer.layer_id] = visible;
      nextRegistry.push(layer);
    }

    thematicRegistryRef.current = nextRegistry;
    setThematicVisibility(nextVisibility);
  }, [mapReady, thematicLayers]);

  useEffect(() => {
    if (!mapReady || !mapRef.current) return;
    mapRef.current.setLayoutProperty('base-osm', 'visibility', activeBaseMap === 'osm' ? 'visible' : 'none');
    mapRef.current.setLayoutProperty('base-bing', 'visibility', activeBaseMap === 'bing' ? 'visible' : 'none');
  }, [activeBaseMap, mapReady]);

  useEffect(() => {
    if (!mapReady || !mapRef.current?.getLayer('points-layer')) return;
    mapRef.current.setLayoutProperty('points-layer', 'visibility', observationsVisible ? 'visible' : 'none');
  }, [mapReady, observationsVisible]);

  useEffect(() => {
    if (!mapReady || !mapRef.current) return;
    for (const layer of thematicLayers) {
      if (!mapRef.current.getLayer(layer.mapLayerId)) continue;
      const visible = thematicVisibility[layer.layer_id] !== false;
      mapRef.current.setLayoutProperty(layer.mapLayerId, 'visibility', visible ? 'visible' : 'none');
    }
  }, [mapReady, thematicLayers, thematicVisibility]);

  useEffect(() => {
    mapRef.current?.flyTo({ center: project.center, zoom: project.zoom });
  }, [project.center, project.zoom]);

  useEffect(() => {
    const isSmall = window.matchMedia('(max-width: 768px)').matches;
    setLegendCollapsed(isSmall);
  }, []);

  const legendHeight = legendCollapsed ? '52px' : '170px';

  return (
    <section className={`map-shell ${panelOpen ? 'panel-open' : ''}`}>
      <div ref={mapContainerRef} className="map-container" />

      <div className="map-overlay-root" style={{ '--legend-h': legendHeight }}>
        <div className="dock dock-bl">
          <MapCard title="Leyenda" className={`legend-card ${legendCollapsed ? 'collapsed' : ''}`}>
            <button
              type="button"
              className="legend-toggle"
              onClick={() => setLegendCollapsed((current) => !current)}
            >
              {legendCollapsed ? 'Mostrar' : 'Ocultar'}
            </button>
            {!legendCollapsed && (
              <div className="legend-scroll">
                {Object.entries(STATUS_COLOR).map(([status, color]) => (
                  <span key={status} className="legend-item">
                    <i style={{ background: color }} />
                    {status.replace('_', ' ')}
                  </span>
                ))}
              </div>
            )}
          </MapCard>
        </div>

        <div className="dock dock-bl-above">
          <MapCard title="Capas">
            <strong>Observaciones</strong>
            <label>
              <input
                type="checkbox"
                checked={observationsVisible}
                onChange={(event) => setObservationsVisible(event.target.checked)}
              />
              Mostrar observaciones
            </label>

            <strong>Capas tematicas</strong>
            {thematicLayers.length === 0 && <small>Sin capas configuradas</small>}
            {thematicLayers.map((layer) => (
              <label key={layer.layer_id}>
                <input
                  type="checkbox"
                  checked={thematicVisibility[layer.layer_id] !== false}
                  onChange={(event) =>
                    setThematicVisibility((current) => ({
                      ...current,
                      [layer.layer_id]: event.target.checked,
                    }))
                  }
                />
                {layer.name}
              </label>
            ))}

            <strong>Mapas base</strong>
            <label>
              <input
                type="radio"
                name="base-map"
                checked={activeBaseMap === 'osm'}
                onChange={() => setActiveBaseMap('osm')}
              />
              OpenStreetMap
            </label>
            <label>
              <input
                type="radio"
                name="base-map"
                checked={activeBaseMap === 'bing'}
                onChange={() => setActiveBaseMap('bing')}
              />
              Bing satelite
            </label>
          </MapCard>
        </div>
      </div>
    </section>
  );
}
