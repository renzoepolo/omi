# OVI – Requerimiento Funcional y Técnico
Versión: v1
Alcance: Campos Núcleo + Flujo Urbano Baldío

Este documento define los campos núcleo y reglas básicas para la carga de una observación tipo "Urbano Baldío".

Codex debe considerar este documento como fuente de verdad.
No debe inventar campos.
No debe eliminar campos.
Debe respetar exactamente los nombres de campo indicados.

---

# 1. Definición de Alcance

Esta versión contempla:

- Solo campos marcados como Tipo = "Nucleo"
- Implementación completa para TIPO_INMUEBLE = 0 (Urbano Baldío)
- Agrupamiento de campos según columna "Grupo"
- Habilitación condicional según columna "Condicion"

Otros tipos de inmueble se definirán en versiones posteriores.

---

# 2. Campos Núcleo Incluidos

A continuación se listan los campos núcleo detectados en el diccionario.

## 2.1 Grupo: Info del mercado

| Campo | Tipo Dato | Obligatorio | Observaciones |
|--------|-----------|------------|---------------|
| ID | integer | SI | Primary key |
| TIPO_INMUEBLE | integer | SI | 0=Urbano Baldío |
| ORIGEN_VALOR | integer | SI | Según valores posibles |
| SUPERFICIE | integer | SI | Superficie terreno |
| UNI_SUP | integer | SI | 0=Metros |
| MONEDA | integer | SI | 0=Pesos, 1=Dólares |
| VALOR_TOTAL | decimal | SI | Valor total de mercado |

---

## 2.2 Grupo: Info del inmueble

| Campo | Tipo Dato | Obligatorio |
|--------|-----------|------------|
| NOMENCLATURA | varchar | SI |
| AFECTACION | integer | SI |
| FRENTE | integer | SI |
| FORMA | integer | SI |
| UBIC_CUADRA | integer | SI |
| TIPO_BARRIO | integer | SI |
| SIT_JURIDICA | integer | SI |
| FECHA_VALOR | date | SI |

---

## 2.3 Grupo: Procedencia

| Campo | Tipo Dato | Obligatorio | Condición |
|--------|-----------|------------|-----------|
| PROCEDENCIA | integer | SI | — |
| TELEFONO | varchar | OPCIONAL | — |
| FOTO_FACHADA | varchar | CONDICIONAL | PROCEDENCIA = 0 |
| FOTO_CARTEL | varchar | CONDICIONAL | PROCEDENCIA = 0 |
| LINK | varchar | CONDICIONAL | PROCEDENCIA = 1 |

---

# 3. Reglas de Agrupamiento en Frontend

El formulario debe organizarse por secciones visuales según columna "Grupo":

- Sección 1: Info del mercado
- Sección 2: Info del inmueble
- Sección 3: Procedencia

Cada grupo debe presentarse en un bloque visual independiente.

---

# 4. Reglas Condicionales (Columna "Condicion")

Las condiciones deben implementarse tanto en frontend como en backend.

## 4.1 FOTO_FACHADA y FOTO_CARTEL

- Solo deben habilitarse cuando:
  PROCEDENCIA = 0 (Relevamiento de Campo)

- Si no aplica:
  - Deben ocultarse en frontend
  - Deben enviarse como NULL en backend

## 4.2 LINK

- Solo debe habilitarse cuando:
  PROCEDENCIA = 1 (Sitio Web)

- Si no aplica:
  - Debe ocultarse
  - Debe enviarse como NULL

---

# 5. Reglas Específicas para Urbano Baldío

En esta versión solo se implementa:

TIPO_INMUEBLE = 0

Reglas:

- UNI_SUP debe ser 0 (Metros cuadrados)
- No existen superficies edificadas ni rurales
- Todos los campos definidos arriba son obligatorios salvo los marcados como opcionales o condicionales

---

# 6. Reglas de Base de Datos

Codex debe:

1. Crear o ajustar migraciones según tipos definidos.
2. Respetar tipos:
   - integer
   - decimal
   - varchar
   - date
3. Permitir NULL solo en campos condicionales.
4. No eliminar columnas existentes sin migración explícita.

---

# 7. Validación Backend Obligatoria

Debe implementarse:

- Validación por tipo de dato
- Validación de campos obligatorios
- Validación condicional por PROCEDENCIA
- Rechazo de campos condicionales con valor cuando no aplica

---

# 8. Reglas de Frontend

1. Formularios organizados por Grupo.
2. Campos condicionales deben:
   - Aparecer dinámicamente
   - Limpiarse cuando se ocultan
3. No permitir envío si faltan campos obligatorios.

---

# 9. Tabla de Mapeo Obligatoria

Antes de implementar, Codex debe generar:

Campo Diccionario → Columna DB → Campo Modelo → Input Formulario

Si detecta inconsistencias, debe detenerse y reportarlas.

---

# 10. Cláusula de Control

Este documento define el alcance actual.
No deben implementarse otros tipos de inmueble en esta versión.
No deben agregarse campos no listados.

