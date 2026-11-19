#!/usr/bin/env bash
# Start the FastAPI backend (127.0.0.1:8000) and the Next.js standalone server ($PORT).
# If either process exits, exit too so the platform restarts the container.
set -uo pipefail
cd /app

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &

for _ in $(seq 1 120); do
  if curl -fs http://127.0.0.1:8000/api/health >/dev/null; then
    echo "backend ready"
    break
  fi
  sleep 1
done

(cd frontend && exec node server.js) &

wait -n
echo "a server process exited; stopping container" >&2
exit 1
