#!/data/data/com.termux/files/usr/bin/bash
# Stop only the Aetherion server recorded by this checkout's start.sh.
set -euo pipefail

AI_HOME="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PID_FILE="$AI_HOME/aetherion.pid"
MODEL="$AI_HOME/models/aetherion.gguf"
LLAMA="$HOME/Aetherion/llama.cpp/build/bin/llama-server"

if [[ ! -f "$PID_FILE" ]]; then
  echo "Aetherion is not running (no PID file)."
  exit 0
fi

pid=''
IFS= read -r pid < "$PID_FILE" || :
if [[ ! "$pid" =~ ^[1-9][0-9]*$ ]]; then
  echo "ERROR: Invalid Aetherion PID file: $PID_FILE" >&2
  exit 1
fi

if ! kill -0 "$pid" 2>/dev/null; then
  rm -- "$PID_FILE"
  echo "Removed stale Aetherion PID file ($pid); no process was signaled."
  exit 0
fi

cmdline="/proc/$pid/cmdline"
if [[ ! -r "$cmdline" ]]; then
  echo "ERROR: Cannot inspect PID $pid; refusing to signal an unverified process." >&2
  exit 1
fi

args=()
if ! mapfile -d '' -t args < "$cmdline" || [[ "${args[0]:-}" != "$LLAMA" ]]; then
  echo "ERROR: PID $pid does not match this Aetherion executable; refusing to signal it." >&2
  exit 1
fi

owns_model=false
for ((i=1; i+1<${#args[@]}; i++)); do
  if [[ "${args[i]}" == '-m' && "${args[i+1]}" == "$MODEL" ]]; then
    owns_model=true
    break
  fi
done
if [[ "$owns_model" != true ]]; then
  echo "ERROR: PID $pid is not running this Aetherion model; refusing to signal it." >&2
  exit 1
fi

if ! kill -TERM "$pid"; then
  echo "ERROR: Could not signal Aetherion PID $pid." >&2
  exit 1
fi

# Wait briefly; do not claim the server stopped merely because TERM was sent.
for ((i=0; i<30; i++)); do
  if ! kill -0 "$pid" 2>/dev/null; then
    break
  fi
  state=''
  if [[ -r "/proc/$pid/stat" ]]; then
    IFS= read -r state < "/proc/$pid/stat" || :
    [[ "$state" == *') Z '* ]] && break
  fi
  sleep 0.1
done
if kill -0 "$pid" 2>/dev/null; then
  state=''
  if [[ -r "/proc/$pid/stat" ]]; then
    IFS= read -r state < "/proc/$pid/stat" || :
  fi
  if [[ "$state" != *') Z '* ]]; then
    echo "ERROR: Aetherion PID $pid has not exited after SIGTERM; check manually." >&2
    exit 1
  fi
fi

# Do not erase a PID file replaced by a concurrent start.
current=''
IFS= read -r current < "$PID_FILE" || :
if [[ "$current" == "$pid" ]]; then
  rm -- "$PID_FILE"
fi
echo "Aetherion stopped (PID $pid)."
