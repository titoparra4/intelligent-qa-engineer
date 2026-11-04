#!/usr/bin/env bash
# Start the local Customers mock, run the Postman collection with Newman,
# then stop the mock. Targets 127.0.0.1 only.
#   Usage: examples/postman/run-local.sh [port]
# Requires: Python 3.9+, Node.js 18+ (Newman is fetched with npx if missing).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8000}"
BASE_URL="http://127.0.0.1:${PORT}"
REPORT_DIR="${REPORT_DIR:-${HERE}/reports}"
NEWMAN_VERSION="${NEWMAN_VERSION:-6}"

python3 "${HERE}/../mock-api/server.py" --port "${PORT}" &
SERVER_PID=$!
trap 'kill "${SERVER_PID}" 2>/dev/null || true' EXIT

# Poll the health endpoint (max ~10 s) instead of sleeping a fixed time.
for _ in $(seq 1 50); do
  if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then break; fi
  sleep 0.2
done
curl -fsS "${BASE_URL}/health" >/dev/null || { echo "mock API did not start on ${BASE_URL}" >&2; exit 1; }

mkdir -p "${REPORT_DIR}"
npx --yes "newman@${NEWMAN_VERSION}" run "${HERE}/customers-api.postman_collection.json" \
  -e "${HERE}/local.postman_environment.json" \
  --env-var "baseUrl=${BASE_URL}" \
  --timeout-request 5000 \
  -r cli,junit --reporter-junit-export "${REPORT_DIR}/newman-junit.xml"
