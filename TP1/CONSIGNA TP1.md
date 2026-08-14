# TP1 — Captura y almacenamiento (Extracción ETL con scraping)

## Objetivo

Emular la etapa de **Extracción** del proceso ETL usando scraping como técnica de obtención de datos.

---

## 1. Página elegida y relación uno a muchos

**Sitio:** [Transfermarkt](https://www.transfermarkt.com.ar)  
**Página:** [Torneo Clausura — Fichajes](https://www.transfermarkt.com.ar/torneo-clausura/transfers/wettbewerb/ARGC)

> Uso exclusivamente **educativo** (TP universitario). Se descarga una sola pantalla pública de la competencia, con User-Agent identificable y sin abusos de frecuencia.

### Relación 1 → N

| Nivel | Entidad | Descripción |
|--------|---------|-------------|
| Principal (1) | **Equipo** de Primera División | Al menos 10 clubes (≥ 4 atributos) |
| Secundaria (N) | **Movimientos de pase** (altas / bajas) | Entre 2 y 5+ por equipo (≥ 3 atributos, varios numéricos) |

**Tabla principal — Equipo (≥ 4 atributos):**

1. `equipo` (nombre)
2. `club_id` (identificador Transfermarkt)
3. `edad_promedio_altas`
4. `valor_mercado_bajas`
5. `ingresos`
6. `balance_fichajes`

**Tabla secundaria — Alta / Baja (≥ 3 atributos, con numéricos):**

1. `jugador`
2. `edad` *(numérico)*
3. `nacionalidad`
4. `posicion`
5. `valor_mercado` *(monetario / numérico textual)*
6. `ultimo_club` (en altas) / `nuevo_club` (en bajas)
7. `coste` *(monetario / numérico textual)*

---

## 2. Inspección del HTML (tags, ids y clases)

La página concentra **los 30 equipos** del Torneo Clausura. Cada club es un bloque `div.box` con un título anclado por **id**.

### 2.1 Contenedor de cada equipo

| Elemento | Selector / atributo | Rol |
|----------|---------------------|-----|
| Título del club | `h2.content-box-headline--logo` | Nombre del equipo |
| Ancla estable | `id="to-{club_id}"` (ej. `id="to-209"` River) | Identifica al club sin depender solo del texto |
| Link del club | `a[href*="/transfers/verein/{id}"]` | Enlace propio del equipo |
| Contenedor | `div.box` que envuelve el `h2` | Agrupa altas, bajas y resúmenes |

**XPath de equipos:**

```xpath
//div[contains(@class,'box')][.//h2[contains(@class,'content-box-headline--logo')]]
```

**XPath del id del club:**

```xpath
.//h2[contains(@class,'content-box-headline--logo')]/@id
```

Ejemplo real: `id="to-209"` → club_id `209` (CA River Plate).

### 2.2 Tablas de altas y bajas

Las tablas **no usan `id` propio** ni `name` en el `<table>`; Transfermarkt las identifica por:

1. El encabezado de la primera columna (`Altas` / `Bajas`)
2. Clases CSS muy estables en cada `<td>`

Estructura de columnas (inspección real):

| # | Columna visible | Clase / ubicación HTML | Dato |
|---|-----------------|------------------------|------|
| 0 | Altas / Bajas (jugador) | `td` → `span.hide-for-small a[@title]` | Nombre completo |
| 1 | Edad | `td.alter-transfer-cell` | Edad |
| 2 | Nac. | `td.nat-transfer-cell` → `img[@title]` | Nacionalidad(es) |
| 3 | Posición | `td.pos-transfer-cell` | Posición larga |
| 4 | Pos | `td.kurzpos-transfer-cell` | Abreviatura |
| 5 | Valor de mercado | `td.mw-transfer-cell` | Valor € |
| 6–7 | Último club / Nuevo club | `td.no-border-rechts` (escudo) + `td.verein-flagge-transfer-cell a[@title]` | Club relacionado |
| 8 | Coste | último `td.rechts` | Coste del pase |

**XPath tablas:**

```xpath
.//div[contains(@class,'responsive-table')]//table
```

**XPath filas de jugadores:**

```xpath
./tbody/tr[td]
```

**XPaths por dato (relativos a la fila):**

```xpath
./td[1]//span[contains(@class,'hide-for-small')]//a/@title   # jugador
./td[contains(@class,'alter-transfer-cell')]                 # edad
./td[contains(@class,'nat-transfer-cell')]//img/@title       # nacionalidad
./td[contains(@class,'pos-transfer-cell')]                   # posición
./td[contains(@class,'mw-transfer-cell')]                    # valor de mercado
./td[contains(@class,'verein-flagge-transfer-cell')]//a/@title  # club
./td[last()]                                                 # coste
```

> Nota: en **bajas** el encabezado de club es **“Nuevo club”** (no “Último club”). En el JSON se guarda como `nuevo_club`.

### 2.3 Resúmenes por equipo (edad promedio, ingresos, balance)

| Dato pedido | Elemento HTML | Clase |
|-------------|---------------|--------|
| Edad promedio de altas | `span` dentro del 1.º resumen | `transfer-zusatzinfo-alter` |
| Valor de mercado de bajas | `span` dentro del 2.º resumen | `transfer-zusatzinfo-wert` |
| Ingresos | `span` dentro del 2.º resumen | `transfer-einnahmen-ausgaben` + texto `Ingresos:` |
| Balance de fichajes | `div` al pie del bloque | `table-footer` |

Contenedor de resúmenes:

```html
<div class="transfer-zusatzinfo-box">
  <span class="transfer-zusatzinfo-alter">Edad promedio de altas: …</span>
  <span class="transfer-zusatzinfo-wert">Valor de mercado …</span>
  <span class="transfer-einnahmen-ausgaben …">Ingresos:/Gastos: …</span>
</div>
```

**XPath:**

```xpath
.//div[contains(@class,'transfer-zusatzinfo-box')]
.//div[contains(@class,'table-footer')]
```

Hay **dos** `transfer-zusatzinfo-box` por club: el primero debajo de Altas (edad altas, valor altas, gastos) y el segundo debajo de Bajas (edad bajas, valor bajas, ingresos).

---

## 3. Técnica de scraping: XPath

Se eligió **XPath** con la librería `lxml` (alternativa permitida junto a BeautifulSoup).

Archivo principal: `scraping_transfermarkt.py`

Flujo:

1. Descargar con `requests` el único HTML usado en el trabajo  
2. Guardarlo como `pagina_transfermarkt.html`  
3. Localizar con XPath los 30 `div.box` de equipos  
4. Recorrer las tablas de altas y bajas  
5. Guardar el resultado en JSON  

---

## 4. Almacenamiento

Formato elegido: **JSON** → `datos_fichajes_primera.json`

Estructura resumida:

```json
{
  "fuente": "https://www.transfermarkt.com.ar/torneo-clausura/transfers/wettbewerb/ARGC",
  "cantidad_equipos": 30,
  "equipos": [
    {
      "equipo": "CA River Plate",
      "club_id": "209",
      "edad_promedio_altas": "25,3",
      "valor_mercado_bajas": "31,93 mill. €",
      "ingresos": "6,45 mill. €",
      "balance_fichajes": "-47,47 mill. €",
      "altas": [ { "jugador": "...", "edad": "...", "nacionalidad": [], "posicion": "...", "valor_mercado": "...", "ultimo_club": "...", "coste": "..." } ],
      "bajas": [ { "jugador": "...", "edad": "...", "nacionalidad": [], "posicion": "...", "valor_mercado": "...", "nuevo_club": "...", "coste": "..." } ]
    }
  ]
}
```

---

## Cómo ejecutar

```bash
cd TP1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scraping_transfermarkt.py
```

El script genera o actualiza:

- `pagina_transfermarkt.html`: copia del HTML analizado
- `datos_fichajes_primera.json`: datos extraídos
