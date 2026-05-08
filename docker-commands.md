docker compose --profile embeddings --profile observability down --remove-orphans

docker compose build ui && docker compose up -d ui

docker compose --profile embeddings --profile observability up --build -d  