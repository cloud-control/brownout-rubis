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
DB_DIR=/srv/brownout-rubis/data

cleanup

for tier in db web control; do
    log "Building rubis-$tier-tier ..."
    (cd rubis-$tier-tier; docker build -t rubis-$tier-tier .)
done

log "Starting rubis-db-tier ..."
docker run --detach \
    --name rubis-db-tier-0 \
    --volume $DB_DIR:/var/lib/mysql \
    --cpuset-cpus '0' \
    rubis-db-tier
log "Starting rubis-web-tier ..."
docker run --detach \
    --name rubis-web-tier-0 \
    --link rubis-db-tier-0:mysql \
    --cpuset-cpus '0' \
    rubis-web-tier

# Wait for db-tier to start
while ! docker run --rm --link rubis-db-tier-0:db appropriate/nc -w 1 -q 0 db 3306 > /dev/null; do
    log "Waiting for DB tier to start (this may take 60 seconds) ..."
    sleep 5
done

log "Starting vmtouch-rubis-db-data-0 ..."
docker run --detach -t \
    --name vmtouch-rubis-db-data-0 \
    --cap-add IPC_LOCK \
    --volume $DB_DIR:/data \
    cklein/vmtouch

while ! docker logs vmtouch-rubis-db-data-0 | grep -q LOCKED; do
    log "Waiting for vmtouch to lock DB in-memory ..."
    sleep 1
done

log "Starting rubis-control-tier-0 ..."
docker run --detach \
    --name rubis-control-tier-0 \
    --link rubis-web-tier-0:backend \
    --publish 80:80 \
    rubis-control-tier

log "Starting httpmon ..."

#
# Experiment verbs (see below for usage)
#
function setStart {
	echo [`date +%s`] start
}
function setCount {
	echo [`date +%s`] count=$1
	echo "count=$1" >&9
}
function setOpen {
	echo [`date +%s`] open=$1
	echo "open=$1" >&9
}
function setThinkTime {
	echo [`date +%s`] thinktime=$1
	echo "thinktime=$1" >&9
}
function setConcurrency {
	echo [`date +%s`] concurrency=$1
	echo "concurrency=$1" >&9
}
function setTimeout {
	echo [`date +%s`] timeout=$1
	echo "timeout=$1" >&9
}

#
# Initialization
#

# Create FIFO to communicate with httpmon and start httpmon
rm -f httpmon.fifo
mkfifo httpmon.fifo
docker run --rm -i \
    --name rubis-wg-0 \
    --link rubis-control-tier-0:host \
    cklein/httpmon \
    --url http://host/PHP/RandomItem.php \
    --deterministic \
    --concurrency 0 \
    < httpmon.fifo &> httpmon.log &
exec 9> httpmon.fifo

#
# Initialize experiment
#
setOpen 1
setThinkTime 1
setTimeout 4
setStart

for i in $(seq 1 20); do
    setConcurrency  20
    sleep 60
    setConcurrency  100
    sleep 60
    setConcurrency  30
    sleep 60
    setConcurrency  70
    sleep 60
    setConcurrency  20
    sleep 60
done
setConcurrency  0

docker logs rubis-control-tier-0 2> rubis-control-tier-0.log
