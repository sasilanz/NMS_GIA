FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py exporter.py init_db.py hotg_import.py i18n.py translations_en.py galaxien_quelle_a.csv hotg_hubs.csv ./
COPY templates ./templates

# Datenbank und Sicherungen liegen im Volume /data (bleiben beim Neubauen des Images erhalten)
ENV NMS_DB=/data/nms.db \
    NMS_EXPORT_DIR=/data/export \
    NMS_HOST=0.0.0.0 \
    NMS_PORT=5050
VOLUME /data
EXPOSE 5050

CMD ["python", "app.py"]
