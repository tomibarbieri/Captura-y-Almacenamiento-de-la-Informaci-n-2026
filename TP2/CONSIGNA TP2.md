# TP2 — Captura y almacenamiento (MongoDB)

## Objetivo

Almacenar en MongoDB el dataset obtenido en el TP1 y realizar una consulta de agregación que incluya filtro (`$match`), agrupación (`$group`) y join (`$lookup` / `$unwind`).

**Dataset utilizado:** `datos_fichajes_primera.json` (fichajes de la Primera División argentina — Torneo Clausura / Transfermarkt).

**Relación 1 → N:** un equipo (1) tiene muchas altas y bajas (N).

---

## 1. Importación de los datos en MongoDB

### 1.1 Elección de modelado: colecciones independientes

La consigna permite guardar la relación 1 a N como **embeddings** o en **colecciones independientes**. En este trabajo se eligió **colecciones independientes**.

| Opción | Descripción | Operador de join |
|--------|-------------|------------------|
| Embeddings | Altas/bajas embebidas dentro del documento del equipo | `$unwind` |
| Colecciones independientes *(elegida)* | Colección `equipos` + colección `movimientos`, unidas por `club_id` | `$lookup` (+ `$unwind`) |

**Por qué independientes:** el join queda claro con `$lookup` y el 1 a N se ve bien en el esquema.

### 1.2 Base y colecciones

- **Base de datos:** `tp2_fichajes`
- **Colección `equipos`** (lado 1)
- **Colección `movimientos`** (lado N)

### 1.3 Colección `equipos`

| Campo | Descripción |
|-------|-------------|
| `club_id` | Identificador del club |
| `equipo` | Nombre del club |
| `edad_promedio_altas` | Edad promedio de las altas |
| `valor_mercado_bajas` | Valor de mercado de las bajas |
| `ingresos` | Ingresos por fichajes |
| `balance_fichajes` | Balance de fichajes del club |

Ejemplo de documento:

```json
{
  "club_id": "209",
  "equipo": "CA River Plate",
  "edad_promedio_altas": "25,3",
  "valor_mercado_bajas": "31,93 mill. €",
  "ingresos": "6,45 mill. €",
  "balance_fichajes": "-47,47 mill. €"
}
```

### 1.4 Colección `movimientos`

| Campo | Descripción |
|-------|-------------|
| `club_id` | Referencia al equipo |
| `equipo` | Nombre del club |
| `tipo` | `"alta"` o `"baja"` |
| `jugador` | Nombre del jugador |
| `edad` | Edad (numérico, para filtrar y promediar) |
| `nacionalidad` | Lista de nacionalidades |
| `posicion` | Posición del jugador |
| `valor_mercado` | Valor de mercado |
| `coste` | Coste del pase |
| `ultimo_club` / `nuevo_club` | Club de origen (alta) o destino (baja) |

Ejemplo de documento (alta):

```json
{
  "club_id": "209",
  "equipo": "CA River Plate",
  "tipo": "alta",
  "jugador": "Thiago Almada",
  "edad": 25,
  "nacionalidad": ["Argentina", "Italia"],
  "posicion": "Mediocentro ofensivo",
  "valor_mercado": "20,00 mill. €",
  "coste": "20,00 mill. €",
  "ultimo_club": "Atlético de Madrid"
}
```

### 1.5 Script de importación

Archivo: `importar_mongo.py`

Flujo:

1. Leer `datos_fichajes_primera.json`
2. Separar cada equipo en un documento de `equipos`
3. Separar cada alta/baja en un documento de `movimientos` (con `club_id` como referencia)
4. Insertar ambas colecciones en MongoDB

---

## 2. Consultas

Archivo: `consulta_mongo.py`

### 2.1 Consulta 1 (principal)

> ¿Cuántas **altas de jugadores de 25 años o más** hubo por equipo y posición, y cuál es la edad promedio de ese grupo? (incluyendo el balance del club obtenido por join)

| Etapa | Uso |
|-------|-----|
| `$match` | Filtra `tipo = "alta"` y `edad >= 25` |
| `$lookup` | Une `movimientos` con `equipos` por `club_id` |
| `$unwind` | Aplana el array `info_equipo` |
| `$group` | Agrupa por equipo + posición; cuenta y promedia edad |
| `$addFields` | Redondea `edad_promedio` a 1 decimal |

