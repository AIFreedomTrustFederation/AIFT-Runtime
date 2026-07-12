#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REGISTRY="$ROOT/registry"

INTEL="$REGISTRY/repo-intelligence.json"
GRAPH="$REGISTRY/graph-db.json"

REL="$REGISTRY/relationship-map.json"
MERMAID="$REGISTRY/federation.mmd"
DOT="$REGISTRY/federation.dot"

echo "========================================"
echo " Aetherion Graph Builder v1"
echo " Building Federation Relationships"
echo "========================================"


if [ ! -f "$INTEL" ]; then
 echo "Missing repo intelligence"
 exit 1
fi


jq '
{
generated:(now|todate),
version:"1.0",

nodes:
[
 .[] |
 {
  id:.name,
  type:.role,
  language:.language,
  framework:.framework
 }
],

edges:
[
 .[] |

(
 if (.name=="AIFT-OS")
 then
 {
 from:.name,
 to:"AIFT-Forge",
 relationship:"orchestrates"
 }
 else empty end
),

(
 if (.name=="AIFT-Genesis")
 then
 {
 from:.name,
 to:"AIFT-Forge",
 relationship:"contains_doctrine"
 }
 else empty end
),

(
 if (.framework=="Next.js")
 then
 {
 from:.name,
 to:"AIFT-Forge",
 relationship:"creates_interface"
 }
 else empty end
),

(
 if (.name=="VPS")
 then
 {
 from:.name,
 to:"AIFT-OS",
 relationship:"provides_infrastructure"
 }
 else empty end
),

(
 if (.name=="BookSmith-Federation-OS")
 then
 {
 from:.name,
 to:"booksmith-ai",
 relationship:"extends"
 }
 else empty end
),

(
 if (.name=="capital-city-provisions")
 then
 {
 from:.name,
 to:"tastycutz",
 relationship:"business_application"
 }
 else empty end
)

]

}
' "$INTEL" > "$GRAPH"


cp "$GRAPH" "$REL"


echo "graph TD" > "$MERMAID"

jq -r '
.edges[] |
"    \(.from) -->|\(.relationship)| \(.to)"
' "$GRAPH" >> "$MERMAID"


echo "digraph Aetherion {" > "$DOT"

jq -r '
.edges[] |
"\"\(.from)\" -> \"\(.to)\" [label=\"\(.relationship)\"];"
' "$GRAPH" >> "$DOT"

echo "}" >> "$DOT"


echo ""
echo "========================================"
echo " Graph Build Complete"
echo ""
echo "$GRAPH"
echo "$REL"
echo "$MERMAID"
echo "$DOT"
echo "========================================"

