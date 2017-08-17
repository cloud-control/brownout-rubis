#!/bin/bash

#
# Helper functions
#
bold=$(tput bold)
normal=$(tput sgr0)
function log {
    echo ${bold}[`date --iso-8601=ns`] "$*"${normal} >&2
}
function cleanup {
    log "*** Cleanup ***"
    docker rm -f \
        rubis-db-tier-0 \
        vmtouch-rubis-db-data-0 \
        rubis-web-tier-0 \
        rubis-control-tier-0 \
        rubis-wg-0 || true
}

set -e

: ${XDG_CACHE_HOME:=$HOME/.cache}
DB_DIR=$XDG_CACHE_HOME/brownout-rubis/data

cleanup

for tier in db web control; do
    log "Building rubis-$tier-tier ..."
    (cd rubis-$tier-tier; docker build -t rubis-$tier-tier .)
done

log "Starting rubis-db-tier ..."
docker run --detach \
    --name rubis-db-tier-0 \
    --volume $DB_DIR:/var/lib/mysql \
    --cpuset-cpus '0-1' \
    rubis-db-tier
log "Starting rubis-web-tier ..."
docker run --detach \
    --name rubis-web-tier-0 \
    --link rubis-db-tier-0:mysql \
    --publish 8080:80 \
    --cpuset-cpus '0-1' \
    rubis-web-tier

# Wait for db-tier to start
while ! docker run --rm --link rubis-db-tier-0:db appropriate/nc -w 1 -q 0 db 3306 > /dev/null; do
    log "Waiting for DB tier to start (this may take 60 seconds) ..."
    sleep 5
done

log "Starting vmtouch-rubis-db-data-0 ..."
docker run --detach \
    --name vmtouch-rubis-db-data-0 \
    --volume $DB_DIR:/data \
    cklein/vmtouch

log "Starting rubis-control-tier-0 ..."
docker run --detach \
    --name rubis-control-tier-0 \
    --publish 80:80 \
    rubis-control-tier

log "Starting httpmon ..."
docker run --rm -ti \
    --name rubis-wg-0 \
    --link rubis-control-tier-0:host \
    cklein/httpmon \
    --url http://host/PHP/RandomItem.php \
    --open \
    --deterministic \
    --concurrency 100 \
    --thinktime 1 \
| sed -r -e 's/^(time=[0-9.]+).*(latency95=[0-9.]+ms).*(rr=[0-9.]+%).*$/\1\t\2\t\3/p'
