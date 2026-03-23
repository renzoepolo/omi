# Mapeo OVI Urbano Baldio v1

Field | DB column | Backend validator | Frontend component
--- | --- | --- | ---
ID | `observations.id` | N/A (PK) | N/A
TIPO_INMUEBLE | `observation_ovi_urbano_baldio.tipo_inmueble` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `TIPO_INMUEBLE` | `Select` (disabled, fijo 0)
ORIGEN_VALOR | `observation_ovi_urbano_baldio.origen_valor` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `ORIGEN_VALOR` | `Select`
SUPERFICIE | `observation_ovi_urbano_baldio.superficie` | Pydantic type `int` + `Field(ge=0)` | `Input` number
UNI_SUP | `observation_ovi_urbano_baldio.uni_sup` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `UNI_SUP` | `Select` (disabled, fijo 0)
MONEDA | `observation_ovi_urbano_baldio.moneda` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `MONEDA` | `Select`
VALOR_TOTAL | `observation_ovi_urbano_baldio.valor_total` | Pydantic type `Decimal` + `Field(ge=0)` | `Input` number
NOMENCLATURA | `observation_ovi_urbano_baldio.nomenclatura` | Pydantic type `str` + `Field(min_length=1,max_length=255)` | `Input` text
AFECTACION | `observation_ovi_urbano_baldio.afectacion` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `AFECTACION` | `Select`
FRENTE | `observation_ovi_urbano_baldio.frente` | Pydantic type `int` | `Input` number
FORMA | `observation_ovi_urbano_baldio.forma` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `FORMA` | `Select`
UBIC_CUADRA | `observation_ovi_urbano_baldio.ubic_cuadra` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `UBIC_CUADRA` | `Select`
TIPO_BARRIO | `observation_ovi_urbano_baldio.tipo_barrio` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `TIPO_BARRIO` | `Select`
SIT_JURIDICA | `observation_ovi_urbano_baldio.sit_juridica` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `SIT_JURIDICA` | `Select`
FECHA_VALOR | `observation_ovi_urbano_baldio.fecha_valor` | Pydantic type `date` | `Input` date
PROCEDENCIA | `observation_ovi_urbano_baldio.procedencia` | `OviUrbanoBaldioPayload.validate_business_rules` + shared enum `PROCEDENCIA` | `Select`
TELEFONO | `observation_ovi_urbano_baldio.telefono` | Pydantic type `str | None` | `Input` text
FOTO_FACHADA | `observation_ovi_urbano_baldio.foto_fachada` | Condicional en `validate_business_rules` (solo PROCEDENCIA=0) | `Input` text condicional
FOTO_CARTEL | `observation_ovi_urbano_baldio.foto_cartel` | Condicional en `validate_business_rules` (solo PROCEDENCIA=0) | `Input` text condicional
LINK | `observation_ovi_urbano_baldio.link` | Condicional en `validate_business_rules` (solo PROCEDENCIA=1) | `Input` text condicional

## Definicion compartida de enums

- `shared/ovi_enums.json`
- Backend usa `app/core/ovi_enums.py`
- Frontend usa import directo JSON en `src/components/RightPanel.jsx`
