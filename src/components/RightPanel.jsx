import { useState } from 'react';
import OVI_ENUMS from '../../shared/ovi_enums.json';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select } from './ui/select';

const STATUS_OPTIONS = [
  { value: 'cargado', label: 'Cargado' },
  { value: 'posicionado', label: 'Posicionado' },
  { value: 'revision', label: 'Revision' },
  { value: 'completado', label: 'Completado' },
  { value: 'outlier', label: 'Outlier' },
  { value: 'eliminado', label: 'Eliminado' },
];

const ALIAS = {
  TIPO_INMUEBLE: 'Tipo de inmueble',
  ORIGEN_VALOR: 'Origen del valor',
  SUPERFICIE: 'Superficie',
  UNI_SUP: 'Unidad de superficie',
  MONEDA: 'Moneda',
  VALOR_TOTAL: 'Valor total',
  NOMENCLATURA: 'Nomenclatura',
  AFECTACION: 'Afectacion',
  FRENTE: 'Frente',
  FORMA: 'Forma',
  UBIC_CUADRA: 'Ubicacion en cuadra',
  TIPO_BARRIO: 'Tipo de barrio',
  SIT_JURIDICA: 'Situacion juridica',
  FECHA_VALOR: 'Fecha de valor',
  PROCEDENCIA: 'Procedencia',
  TELEFONO: 'Telefono',
  FOTO_FACHADA: 'Foto fachada',
  FOTO_CARTEL: 'Foto cartel',
  LINK: 'Link',
};

function toText(value) {
  return value === null || value === undefined ? '' : String(value);
}

function optionsFor(field) {
  return OVI_ENUMS[field] || [];
}

function allowedSetFor(field) {
  return new Set(optionsFor(field).map((row) => Number(row.code)));
}

function labelFor(field, value) {
  const code = Number(value);
  const found = optionsFor(field).find((row) => Number(row.code) === code);
  return found ? `${found.code} - ${found.label}` : '-';
}

function Row({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value || '-'}</strong>
    </div>
  );
}

function EnumField({ field, value, onChange, disabled = false, error = '' }) {
  return (
    <label className="break-words">
      {ALIAS[field] || field}
      <Select
        value={toText(value)}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        className={`w-full transition-all duration-200 ${error ? 'border-red-500 focus-visible:ring-red-300' : ''}`}
      >
        <option value="">Seleccionar opcion</option>
        {optionsFor(field).map((item) => (
          <option key={`${field}-${item.code}`} value={item.code}>
            {item.code} - {item.label}
          </option>
        ))}
      </Select>
      {error && <small className="text-xs text-red-600">{error}</small>}
    </label>
  );
}

function SectionCard({ title, open, onToggle, children }) {
  return (
    <section className="card ovi-section transition-all duration-200">
      <button type="button" className="ovi-section-trigger" onClick={onToggle} aria-expanded={open}>
        <h3>{title}</h3>
        <span>{open ? '−' : '+'}</span>
      </button>
      <div className={`ovi-collapse ${open ? 'open' : ''}`}>
        <div className="ovi-collapse-inner">{children}</div>
      </div>
    </section>
  );
}

function isOviUrbanoBaldioValid(ovi) {
  if (!ovi) return false;

  const requiredKeys = [
    'TIPO_INMUEBLE',
    'ORIGEN_VALOR',
    'SUPERFICIE',
    'UNI_SUP',
    'MONEDA',
    'VALOR_TOTAL',
    'NOMENCLATURA',
    'AFECTACION',
    'FRENTE',
    'FORMA',
    'UBIC_CUADRA',
    'TIPO_BARRIO',
    'SIT_JURIDICA',
    'FECHA_VALOR',
    'PROCEDENCIA',
  ];
  for (const key of requiredKeys) {
    if (ovi[key] === '' || ovi[key] === null || ovi[key] === undefined) return false;
  }

  const enumFields = [
    'TIPO_INMUEBLE',
    'ORIGEN_VALOR',
    'UNI_SUP',
    'MONEDA',
    'AFECTACION',
    'FORMA',
    'UBIC_CUADRA',
    'TIPO_BARRIO',
    'SIT_JURIDICA',
    'PROCEDENCIA',
  ];
  for (const field of enumFields) {
    if (!allowedSetFor(field).has(Number(ovi[field]))) return false;
  }

  if (Number(ovi.TIPO_INMUEBLE) !== 0) return false;
  if (Number(ovi.UNI_SUP) !== 0) return false;

  const procedencia = Number(ovi.PROCEDENCIA);
  if (procedencia === 0) {
    if (!ovi.FOTO_FACHADA || !ovi.FOTO_CARTEL) return false;
    if (ovi.LINK) return false;
  }
  if (procedencia === 1) {
    if (!ovi.LINK) return false;
    if (ovi.FOTO_FACHADA || ovi.FOTO_CARTEL) return false;
  }
  if (procedencia !== 0 && procedencia !== 1) {
    if (ovi.FOTO_FACHADA || ovi.FOTO_CARTEL || ovi.LINK) return false;
  }
  return true;
}