```javascript
[
  { "$match": { "tipo": "alta", "edad": { "$gte": 25 } } },
  {
    "$lookup": {
      "from": "equipos",
      "localField": "club_id",
      "foreignField": "club_id",
      "as": "info_equipo"
    }
  },
  { "$unwind": "$info_equipo" },
  {
    "$group": {
      "_id": { "equipo": "$equipo", "posicion": "$posicion" },
      "cantidad_altas": { "$sum": 1 },
      "edad_promedio": { "$avg": "$edad" },
      "balance_equipo": { "$first": "$info_equipo.balance_fichajes" }
    }
  },
  { "$addFields": { "edad_promedio": { "$round": ["$edad_promedio", 1] } } },
  { "$sort": { "cantidad_altas": -1, "edad_promedio": -1 } }
]
```

### 2.2 Consulta 2

> ¿Qué equipos trajeron más jugadores?

| Etapa | Uso |
|-------|-----|
| `$match` | Filtra solo altas |
| `$group` | Agrupa por equipo; cuenta altas y promedia edad |
| `$addFields` | Redondea `edad_promedio` a 1 decimal |

```javascript
[
  { "$match": { "tipo": "alta" } },
  {
    "$group": {
      "_id": "$equipo",
      "cantidad_altas": { "$sum": 1 },
      "edad_promedio": { "$avg": "$edad" }
    }
  },
  { "$addFields": { "edad_promedio": { "$round": ["$edad_promedio", 1] } } },
  { "$sort": { "cantidad_altas": -1 } }
]
```

### 2.3 Consulta 3

> ¿De qué posiciones hubo más bajas?

| Etapa | Uso |
|-------|-----|
| `$match` | Filtra solo bajas |
| `$group` | Agrupa por posición; cuenta bajas y promedia edad |
| `$addFields` | Redondea `edad_promedio` a 1 decimal |

```javascript
[
  { "$match": { "tipo": "baja" } },
  {
    "$group": {
      "_id": "$posicion",
      "cantidad_bajas": { "$sum": 1 },
      "edad_promedio": { "$avg": "$edad" }
    }
  },
  { "$addFields": { "edad_promedio": { "$round": ["$edad_promedio", 1] } } },
  { "$sort": { "cantidad_bajas": -1 } }
]
```

### 2.4 Consulta 4

> ¿Qué equipos incorporaron más extranjeros?

| Etapa | Uso |
|-------|-----|
| `$match` | Filtra altas cuya nacionalidad no incluye Argentina |
| `$lookup` | Une con `equipos` por `club_id` |
| `$unwind` | Aplana el array `info_equipo` |
| `$group` | Agrupa por equipo; cuenta extranjeros |

```javascript
[
  {
    "$match": {
      "tipo": "alta",
      "nacionalidad": { "$nin": ["Argentina"] }
    }
  },
  {
    "$lookup": {
      "from": "equipos",
      "localField": "club_id",
      "foreignField": "club_id",
      "as": "info_equipo"
    }
  },
  { "$unwind": "$info_equipo" },
  {
    "$group": {
      "_id": "$equipo",
      "altas_extranjeros": { "$sum": 1 },
      "ingresos_equipo": { "$first": "$info_equipo.ingresos" }
    }
  },
  { "$sort": { "altas_extranjeros": -1 } }
]
```

### 2.5 Consulta 5

> Por equipo: ¿cuántas altas vs bajas y con qué edad promedio?

| Etapa | Uso |
|-------|-----|
| `$group` | Por equipo cuenta altas/bajas y promedia edad de cada lado |
| `$addFields` | Redondea ambas edades promedio a 1 decimal |

```javascript
[
  {
    "$group": {
      "_id": "$equipo",
      "altas": {
        "$sum": { "$cond": [{ "$eq": ["$tipo", "alta"] }, 1, 0] }
      },
      "bajas": {
        "$sum": { "$cond": [{ "$eq": ["$tipo", "baja"] }, 1, 0] }
      },
      "edad_promedio_altas": {
        "$avg": {
          "$cond": [{ "$eq": ["$tipo", "alta"] }, "$edad", null]
        }
      },
      "edad_promedio_bajas": {
        "$avg": {
          "$cond": [{ "$eq": ["$tipo", "baja"] }, "$edad", null]
        }
      }
    }
  },
  {
    "$addFields": {
      "edad_promedio_altas": { "$round": ["$edad_promedio_altas", 1] },
      "edad_promedio_bajas": { "$round": ["$edad_promedio_bajas", 1] }
    }
  },
  { "$sort": { "altas": -1 } }
]
```

---

## 3. Entorno y ejecución

MongoDB en `mongodb://localhost:27017` (por ejemplo con Docker):

```bash
cd TP2
docker compose up -d

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python importar_mongo.py
python consulta_mongo.py
```

Si no usás Docker, podés tener Mongo instalado en local apuntando al mismo puerto.
