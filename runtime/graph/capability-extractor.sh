#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REGISTRY="$ROOT/registry"

INTEL="$REGISTRY/repo-intelligence.json"
OUTPUT="$REGISTRY/capability-map.json"

echo "========================================"
echo " Aetherion Capability Extractor v1"
echo " Discovering Federation Abilities"
echo "========================================"


jq '
[
.[] |

{
 repository:.name,

 capabilities:
 [

  (
   if (.name|test("AIFT-OS";"i"))
   then "operating-system"
   else empty end
  ),

  (
   if (.name|test("Forge";"i"))
   then "development-platform"
   else empty end
  ),

  (
   if (.name|test("Genesis";"i"))
   then "constitutional-source"
   else empty end
  ),

  (
   if (.name|test("Book";"i"))
   then "knowledge-production"
   else empty end
  ),

  (
   if (.name|test("VPS";"i"))
   then "cloud-infrastructure"
   else empty end
  ),

  (
   if (.name|test("Coin|bio";"i"))
   then "value-system"
   else empty end
  ),

  (
   if (.name|test("OpenMontage";"i"))
   then "media-generation"
   else empty end
  ),

  (
   if (.framework=="Next.js")
   then "web-application"
   else empty end
  ),

  (
   if (.framework=="Vite")
   then "frontend-interface"
   else empty end
  ),

  (
   if (.language=="Go")
   then "systems-programming"
   else empty end
  ),

  (
   if (.language=="Python")
   then "automation-ai"
   else empty end
  )

 ]

}

]
' "$INTEL" > "$OUTPUT"


echo ""
echo "========================================"
echo " Capability Extraction Complete"
echo "$OUTPUT"
echo "========================================"

