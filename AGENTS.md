# Agentes

## Cursor Cloud specific instructions

No hay aplicación web. El trabajo son dos scripts de consola: scraping (TP1) y consultas en MongoDB (TP2).

- Python 3.12. El entorno virtual queda en `.venv` (está en `.gitignore`). Dependencias: `TP1/requirements.txt` y `TP2/requirements.txt`.
- MongoDB 7 sale de `TP2/docker-compose.yml` y escucha en `localhost:27017`. Esta VM no usa systemd: `dockerd` hay que levantarlo a mano (`sudo dockerd --host=unix:///var/run/docker.sock`) y Docker se usa con `sudo`.
- Para ver el TP2: `sudo docker compose -f TP2/docker-compose.yml up -d`, después `.venv/bin/python TP2/importar_mongo.py` y `.venv/bin/python TP2/consulta_mongo.py`. La importación borra y vuelve a cargar la base `tp2_fichajes` (30 equipos, 801 movimientos).
- `TP1/scraping_transfermarkt.py` descarga Transfermarkt en vivo. Desde esta red el sitio responde 202 con cuerpo vacío (`x-amzn-waf-action: challenge`), así que el script no puede regenerar el HTML. El HTML y el JSON ya están en el repo y el parser de `lxml` los reproduce igual.
