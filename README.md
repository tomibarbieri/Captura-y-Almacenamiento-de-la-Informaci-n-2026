# Captura y almacenamiento

Trabajos prácticos de la materia **Captura y almacenamiento**: scraping de fichajes de la Primera División argentina (Transfermarkt — Torneo Clausura) y consultas en MongoDB.

Relación **1 a N**: un equipo → muchas altas y bajas.

Repo: [tomibarbieri/Captura-y-Almacenamiento-de-la-Informaci-n-2026](https://github.com/tomibarbieri/Captura-y-Almacenamiento-de-la-Informaci-n-2026)

---

## Trabajos prácticos

| TP | Tema | Carpeta |
|----|------|---------|
| **TP1** | Extracción ETL con scraping (XPath) + JSON | [TP1/](TP1/) · [CONSIGNA TP1](TP1/CONSIGNA%20TP1.md) |
| **TP2** | Almacenamiento y consultas en MongoDB | [TP2/](TP2/) · [CONSIGNA TP2](TP2/CONSIGNA%20TP2.md) |

### [TP1 — Scraping](TP1/)

- Fuente: [Torneo Clausura — Fichajes](https://www.transfermarkt.com.ar/torneo-clausura/transfers/wettbewerb/ARGC)
- Técnica: `requests` + XPath (`lxml`)
- Salida: `datos_fichajes_primera.json` (30 equipos con altas, bajas y resúmenes)

Cómo ejecutarlo y detalle de la inspección HTML: **[TP1/CONSIGNA TP1.md](TP1/CONSIGNA%20TP1.md)**

### [TP2 — MongoDB](TP2/)

- Usa el JSON del TP1
- Colecciones independientes: `equipos` + `movimientos`
- Consultas con `$match`, `$group`, `$lookup` y `$unwind`
- Mongo con Docker (`docker-compose.yml`) o local en `localhost:27017`

Modelado, pipelines y cómo ejecutarlo: **[TP2/CONSIGNA TP2.md](TP2/CONSIGNA%20TP2.md)**

Consultas incluidas:

1. Altas de 25+ años por equipo y posición (con join)
2. Ranking de equipos por cantidad de altas
3. Bajas agrupadas por posición
4. Altas de extranjeros por equipo (con join)
5. Altas vs bajas por equipo (con edades promedio)

---

## Flujo del proyecto

```text
Transfermarkt (HTML)
        │
        ▼
   TP1 scraping ──► JSON (equipos + altas/bajas)
        │
        ▼
   TP2 MongoDB ──► colecciones + agregación
```
