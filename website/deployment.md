---
title: Standalone Deployment
description: Install, operate, update, back up, and retire a standalone Clear mint.
---

# Standalone deployment

This guide is for an independently operated Clear instance. When Clear is part
of a Mainstay instance, Mainstay owns its configuration, data, start, update,
and recovery lifecycle; operate it from the Mainstay deployment directory.

## Install and configure

Use a dedicated checkout or release directory for each instance. Create the
runtime environment and replace every required placeholder with independently
generated material:

```bash
cp .env.example .env
# Set CLEAR_MASTER_SECRET, CLEAR_OPERATOR_TOKEN, and CLEAR_MINT_SERVICE_NSEC.
docker compose config --quiet
docker compose up --build --detach
```

Keep `.env`, the deployment revision, and the `CLEAR_DATA_DIR` host directory associated
with the same instance. The directory contains the mint database and privileged
root wallet. The configured service key supplies the mint's stable
communication identity; commissioning and treasury authority remain separate
operator actions.

Clear binds to `127.0.0.1` by default. For remote access, select the required
LAN, VPN, or reverse-proxy interface explicitly and protect that path with
appropriate network policy and HTTPS.

## Verify

```bash
docker compose ps
curl --fail http://127.0.0.1:3339/health
docker compose exec clear clear-root info
```

A healthy process is not the same as a commissioned service or enabled
treasury. Verify those states independently before issuing value.

## Update

From the dedicated deployment checkout:

```bash
./refresh-containers.sh
```

The script refuses tracked working-tree changes, performs only a fast-forward
source update, validates Compose, rebuilds and recreates the container, and
waits for Clear's health check. It does not rotate secrets, change
commissioning, or alter treasury policy.

## Back up and recover

Back up the `CLEAR_DATA_DIR` host directory together with the protected `.env`, deployment
revision, and local operating policy. Stop Clear while taking a simple directory
backup so the SQLite database and root wallet are captured consistently. Test
the recovery procedure without allowing two active instances to share the same
state or service key.

## Stop and retire

`docker compose stop` or `docker compose down` stops the service without
deleting the host data directory. Do not use `docker compose down --volumes` for a
routine stop. Retirement of a mint, its service identity, or its currency
authority is a separate governance decision and should be recorded before
state is destroyed.

### Standalone storage selection

Set `CLEAR_DATA_DIR` in your ignored `.env` to the existing mint data directory.
For the Beelink Lexar deployment, use `/mnt/lexar/clear`. Both public and operator
services mount this directory at `/app/data`; a missing setting or directory
fails instead of falling back to a Docker volume. Verify the external drive is
mounted before starting. `create_host_path: false` checks directory existence,
not the identity of the mounted drive.

This change does not migrate data. Existing named-volume deployments must stop
both services, back up their current data and deliberately choose/migrate that
same data before restarting. Never initialize an empty replacement mint or copy
an older database over a newer one. Preserve the matching `.env` secrets. A new
mint needs a pre-created directory writable by image UID/GID 10001.

Keep the tracked Compose file unchanged on the deployment host; the local path
belongs in `.env` so it survives repository refreshes without a storage patch.
