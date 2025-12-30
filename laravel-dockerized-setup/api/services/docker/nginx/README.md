# Shared Volume Pattern: FPM Producer → NGINX Consumer

## Overview

A **shared Docker volume** synchronizes the `/var/www/public` folder between PHP-FPM (producer) and NGINX (consumer) containers. This pattern separates application logic from web serving responsibilities.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   myapp-fpm     │ writes  │   app_public     │  reads  │  myapp-nginx    │
│   (Producer)    │────────>│  (Shared Volume) │<────────│   (Consumer)    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                            │                             │
        │                            │                             │
   Generates assets              Persistent                   Serves static
   Runs Laravel                  Docker Volume                files to clients
```

## Configuration

```yaml
services:
  myapp-fpm:
    volumes:
      - app_public:/var/www/public    # Read-write access
      
  myapp-nginx:
    volumes:
      - app_public:/var/www/public:ro  # Read-only access (:ro flag)

volumes:
  app_public:
    driver: local
```

## How It Works

**FPM (Producer)**: Mounts volume with read-write access. Generates assets (compiled CSS/JS, uploads, generated files) and writes to `/var/www/public`.

**Shared Volume**: Named Docker volume persists on the host, acts as a bridge between containers, survives restarts.

**NGINX (Consumer)**: Mounts volume read-only (`:ro`). Serves static files directly and proxies PHP requests to FPM via FastCGI.


## Typical Contents

```
/var/www/public/
├── index.php       # Laravel entry point
├── build/          # Compiled Vite/Mix assets
├── storage/        # User uploads
├── images/         # Static images
└── robots.txt
```

## Key Points

- **Initialization**: Volume populated from FPM's `/var/www/public` on first mount
- **Persistence**: Use `docker-compose down -v` to remove volumes
- **Read-only flag**: Enforces one-way data flow (FPM → NGINX)
- **No sync needed**: Both containers see the same files in real-time
