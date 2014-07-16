#!/bin/bash

cmd="uwsgi"
port=${2:-5000}
projectpath="${PROJ_PATH:-.}"
venvpath="${UWSGI_VIRTUALENV:-$projectpath/venv}"
logdir="${UWSGI_LOG_DIR:-/tmp}"
piddir="${UWSGI_PID_DIR:-/tmp}"
callable="${UWSGI_CALLABLE:-main}"
module="${UWSGI_MODULE:-wsgi}"
processes="${UWSGI_PROCESSES:-8}"   #same as cpu cores. or +1 or +2.
listen="${UWSGI_LISTEN:-100}"      #sysctl -w net.core.somaxconn=5000
timeout="${UWSGI_TIMEOUT:-60}"

logpath="$logdir/flask_log_level_runtime_uwsgi.log.$port"
pidpath="$piddir/flask_log_level_runtime_uwsgi.pid.$port"
statspath="$logdir/flask_log_level_runtime_uwsgi.stats.$port"

isrunning() {
    local pid="$(cat "$pidpath")"
    kill -0 "$pid" > /dev/null 2>&1
    return $?
}

startdaemon() {
    isrunning && { 
        local pid="$(cat "$pidpath")"
        echo "daemon is already started with pid = $pid; stop it first?"
        return 1
    }

    "$cmd" --http-socket "0.0.0.0:$port" \
        --master --processes "$processes" \
        --daemonize "$logpath" \
        --pidfile "$pidpath" \
        --callable "$callable" --virtualenv "$venvpath" \
        --chdir "$projectpath" \
        --http-timeout "$timeout" \
        --listen "$listen" \
        --stats "$statspath" \
        --module "$module" > /dev/null 2>&1
    return $?
}

stopdaemon() {
    "$cmd" --stop "$pidpath" > /dev/null 2>&1
    ret="$?"
    poll_till_stopped
    return $ret
}

reloaddaemon() {
    "$cmd" --reload "$pidpath" > /dev/null 2>&1
    return $?
}

poll_till_stopped() {
    for x in 1 2 3 4 5 6 7 8 9 10
    do
        isrunning || return 0
        sleep $x
    done
    return 1
}

case "$1" in
    start)
        echo "starting... "
        startdaemon
        echo "status: $?"
        ;;
    stop)
        echo "stopping... "
        stopdaemon
        echo "status: $?"
        ;;
    restart)
        echo "restarting... "
        stopdaemon
        startdaemon
        echo "status: $?"
        ;;
    reload)
        echo "reloading... "
        reloaddaemon
        echo "status: $?"
        ;;
    *)
        cat << EOF
Usage: $0 start|stop|reload [port]

Also, you can set various UWSGI_ environment variables.
Some UWSGI_ environment variables are this script specific. 
Others are same as http://uwsgi-docs.readthedocs.org/en/latest/Configuration.html#environment-variables

Example:
    UWSGI_LOG_DIR=/var/log UWSGI_PID_DIR=/var/run UWSGI_UID=flask ./uwsgi.bash start
        logs to /var/log/flask_log_level_runtime_uwsgi.log.9001 
        pid file is /var/run/flask_log_level_runtime_uwsgi.pid.9001
        uwsgi is run as flask user
EOF
        exit 1
        ;;
esac

