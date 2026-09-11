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

Keep `.env`, the deployment revision, and the `clear-data` volume associated
with the same instance. The volume contains the mint database and privileged
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

Back up the `clear-data` volume together with the protected `.env`, deployment
revision, and local operating policy. Stop Clear while taking a simple volume
backup so the SQLite database and root wallet are captured consistently. Test
the recovery procedure without allowing two active instances to share the same
state or service key.

## Stop and retire

`docker compose stop` or `docker compose down` stops the service without
deleting the named volume. Do not use `docker compose down --volumes` for a
routine stop. Retirement of a mint, its service identity, or its currency
authority is a separate governance decision and should be recorded before
state is destroyed.
