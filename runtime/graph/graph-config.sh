#!/data/data/com.termux/files/usr/bin/bash
#
# Aetherion Knowledge Graph
# Phase 14
# graph-config.sh
#

export AIFT_ROOT="${AIFT_ROOT:-$HOME/AIFT}"

export GRAPH_RUNTIME="$AIFT_ROOT/runtime/graph"

export REGISTRY="$AIFT_ROOT/registry"

export REPO_BRAIN="$REGISTRY/repo-brain.json"
export REPO_INTEL="$REGISTRY/repo-intelligence.json"
export CONTEXT_DB="$REGISTRY/aetherion-context.json"

export GRAPH_DB="$REGISTRY/graph-db.json"

export REPOSITORY_MAP="$REGISTRY/repository-map.json"
export RELATIONSHIP_MAP="$REGISTRY/relationship-map.json"
export CAPABILITY_MAP="$REGISTRY/capability-map.json"
export COMMAND_MAP="$REGISTRY/command-map.json"
export DEPENDENCY_MAP="$REGISTRY/dependency-map.json"
export API_MAP="$REGISTRY/api-map.json"
export AGENT_MAP="$REGISTRY/agent-map.json"
export SEMANTIC_MAP="$REGISTRY/semantic-map.json"

export GRAPH_REPORT="$REGISTRY/knowledge-graph.md"
export GRAPH_JSON="$REGISTRY/knowledge-graph.json"

export GRAPH_DOT="$REGISTRY/federation.dot"
export GRAPH_GRAPHML="$REGISTRY/federation.graphml"
export GRAPH_MERMAID="$REGISTRY/federation.mmd"

export MAX_FILE_SIZE=$((1024*1024))
export MAX_README_SIZE=$((256*1024))
export MAX_SCAN_DEPTH=8

export SUPPORTED_LANGUAGES="go javascript typescript python rust c cpp"

export SUPPORTED_FRAMEWORKS="next vite react express fastify"


init_graph_database() {

mkdir -p "$REGISTRY"

if [ ! -f "$GRAPH_DB" ]; then

cat > "$GRAPH_DB" <<JSON
{
  "generated": "",
  "version": "1.0",
  "nodes": [],
  "edges": [],
  "repositories": [],
  "capabilities": [],
  "commands": [],
  "dependencies": [],
  "apis": [],
  "agents": [],
  "concepts": []
}
JSON

fi

}


graph_timestamp() {

date -u +"%Y-%m-%dT%H:%M:%SZ"

}
