#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"
source "$HOME/AIFT/runtime/repo.sh"

aift_graph() {
  local out="$AIFT_REPORTS/federation-graph.txt"

  {
    echo "AI Freedom Trust Federation"
    echo "├── Control Plane"
    echo "│   ├── $AIFT_WORKSPACE/aift-os.sh"
    echo "│   ├── $AIFT_WORKSPACE/runtime"
    echo "│   ├── $AIFT_REGISTRY/federation-index.json"
    echo "│   └── $AIFT_INTEL/federation-intelligence.json"

    for p in $(repo_paths); do
      echo "├── $(repo_name "$p")"
      echo "│   ├── Language: $(detect_language "$p")"
      echo "│   └── Runtime: $(detect_runtime "$p")"
    done

    echo "└── Principle"
    echo "    └── One workspace, many sovereign repositories, shared local-first runtime"
  } > "$out"

  cat "$out"
}
