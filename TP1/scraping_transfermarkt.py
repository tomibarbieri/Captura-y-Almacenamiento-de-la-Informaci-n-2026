import json
from pathlib import Path

import requests
from lxml import html


URL = "https://www.transfermarkt.com.ar/torneo-clausura/transfers/wettbewerb/ARGC"
CARPETA = Path(__file__).parent


# Esta función deja prolijo el texto que viene del HTML.
def texto(nodo):
    return " ".join(nodo.text_content().split())


# Le pedimos la página a Transfermarkt con requests.
respuesta = requests.get(
    URL,
    headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "es-AR"},
    timeout=60,
)
respuesta.raise_for_status()


# Guardamos una copia del único HTML que usamos y la preparamos para aplicar XPath.
(CARPETA / "pagina_transfermarkt.html").write_bytes(respuesta.content)
pagina = html.fromstring(respuesta.content)


# Buscamos los bloques que contienen la información de cada equipo.
bloques_equipos = pagina.xpath(
    "//div[contains(@class,'box')]"
    "[.//h2[contains(@class,'content-box-headline--logo')]]"
)
equipos = []


# Recorremos un equipo por vez.
for bloque in bloques_equipos:
    titulo = bloque.xpath(
        ".//h2[contains(@class,'content-box-headline--logo')][1]"
    )[0]
    nombre_equipo = texto(titulo)
    club_id = titulo.get("id", "").replace("to-", "")

    resumenes = bloque.xpath(
        ".//div[contains(@class,'transfer-zusatzinfo-box')]"
    )
    balance = bloque.xpath(".//div[contains(@class,'table-footer')]")

    equipo = {
        "equipo": nombre_equipo,
        "club_id": club_id,
        "edad_promedio_altas": "",
        "valor_mercado_bajas": "",
        "ingresos": "",
        "balance_fichajes": "",
        "altas": [],
        "bajas": [],
    }

    # Sacamos los totales que aparecen debajo de las tablas.
    if len(resumenes) >= 2:
        equipo["edad_promedio_altas"] = texto(
            resumenes[0].xpath(
                ".//span[contains(@class,'transfer-zusatzinfo-alter')]"
            )[0]
        ).replace("Edad promedio de altas:", "").strip()

        equipo["valor_mercado_bajas"] = texto(
            resumenes[1].xpath(
                ".//span[contains(@class,'transfer-zusatzinfo-wert')]"
            )[0]
        ).replace("Valor de mercado de bajas:", "").strip()

        equipo["ingresos"] = texto(
            resumenes[1].xpath(
                ".//span[contains(@class,'transfer-einnahmen-ausgaben')]"
            )[0]
        ).replace("Ingresos:", "").strip()

    if balance:
        equipo["balance_fichajes"] = texto(balance[0]).replace(
            "Balance de fichajes:", ""
        ).strip()

    # Recorremos las dos tablas: la primera es Altas y la segunda es Bajas.
    tablas = bloque.xpath(
        ".//div[contains(@class,'responsive-table')]/table"
    )
    for tabla in tablas:
        encabezado = texto(tabla.xpath(".//th[1]")[0])
        tipo = "altas" if encabezado == "Altas" else "bajas"

        # Recorremos cada jugador de la tabla y tomamos sus columnas.
        for fila in tabla.xpath("./tbody/tr[td]"):
            celdas = fila.xpath("./td")
            if len(celdas) < 9:
                continue

            nombre = celdas[0].xpath(
                ".//span[contains(@class,'hide-for-small')]//a/@title"
            )
            nacionalidades = celdas[2].xpath(".//img/@title")
            club = celdas[7].xpath(".//a/@title")

            movimiento = {
                "jugador": nombre[0] if nombre else texto(celdas[0]),
                "edad": texto(celdas[1]),
                "nacionalidad": nacionalidades,
                "posicion": texto(celdas[3]),
                "valor_mercado": texto(celdas[5]),
                "coste": texto(celdas[8]),
            }

            # El nombre del campo cambia según sea una alta o una baja.
            campo_club = "ultimo_club" if tipo == "altas" else "nuevo_club"
            movimiento[campo_club] = club[0] if club else ""
            equipo[tipo].append(movimiento)

    equipos.append(equipo)
    print(f"{nombre_equipo}: {len(equipo['altas'])} altas y {len(equipo['bajas'])} bajas")


# Juntamos todo y lo guardamos en un JSON fácil de leer.
datos = {
    "fuente": URL,
    "cantidad_equipos": len(equipos),
    "equipos": equipos,
}

with open(CARPETA / "datos_fichajes_primera.json", "w", encoding="utf-8") as archivo:
    json.dump(datos, archivo, ensure_ascii=False, indent=2)

print("\nListo: se creó datos_fichajes_primera.json")
