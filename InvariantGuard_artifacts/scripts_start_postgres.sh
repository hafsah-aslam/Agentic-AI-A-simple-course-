#!/usr/bin/env bash
# Start a throw-away PostgreSQL 16 cluster on port 5433 (socket in /tmp) for the experiments.
set -euo pipefail
PGBIN=${PGBIN:-/usr/lib/postgresql/16/bin}
DATA=${1:-$HOME/ig_pgdata}
[ -d "$DATA" ] || "$PGBIN/initdb" -D "$DATA" -A trust -U postgres >/dev/null
"$PGBIN/pg_ctl" -D "$DATA" -o "-p 5433 -k /tmp -c max_connections=200" -l "$DATA/log" start
