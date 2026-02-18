# Configuración de producción

Este repositorio incluye una base de hardening para despliegues productivos.

## 1) Nginx reverse proxy con HTTPS
- Archivo: `deploy/nginx/nginx.conf`
- Redirección HTTP→HTTPS y terminación TLS en `:443`.
- Encabezados de seguridad (HSTS, X-Frame-Options, etc.).

## 2) Variables de entorno seguras
- Plantilla: `.env.production.example`
- Incluye secretos, CORS allowlist, logging y healthcheck paths.
- Recomendado: inyectar secretos desde un vault (no commitear `.env.production`).

## 3) Configuración CORS
- Allowlist por origen con `map` en Nginx.
- Soporte de preflight (`OPTIONS`) y headers mínimos necesarios.

## 4) Rate limiting básico
- `limit_req_zone` por IP con `10r/s` y `burst=20`.
- Ajustar según tráfico esperado.

## 5) Logs estructurados
- `log_format` en JSON (`json_combined`) para ingestión en ELK/Loki/Datadog.

## 6) Healthcheck endpoints
- `/healthz` (Nginx) para liveness del proxy.
- `/readyz` (Nginx → backend `/health/ready`) para readiness end-to-end.
- Healthchecks Docker para `app` y `nginx` en `deploy/docker-compose.production.yml`.

## Pasos sugeridos
1. Copiar `.env.production.example` → `.env.production` y completar secretos reales.
2. Reemplazar `server_name` y dominios permitidos de CORS.
3. Verificar certificados en `/etc/letsencrypt/live/<dominio>/`.
4. Levantar con: `docker compose -f deploy/docker-compose.production.yml up -d`.
5. Probar:
   - `curl -I http://api.example.com` (debe redirigir a HTTPS)
   - `curl -k https://api.example.com/healthz`
   - `curl -k https://api.example.com/readyz`
