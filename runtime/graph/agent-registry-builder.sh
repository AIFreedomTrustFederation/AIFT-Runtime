#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REGISTRY="$ROOT/registry"

CAP="$REGISTRY/capability-map.json"
OUTPUT="$REGISTRY/agent-map.json"

echo "========================================"
echo " Aetherion Agent Registry Builder v1"
echo " Mapping Capabilities To Agents"
echo "========================================"


jq '
[
.[] |

{
 repository:.repository,

 agents:

 (

  [
   .capabilities[] |

   if .=="operating-system"
   then
    {
     name:"SystemAgent",
     abilities:[
       "inspect_runtime",
       "manage_services",
       "coordinate_tasks"
     ]
    }

   elif .=="development-platform"
   then
    {
     name:"ForgeAgent",
     abilities:[
       "analyze_code",
       "generate_projects",
       "manage_builds"
     ]
    }

   elif .=="constitutional-source"
   then
    {
     name:"GenesisAgent",
     abilities:[
       "preserve_doctrine",
       "validate_structure",
       "maintain_canon"
     ]
    }

   elif .=="knowledge-production"
   then
    {
     name:"KnowledgeAgent",
     abilities:[
       "organize_documents",
       "index_information",
       "manage_publications"
     ]
    }

   elif .=="cloud-infrastructure"
   then
    {
     name:"InfrastructureAgent",
     abilities:[
       "manage_nodes",
       "monitor_services",
       "deploy_apps"
     ]
    }

   elif .=="media-generation"
   then
    {
     name:"MediaAgent",
     abilities:[
       "process_media",
       "create_assets"
     ]
    }

   elif .=="automation-ai"
   then
    {
     name:"AutomationAgent",
     abilities:[
       "execute_workflows",
       "assist_reasoning"
     ]
    }

   elif .=="web-application"
   then
    {
     name:"ApplicationAgent",
     abilities:[
       "manage_interfaces",
       "inspect_frontends"
     ]
    }

   elif .=="value-system"
   then
    {
     name:"StewardshipAgent",
     abilities:[
       "track_protocols",
       "maintain_rules"
     ]
    }

   else empty end

  ]

 )

}

]
' "$CAP" > "$OUTPUT"


echo ""
echo "========================================"
echo " Agent Registry Complete"
echo "$OUTPUT"
echo "========================================"

