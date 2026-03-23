Act as a Senior Product Designer + Frontend Engineer (React + Tailwind).
We use MapLibre GL JS.

GOAL
Premium, modern, sophisticated map UI:
- No overlapping overlays (layers panel vs legend)
- Replace ugly edit button with a vertical expanding FAB (controls -> + -> pencil)
- Unify ALL map controls styling (including MapLibre native controls)

------------------------------------------------------------
1) MAP OVERLAY DOCK SYSTEM (NO OVERLAP)
------------------------------------------------------------
Implement a deterministic overlay layout with dock zones using absolute-positioned HTML overlays on top of the MapLibre canvas.

Create a single overlay root inside the map container:
<MapOverlayRoot class="pointer-events-none absolute inset-0 z-30" />

Inside it, create dock containers (pointer-events enabled):
- Bottom-left: Legend (fixed card)
- Bottom-left-above-legend: Layers panel (fixed card) -> NEVER overlap legend
- Bottom-right: FloatingActionMenu (FAB)
- Top-right: other controls if needed (optional)

Key rule:
- Legend has a known max height (e.g. 170px). If content exceeds, it scrolls internally.
- Layers panel must position using: bottom = (legendHeight + gap).
  - Implement via CSS variable on overlay root: --legend-h: 170px
  - legend: max-h-[var(--legend-h)] overflow-y-auto
  - layersPanel: style bottom: calc(var(--legend-h) + 12px)

Responsive:
- On small screens, legend collapses by default (accordion), and when collapsed set --legend-h to smaller (e.g. 52px).

Acceptance:
- At any viewport size, layers panel never overlaps the legend.

------------------------------------------------------------
2) PREMIUM FAB (VERTICAL EXPAND UPWARDS)
------------------------------------------------------------
Replace current edit widget with a FAB menu component:

Component: <MapFabMenu />

- Main FAB button (48px): icon "controls/sliders"
- On click, open menu items above (vertical):
  - "+" Crear punto
  - "pencil" Editar punto

Interactions:
- Animate open/close with:
  - opacity + translateY + scale
  - duration-200 ease-out
  - optional stagger 60ms between items
- Close on:
  - click outside
  - ESC key
- Tooltips on hover
- Keyboard accessible:
  - tab focus order
  - aria-expanded, aria-controls

Design tokens:
- bg-white/90 backdrop-blur-md
- border border-zinc-200
- shadow-sm
- text-zinc-700
- hover bg-white
- focus ring ring-2 ring-blue-500/30
- rounded-full

Menu items:
- 44px circles, same style
- show small label pill on hover OR tooltip (do not clutter)

Important:
- FAB must sit above all overlays (z-50) but not cover the right-side panel.

------------------------------------------------------------
3) UNIFY MAPLIBRE NATIVE CONTROLS STYLING
------------------------------------------------------------
We use MapLibre built-in controls (zoom, nav, etc.).
They render with classes:
- .maplibregl-ctrl
- .maplibregl-ctrl-group
- .maplibregl-ctrl button

Create global CSS overrides (Tailwind @layer utilities or a CSS module) to match our premium style:

Requirements:
- .maplibregl-ctrl-group:
  - background: rgba(255,255,255,0.85)
  - backdrop-filter: blur(10px)
  - border: 1px solid #e4e4e7 (zinc-200)
  - border-radius: 12px
  - box-shadow: small (shadow-sm equivalent)
  - overflow: hidden
- .maplibregl-ctrl-group button:
  - width/height: 40px
  - background: transparent
  - color: zinc-700
  - hover: background rgba(0,0,0,0.04)
  - focus: outline none + ring

Also ensure no weird borders and separators are subtle.

Place these styles in a single file (e.g. src/styles/maplibre-controls.css) and import once.

------------------------------------------------------------
4) MAP CARDS (LEGEND + LAYERS PANEL) PREMIUM COMPONENTS
------------------------------------------------------------
Create reusable primitives:
- <MapCard title="...">...</MapCard>
- <MapControlButton />

MapCard:
- pointer-events-auto
- bg-white/90 backdrop-blur-md
- border border-zinc-200
- rounded-xl
- shadow-sm
- p-3
- max-w-[280px]
- title: text-sm font-medium text-zinc-900
- body: text-xs text-zinc-600

Ensure both legend and layers panel use MapCard.

------------------------------------------------------------
5) Z-INDEX AND POINTER EVENTS
------------------------------------------------------------
- Map canvas: base
- Map overlays: z-30
- Right inspector panel: z-40
- FAB menu: z-50
- Dropdown menus/tooltips: z-60

Overlay root: pointer-events-none
Individual cards/buttons: pointer-events-auto

------------------------------------------------------------
6) OUTPUT
------------------------------------------------------------
- List modified files
- Explain docking system and CSS var approach
- Confirm native MapLibre controls are restyled
- Provide a short “manual test checklist”:
  - Resize window: no overlaps
  - Open FAB: + and pencil appear above
  - Zoom controls match style
  - Click outside closes menu
  
Visual reference: match the tone of Linear.app / Vercel dashboard (minimal, high whitespace, subtle borders).
Avoid colored panels. Only one accent color for focus states.


