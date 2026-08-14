import json
from pathlib import Path

from pymongo import MongoClient


# Apuntamos a Mongo local (Docker en el puerto 27017).
URI = "mongodb://localhost:27017"
CARPETA = Path(__file__).parent


# Convertimos edad a número para poder filtrar y promediar después.
def edad_a_numero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


# Abrimos el JSON del TP1.
with open(CARPETA / "datos_fichajes_primera.json", encoding="utf-8") as archivo:
    datos = json.load(archivo)


# Nos conectamos a la base y limpiamos colecciones viejas para reimportar limpio.
cliente = MongoClient(URI)
db = cliente["tp2_fichajes"]
db.equipos.drop()
db.movimientos.drop()


equipos = []
movimientos = []

# Separamos el 1 a N: un doc por equipo y muchos docs de altas/bajas.
for item in datos["equipos"]:
    equipos.append(
        {
            "club_id": item["club_id"],
            "equipo": item["equipo"],
            "edad_promedio_altas": item.get("edad_promedio_altas", ""),
            "valor_mercado_bajas": item.get("valor_mercado_bajas", ""),
            "ingresos": item.get("ingresos", ""),
            "balance_fichajes": item.get("balance_fichajes", ""),
        }
    )

    for alta in item.get("altas", []):
        movimientos.append(
            {
                "club_id": item["club_id"],
                "equipo": item["equipo"],
                "tipo": "alta",
                "jugador": alta.get("jugador", ""),
                "edad": edad_a_numero(alta.get("edad")),
                "nacionalidad": alta.get("nacionalidad", []),
                "posicion": alta.get("posicion", ""),
                "valor_mercado": alta.get("valor_mercado", ""),
                "coste": alta.get("coste", ""),
                "ultimo_club": alta.get("ultimo_club", ""),
            }
        )

    for baja in item.get("bajas", []):
        movimientos.append(
            {
                "club_id": item["club_id"],
                "equipo": item["equipo"],
                "tipo": "baja",
                "jugador": baja.get("jugador", ""),
                "edad": edad_a_numero(baja.get("edad")),
                "nacionalidad": baja.get("nacionalidad", []),
                "posicion": baja.get("posicion", ""),
                "valor_mercado": baja.get("valor_mercado", ""),
                "coste": baja.get("coste", ""),
                "nuevo_club": baja.get("nuevo_club", ""),
            }
        )


# Guardamos todo en Mongo.
db.equipos.insert_many(equipos)
db.movimientos.insert_many(movimientos)

print(f"Equipos cargados: {db.equipos.count_documents({})}")
print(f"Movimientos cargados: {db.movimientos.count_documents({})}")
print("Listo: datos importados en la base tp2_fichajes")
