# Deployment Guide

Production deployment and verification documentation for the Real-Time AI Chat Platform.

## Render Deployment

The current live deployment uses Render:

| Service | Render type | Name | URL |
|---|---|---|---|
| Backend | Web Service / Docker | `rda-backend` | [Backend API](https://rda-backend-62d0.onrender.com) |
| Frontend | Static Site | `rda-frontend` | [Live Application](https://rda-frontend-zmln.onrender.com) |
| Database | PostgreSQL | `rda-postgres` | Internal Render database URL |
| Redis | Key Value / Redis | `rda-redis` | Internal Render Redis URL |

### Backend Render Service

The backend is deployed as a Docker Web Service using:

- Dockerfile: `backend/Dockerfile`
- Entrypoint: `backend/entrypoint.sh`
- Runtime command handled by the entrypoint:
  - Runs migrations with `python manage.py migrate --noinput`
  - Starts Daphne with `daphne -b 0.0.0.0 -p "${PORT:-8000}" config.asgi:application`

Required backend environment variables:

```env
DJANGO_ENV=production
DEBUG=False
SECRET_KEY=<render-secret-key>
ALLOWED_HOSTS=rda-backend-62d0.onrender.com
CORS_ALLOWED_ORIGINS=https://rda-frontend-zmln.onrender.com
DATABASE_URL=<render-postgres-url>
REDIS_URL=<render-redis-url>
```

AI integration:

```env
OPENAI_API_KEY=<openai-api-key>
```
`OPENAI_API_KEY` is required for `/ai` responses, but the Django service can start without it.

Do not commit production secrets to Git.

### Frontend Render Static Site

The frontend is deployed as a Render Static Site from the `frontend/` app.

If the Render root directory is set to `frontend`, use:

```bash
npm ci
npm run build
```

Publish directory:

```text
dist
```

Frontend environment variables:

```env
VITE_API_BASE_URL=https://rda-backend-62d0.onrender.com
VITE_WS_BASE_URL=wss://rda-backend-62d0.onrender.com
```

### Vercel Alternative

For Vercel, set the project root directory to `frontend`.

Required environment variables:

```env
VITE_API_BASE_URL=https://<render-backend-host>
VITE_WS_BASE_URL=wss://<render-backend-host>
```

`frontend/vercel.json` rewrites application routes so React Router routes are served by the SPA entry point.

### Post-Deploy Verification

Backend health check:

```bash
curl https://rda-backend-62d0.onrender.com/api/health/
```

Expected response:

```json
{"status":"ok"}
```

Frontend verification:

1. Open `https://rda-frontend-zmln.onrender.com`.
2. Register a test user.
3. Log in.
4. Open Dashboard.
5. Open Items and create an item.
6. Open Chat and confirm the WebSocket connects.
7. Send an `/ai` message and confirm an AI response.
8. Test dark/light mode.
9. Test the notification dropdown.
10. Verify responsive behavior on mobile.

### Local DNS/VPN Troubleshooting

If a local browser or `curl` cannot reach Render while the application works from another network, check VPN, Tailscale exit-node, and DNS settings.

A local networking issue does not necessarily mean the Render service is unavailable.