function PointFields({ point }) {
  const ovi = point.ovi_urbano_baldio || {};
  return (
    <div className="point-fields">
      <Row label="Estado" value={point.status} />
      <Row label={ALIAS.TIPO_INMUEBLE} value={labelFor('TIPO_INMUEBLE', ovi.TIPO_INMUEBLE)} />
      <Row label={ALIAS.ORIGEN_VALOR} value={labelFor('ORIGEN_VALOR', ovi.ORIGEN_VALOR)} />
      <Row label={ALIAS.MONEDA} value={labelFor('MONEDA', ovi.MONEDA)} />
      <Row label={ALIAS.PROCEDENCIA} value={labelFor('PROCEDENCIA', ovi.PROCEDENCIA)} />
      <Row label={ALIAS.NOMENCLATURA} value={ovi.NOMENCLATURA} />
      <Row label={ALIAS.VALOR_TOTAL} value={ovi.VALOR_TOTAL} />
      <Row label={ALIAS.SUPERFICIE} value={ovi.SUPERFICIE} />
      <Row label="Longitud" value={point.coordinates?.[0]?.toFixed?.(5)} />
      <Row label="Latitud" value={point.coordinates?.[1]?.toFixed?.(5)} />
    </div>
  );
}

export default function RightPanel({
  open,
  mode,
  point,
  onClose,
  onDraftChange,
  onSaveDraft,
  onCancelDraft,
  saving,
}) {
  const [sections, setSections] = useState({
    market: true,
    property: true,
    source: true,
  });

  const isEditing = mode === 'create' || mode === 'edit';
  const ovi = point?.ovi_urbano_baldio || {};
  const procedencia = Number(ovi.PROCEDENCIA);
  const isProcedenciaCampo = procedencia === 0;
  const isProcedenciaWeb = procedencia === 1;
  const canSave = !isEditing || isOviUrbanoBaldioValid(ovi);

  function patch(partial) {
    onDraftChange({ ...point, ...partial });
  }

  function patchOvi(field, value) {
    patch({
      property_type: 'urbano_baldio',
      ovi_urbano_baldio: {
        ...(point.ovi_urbano_baldio || {}),
        [field]: value,
      },
    });
  }

  function onProcedenciaChange(value) {
    const proc = Number(value);
    patch({
      property_type: 'urbano_baldio',
      ovi_urbano_baldio: {
        ...(point.ovi_urbano_baldio || {}),
        PROCEDENCIA: proc,
        FOTO_FACHADA: proc === 0 ? toText(ovi.FOTO_FACHADA) : '',
        FOTO_CARTEL: proc === 0 ? toText(ovi.FOTO_CARTEL) : '',
        LINK: proc === 1 ? toText(ovi.LINK) : '',
      },
    });
  }

  function requiredError(value) {
    return value === '' || value === null || value === undefined ? 'Campo obligatorio' : '';
  }

  return (
    <aside className={`right-panel ${open ? 'open' : ''}`} aria-hidden={!open}>
      <div className="right-panel-head">
        <div>
          <h2>{isEditing ? (mode === 'create' ? 'Crear observacion' : 'Editar observacion') : 'Consulta'}</h2>
          <p>{isEditing ? 'Gestiona los atributos del punto seleccionado.' : 'Detalle de la observacion seleccionada.'}</p>
        </div>
        <Button type="button" variant="outline" onClick={onClose}>
          Cerrar
        </Button>
      </div>

      {!point && (
        <div className="right-panel-empty card p-6">
          <p>Selecciona un punto en el mapa para ver sus atributos.</p>
        </div>
      )}

      {point && !isEditing && <PointFields point={point} />}

      {point && isEditing && (
        <div className="right-panel-scroll">
          <div className="right-panel-content">
            <div className="right-panel-form space-y-4">
              <label className="break-words">
                Estado
                <Select className="w-full transition-all duration-200" value={point.status ?? 'cargado'} onChange={(event) => patch({ status: event.target.value })}>
                  {STATUS_OPTIONS.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </Select>
              </label>

              <SectionCard
                title="Info del mercado"
                open={sections.market}
                onToggle={() => setSections((current) => ({ ...current, market: !current.market }))}
              >
                <div className="ovi-fields-grid">
                  <EnumField field="TIPO_INMUEBLE" value={0} onChange={(value) => patchOvi('TIPO_INMUEBLE', value)} disabled />
                  <EnumField field="ORIGEN_VALOR" value={ovi.ORIGEN_VALOR} onChange={(value) => patchOvi('ORIGEN_VALOR', value)} error={requiredError(ovi.ORIGEN_VALOR)} />
                  <label className="break-words">
                    {ALIAS.SUPERFICIE}
                    <Input className={`w-full transition-all duration-200 ${requiredError(ovi.SUPERFICIE) ? 'border-red-500 focus-visible:ring-red-300' : ''}`} type="number" value={toText(ovi.SUPERFICIE)} onChange={(event) => patchOvi('SUPERFICIE', event.target.value)} />
                    {requiredError(ovi.SUPERFICIE) && <small className="text-xs text-red-600">{requiredError(ovi.SUPERFICIE)}</small>}
                  </label>
                  <EnumField field="UNI_SUP" value={0} onChange={(value) => patchOvi('UNI_SUP', value)} disabled />
                  <EnumField field="MONEDA" value={ovi.MONEDA} onChange={(value) => patchOvi('MONEDA', value)} error={requiredError(ovi.MONEDA)} />
                  <label className="break-words">
                    {ALIAS.VALOR_TOTAL}
                    <Input className={`w-full transition-all duration-200 ${requiredError(ovi.VALOR_TOTAL) ? 'border-red-500 focus-visible:ring-red-300' : ''}`} type="number" step="0.01" value={toText(ovi.VALOR_TOTAL)} onChange={(event) => patchOvi('VALOR_TOTAL', event.target.value)} />
                    {requiredError(ovi.VALOR_TOTAL) && <small className="text-xs text-red-600">{requiredError(ovi.VALOR_TOTAL)}</small>}
                  </label>
                </div>
              </SectionCard>

              <SectionCard
                title="Info del inmueble"
                open={sections.property}
                onToggle={() => setSections((current) => ({ ...current, property: !current.property }))}
              >
                <div className="ovi-fields-grid">
                  <label className="break-words">
                    {ALIAS.NOMENCLATURA}
                    <Input className={`w-full transition-all duration-200 ${requiredError(ovi.NOMENCLATURA) ? 'border-red-500 focus-visible:ring-red-300' : ''}`} value={toText(ovi.NOMENCLATURA)} onChange={(event) => patchOvi('NOMENCLATURA', event.target.value)} />
                    {requiredError(ovi.NOMENCLATURA) && <small className="text-xs text-red-600">{requiredError(ovi.NOMENCLATURA)}</small>}
                  </label>
                  <EnumField field="AFECTACION" value={ovi.AFECTACION} onChange={(value) => patchOvi('AFECTACION', value)} error={requiredError(ovi.AFECTACION)} />
                  <label className="break-words">
                    {ALIAS.FRENTE}
                    <Input className={`w-full transition-all duration-200 ${requiredError(ovi.FRENTE) ? 'border-red-500 focus-visible:ring-red-300' : ''}`} type="number" value={toText(ovi.FRENTE)} onChange={(event) => patchOvi('FRENTE', event.target.value)} />
                    {requiredError(ovi.FRENTE) && <small className="text-xs text-red-600">{requiredError(ovi.FRENTE)}</small>}
                  </label>
                  <EnumField field="FORMA" value={ovi.FORMA} onChange={(value) => patchOvi('FORMA', value)} error={requiredError(ovi.FORMA)} />
                  <EnumField field="UBIC_CUADRA" value={ovi.UBIC_CUADRA} onChange={(value) => patchOvi('UBIC_CUADRA', value)} error={requiredError(ovi.UBIC_CUADRA)} />
                  <EnumField field="TIPO_BARRIO" value={ovi.TIPO_BARRIO} onChange={(value) => patchOvi('TIPO_BARRIO', value)} error={requiredError(ovi.TIPO_BARRIO)} />
                  <EnumField field="SIT_JURIDICA" value={ovi.SIT_JURIDICA} onChange={(value) => patchOvi('SIT_JURIDICA', value)} error={requiredError(ovi.SIT_JURIDICA)} />
                  <label className="break-words">
                    {ALIAS.FECHA_VALOR}
                    <Input className={`w-full transition-all duration-200 ${requiredError(ovi.FECHA_VALOR) ? 'border-red-500 focus-visible:ring-red-300' : ''}`} type="date" value={toText(ovi.FECHA_VALOR)} onChange={(event) => patchOvi('FECHA_VALOR', event.target.value)} />
                    {requiredError(ovi.FECHA_VALOR) && <small className="text-xs text-red-600">{requiredError(ovi.FECHA_VALOR)}</small>}
                  </label>
                </div>
              </SectionCard>

              <SectionCard
                title="Procedencia"
                open={sections.source}
                onToggle={() => setSections((current) => ({ ...current, source: !current.source }))}
              >
                <div className="ovi-fields-grid">
                  <EnumField field="PROCEDENCIA" value={ovi.PROCEDENCIA} onChange={onProcedenciaChange} error={requiredError(ovi.PROCEDENCIA)} />
                  <label className="break-words">
                    {ALIAS.TELEFONO}
                    <Input className="w-full transition-all duration-200" value={toText(ovi.TELEFONO)} onChange={(event) => patchOvi('TELEFONO', event.target.value)} />
                  </label>
                  {isProcedenciaCampo && (
                    <>
                      <label className="break-words">
                        {ALIAS.FOTO_FACHADA}
                        <Input className={`w-full transition-all duration-200 ${requiredError(ovi.FOTO_FACHADA) ? 'border-red-500 focus-visible:ring-red-300' : ''}`} value={toText(ovi.FOTO_FACHADA)} onChange={(event) => patchOvi('FOTO_FACHADA', event.target.value)} />
                        {requiredError(ovi.FOTO_FACHADA) && <small className="text-xs text-red-600">{requiredError(ovi.FOTO_FACHADA)}</small>}
                      </label>
                      <label className="break-words">
                        {ALIAS.FOTO_CARTEL}
                        <Input className={`w-full transition-all duration-200 ${requiredError(ovi.FOTO_CARTEL) ? 'border-red-500 focus-visible:ring-red-300' : ''}`} value={toText(ovi.FOTO_CARTEL)} onChange={(event) => patchOvi('FOTO_CARTEL', event.target.value)} />
                        {requiredError(ovi.FOTO_CARTEL) && <small className="text-xs text-red-600">{requiredError(ovi.FOTO_CARTEL)}</small>}
                      </label>
                    </>
                  )}
                  {isProcedenciaWeb && (
                    <label className="break-words">
                      {ALIAS.LINK}
                      <Input className={`w-full transition-all duration-200 ${requiredError(ovi.LINK) ? 'border-red-500 focus-visible:ring-red-300' : ''}`} value={toText(ovi.LINK)} onChange={(event) => patchOvi('LINK', event.target.value)} />
                      {requiredError(ovi.LINK) && <small className="text-xs text-red-600">{requiredError(ovi.LINK)}</small>}
                    </label>
                  )}
                </div>
              </SectionCard>

              {!canSave && <p className="text-xs text-red-600 break-words">Completa campos obligatorios y reglas condicionales para poder guardar.</p>}
              <p className="coords">Lon: {point.coordinates[0].toFixed(5)} · Lat: {point.coordinates[1].toFixed(5)}</p>
            </div>

            <div className="actions right-panel-submit-bar">
              <Button type="button" onClick={onSaveDraft} disabled={saving || !canSave} className="transition-all duration-200">
                {saving ? 'Guardando...' : 'Guardar'}
              </Button>
              <Button type="button" variant="ghost" onClick={onCancelDraft} className="transition-all duration-200">
                Cancelar
              </Button>
            </div>
            {saving && (
              <div className="card p-4 animate-pulse">
                <div className="h-3 w-1/3 bg-zinc-200 rounded mb-2" />
                <div className="h-3 w-2/3 bg-zinc-200 rounded" />
              </div>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
