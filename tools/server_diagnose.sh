#!/usr/bin/env bash
# Server diagnosis helper
# Usage: ./server_diagnose.sh -p PORT [-s "start command"] [-l /path/to/log] [-n service_name] [-c cwd] [-t tail_lines]

PORT=""
START_CMD=""
LOG_PATH=""
SERVICE=""
CWD="."
TAIL_LINES=200

print_usage(){
  echo "Usage: $0 -p PORT [-s \"start command\"] [-l /path/to/log] [-n service_name] [-c cwd] [-t tail_lines]"
  exit 1
}

while getopts "p:s:l:n:c:t:h" opt; do
  case $opt in
    p) PORT="$OPTARG" ;;
    s) START_CMD="$OPTARG" ;;
    l) LOG_PATH="$OPTARG" ;;
    n) SERVICE="$OPTARG" ;;
    c) CWD="$OPTARG" ;;
    t) TAIL_LINES="$OPTARG" ;;
    h|*) print_usage ;;
  esac
done

if [ -z "$PORT" ]; then
  echo "Error: PORT required."
  print_usage
fi

echo "Diagnosing server for port: $PORT"
echo "Working dir: $CWD"
echo

# Check which tool is available for port check
port_check_cmd=""
if command -v ss >/dev/null 2>&1; then
  port_check_cmd="ss -ltnp"
elif command -v lsof >/dev/null 2>&1; then
  port_check_cmd="lsof -i :$PORT -P -n"
elif command -v netstat >/dev/null 2>&1; then
  port_check_cmd="netstat -ltnp 2>/dev/null"
else
  echo "No ss/lsof/netstat found. Skipping port check."
fi

if [ -n "$port_check_cmd" ]; then
  echo "Port listeners (filtered by port):"
  if [[ "$port_check_cmd" == *"lsof"* ]]; then
    $port_check_cmd || true
  else
    $port_check_cmd | grep -E ":$PORT\\b|:$PORT " || echo "No listener found on port $PORT"
  fi
  echo
fi

# More direct check with ss or lsof for the specific port
if command -v ss >/dev/null 2>&1; then
  ss -ltnp | grep -E ":$PORT\\b" || echo "No process listening on port $PORT (ss)"
elif command -v lsof >/dev/null 2>&1; then
  lsof -iTCP:$PORT -sTCP:LISTEN -P -n || echo "No process listening on port $PORT (lsof)"
fi

echo

# If service name provided, show systemctl status & journal
if [ -n "$SERVICE" ]; then
  if command -v systemctl >/dev/null 2>&1; then
    echo "systemctl status $SERVICE:"
    systemctl status "$SERVICE" --no-pager || true
    echo
    echo "Recent journalctl for $SERVICE (last 200 lines):"
    journalctl -u "$SERVICE" -n 200 --no-pager || true
    echo
  else
    echo "systemctl not available on this system."
    echo
  fi
fi

# Inspect log file if provided
if [ -n "$LOG_PATH" ]; then
  if [ -f "$LOG_PATH" ]; then
    echo "Permissions for log file: $(ls -l "$LOG_PATH")"
    echo
    echo "Grepping for common errors in logs:"
    grep -E --color=always -n "EADDRINUSE|Address already in use|Permission denied|Traceback|Exception|CRITICAL|FATAL|Error|ERR_" "$LOG_PATH" | tail -n 200 || echo "No obvious matches"
    echo
    echo "Last $TAIL_LINES lines of log ($LOG_PATH):"
    tail -n "$TAIL_LINES" "$LOG_PATH" || true
    echo
  else
    echo "Log file not found at: $LOG_PATH"
    echo
  fi
fi

# Check if user can bind to low port (if port < 1024)
if [ "$PORT" -ge 1 ] 2>/dev/null && [ "$PORT" -le 1023 ] 2>/dev/null; then
  echo "Port $PORT is a privileged port (<1024). Ensure you run as root or use setcap for the binary."
  echo "Example: sudo setcap 'cap_net_bind_service=+ep' /path/to/binary"
  echo
fi

# Check cwd and env
echo "Checking working dir and typical pitfalls:"
if [ -d "$CWD" ]; then
  echo "CWD exists: $CWD"
else
  echo "CWD does not exist: $CWD"
fi
echo

# Common suggestions and commands
echo "Suggested next steps / commands:"
if [ -n "$START_CMD" ]; then
  echo "To run in foreground to see errors directly:"
  echo "  cd $CWD && $START_CMD"
else
  echo "If you have a start command, re-run this script with -s \"your start command\""
fi

echo "To check if port is free and then start the server manually:"
echo "  # on Linux:"
echo "  ss -ltnp | grep :$PORT || (cd $CWD && $START_CMD)"
echo

echo "To kill a stale process on that port (use with caution):"
echo "  PID=\$(lsof -ti tcp:$PORT) && [ -n \"\$PID\" ] && kill \$PID"
echo

echo "If nothing obvious above, copy the startup command output and recent log lines and share them."
exit 0
