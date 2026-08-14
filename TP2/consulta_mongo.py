from pymongo import MongoClient


# Misma conexión que usamos al importar.
URI = "mongodb://localhost:27017"
cliente = MongoClient(URI)
db = cliente["tp2_fichajes"]


# Aplana el _id si viene como dict (ej. equipo + posición).
def aplanar(fila):
    salida = {}
    _id = fila.get("_id")
    if isinstance(_id, dict):
        salida.update(_id)
    else:
        salida["nombre"] = _id
    for clave, valor in fila.items():
        if clave == "_id":
            continue
        salida[clave] = "" if valor is None else valor
    return salida


# Arma una tablita alineada para que se lea bien en consola.
def imprimir_tabla(filas, columnas):
    if not filas:
        print("  (sin resultados)")
        return

    anchos = {}
    for col, titulo in columnas:
        largo = len(titulo)
        for fila in filas:
            largo = max(largo, len(str(fila.get(col, ""))))
        anchos[col] = min(largo, 36)

    encabezado = " | ".join(
        titulo.ljust(anchos[col]) for col, titulo in columnas
    )
    separador = "-+-".join("-" * anchos[col] for col, _ in columnas)

    print(encabezado)
    print(separador)
    for fila in filas:
        print(
            " | ".join(
                str(fila.get(col, ""))[: anchos[col]].ljust(anchos[col])
                for col, _ in columnas
            )
        )


# Corre la consulta y la muestra linda.
def mostrar(titulo, pipeline, columnas, limite=15):
    print("\n" + "=" * 78)
    print(titulo)
    print("=" * 78)

    resultados = list(db.movimientos.aggregate(pipeline))
    filas = [aplanar(r) for r in resultados[:limite]]
    imprimir_tabla(filas, columnas)

    if len(resultados) > limite:
        print(f"\nMostrando {limite} de {len(resultados)} resultados")
    else:
        print(f"\nTotal: {len(resultados)} resultados")


# ---------- Consulta 1 (principal del TP) ----------
# Altas de 25+ años, por equipo y posición, con join al club.
consulta_1 = [
    {"$match": {"tipo": "alta", "edad": {"$gte": 25}}},
    {
        "$lookup": {
            "from": "equipos",
            "localField": "club_id",
            "foreignField": "club_id",
            "as": "info_equipo",
        }
    },
    {"$unwind": "$info_equipo"},
    {
        "$group": {
            "_id": {"equipo": "$equipo", "posicion": "$posicion"},
            "cantidad_altas": {"$sum": 1},
            "edad_promedio": {"$avg": "$edad"},
            "balance_equipo": {"$first": "$info_equipo.balance_fichajes"},
        }
    },
    # Dejamos la edad promedio con un solo decimal.
    {"$addFields": {"edad_promedio": {"$round": ["$edad_promedio", 1]}}},
    {"$sort": {"cantidad_altas": -1, "edad_promedio": -1}},
]


# ---------- Consulta 2 ----------
# Ranking de equipos según cantidad de altas.
consulta_2 = [
    {"$match": {"tipo": "alta"}},
    {
        "$group": {
            "_id": "$equipo",
            "cantidad_altas": {"$sum": 1},
            "edad_promedio": {"$avg": "$edad"},
        }
    },
    {"$addFields": {"edad_promedio": {"$round": ["$edad_promedio", 1]}}},
    {"$sort": {"cantidad_altas": -1}},
]


# ---------- Consulta 3 ----------
# Bajas por posición (qué puestos salieron más).
consulta_3 = [
    {"$match": {"tipo": "baja"}},
    {
        "$group": {
            "_id": "$posicion",
            "cantidad_bajas": {"$sum": 1},
            "edad_promedio": {"$avg": "$edad"},
        }
    },
    {"$addFields": {"edad_promedio": {"$round": ["$edad_promedio", 1]}}},
    {"$sort": {"cantidad_bajas": -1}},
]


# ---------- Consulta 4 ----------
# Altas de jugadores no argentinos, por equipo (con join).
consulta_4 = [
    {
        "$match": {
            "tipo": "alta",
            "nacionalidad": {"$nin": ["Argentina"]},
        }
    },
    {
        "$lookup": {
            "from": "equipos",
            "localField": "club_id",
            "foreignField": "club_id",
            "as": "info_equipo",
        }
    },
    {"$unwind": "$info_equipo"},
    {
        "$group": {
            "_id": "$equipo",
            "altas_extranjeros": {"$sum": 1},
            "ingresos_equipo": {"$first": "$info_equipo.ingresos"},
        }
    },
    {"$sort": {"altas_extranjeros": -1}},
]


# ---------- Consulta 5 ----------
# Por equipo: cuántas altas y bajas, y edad promedio de cada lado.
consulta_5 = [
    {
        "$group": {
            "_id": "$equipo",
            "altas": {
                "$sum": {"$cond": [{"$eq": ["$tipo", "alta"]}, 1, 0]}
            },
            "bajas": {
                "$sum": {"$cond": [{"$eq": ["$tipo", "baja"]}, 1, 0]}
            },
            "edad_promedio_altas": {
                "$avg": {
                    "$cond": [{"$eq": ["$tipo", "alta"]}, "$edad", None]
                }
            },
            "edad_promedio_bajas": {
                "$avg": {
                    "$cond": [{"$eq": ["$tipo", "baja"]}, "$edad", None]
                }
            },
        }
    },
    {
        "$addFields": {
            "edad_promedio_altas": {"$round": ["$edad_promedio_altas", 1]},
            "edad_promedio_bajas": {"$round": ["$edad_promedio_bajas", 1]},
        }
    },
    {"$sort": {"altas": -1}},
]


mostrar(
    "1) Altas de 25+ años, por equipo y posición (con join al club)",
    consulta_1,
    [
        ("equipo", "Equipo"),
        ("posicion", "Posición"),
        ("cantidad_altas", "Altas"),
        ("edad_promedio", "Edad prom."),
        ("balance_equipo", "Balance"),
    ],
)
mostrar(
    "2) Ranking de equipos por cantidad de altas",
    consulta_2,
    [
        ("nombre", "Equipo"),
        ("cantidad_altas", "Altas"),
        ("edad_promedio", "Edad prom."),
    ],
)
mostrar(
    "3) Bajas agrupadas por posición",
    consulta_3,
    [
        ("nombre", "Posición"),
        ("cantidad_bajas", "Bajas"),
        ("edad_promedio", "Edad prom."),
    ],
)
mostrar(
    "4) Altas de extranjeros por equipo (con join)",
    consulta_4,
    [
        ("nombre", "Equipo"),
        ("altas_extranjeros", "Extranjeros"),
        ("ingresos_equipo", "Ingresos"),
    ],
)
mostrar(
    "5) Altas vs bajas por equipo (con edades promedio)",
    consulta_5,
    [
        ("nombre", "Equipo"),
        ("altas", "Altas"),
        ("bajas", "Bajas"),
        ("edad_promedio_altas", "Edad altas"),
        ("edad_promedio_bajas", "Edad bajas"),
    ],
)
