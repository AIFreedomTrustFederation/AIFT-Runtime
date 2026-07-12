#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"
source "$HOME/AIFT/runtime/pull.sh"
source "$HOME/AIFT/runtime/registry.sh"
source "$HOME/AIFT/runtime/intel.sh"
source "$HOME/AIFT/runtime/dashboard.sh"
source "$HOME/AIFT/runtime/graph.sh"
source "$HOME/AIFT/runtime/doctor.sh"
source "$HOME/AIFT/runtime/verify.sh"
source "$HOME/AIFT/runtime/push.sh"

aift_update() {
  echo "======================================"
  echo " AIFT Full Update Workflow"
  echo "======================================"

  aift_pull
  aift_registry
  aift_intelligence
  aift_dashboard
  aift_graph
  aift_doctor
  aift_verify
  aift_push
}
