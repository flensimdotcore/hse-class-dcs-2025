# hse-class-dcs-2025

## Health check

### Web server
```
curl -X GET http://localhost:6000/health
```

### App server
```
curl -X GET http://localhost:8000/health
```

## Post new number
```
curl -X POST http://localhost:6000/process -H "Content-Type: application/json" -d '{"number": 5}'
```

## Get all numbers (debug)

### From web server
```
curl -X GET http://localhost:6000/numbers
```

### Directly from app server
```
curl -X GET http://localhost:8000/numbers
```

## Start app

Go to `src/` dir
```
cd src
```

Create .env file with following variables (look at `src/.env.example` file)
```
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
```

```
docker compose up -d --build
```

## Stop app

```
docker compose down --rmi all --volumes --remove-orphans
```
