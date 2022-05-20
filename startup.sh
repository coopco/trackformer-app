#!/bin/bash
redis-server &

rq worker &

python app.py &

wait -n

exit $?
