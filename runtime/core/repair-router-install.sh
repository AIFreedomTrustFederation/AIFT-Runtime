#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
CORE="$ROOT/runtime/core"

echo "========================================"
echo " Installing Aetherion Router v4"
echo "========================================"


# Replace aeroute alias

cat > "$CORE/aeroute" <<'CMD'
#!/data/data/com.termux/files/usr/bin/bash

exec $HOME/AIFT/runtime/core/aetherion-agent-router.sh "$@"

CMD


chmod +x "$CORE/aeroute"


echo ""
echo "Router target:"
head -5 "$CORE/aetherion-agent-router.sh"


echo ""
echo "Alias fixed:"
cat "$CORE/aeroute"


echo ""
echo "========================================"
echo " Installation Complete"
echo "========================================"

