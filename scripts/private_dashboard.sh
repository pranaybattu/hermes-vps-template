#!/bin/sh
# Run on the VPS: publish only a healthy loopback dashboard to the tailnet.
set -eu

tailscale serve status --json | python3 -c '
import json, sys
config = json.load(sys.stdin)
if any(config.get("AllowFunnel", {}).values()):
    sys.exit("Funnel is enabled; disable public exposure before deploying.")
'

for attempt in $(seq 1 24); do
    code=$(curl --max-time 3 --silent --output /dev/null --write-out '%{http_code}' http://127.0.0.1:9119/ || true)
    case "$code" in
        200|302|303|307)
            tailscale serve --bg --https=443 http://127.0.0.1:9119
            exit 0
            ;;
    esac
    sleep 5
done

echo 'Dashboard did not become healthy; deployment failed.' >&2
exit 1
