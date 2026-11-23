#!/usr/bin/env bash
# Apply a folder of Kubernetes manifests, filling in your Docker Hub username.
# Usage:  export DOCKERHUB_USER=yourname;  ./scripts/apply.sh k8s/rolling
set -euo pipefail
: "${DOCKERHUB_USER:?export DOCKERHUB_USER=<your Docker Hub username> first}"
dir="${1:?usage: apply.sh <manifest-directory>}"
for f in "$dir"/*.yaml; do
    sed "s|DOCKERHUB_USER|${DOCKERHUB_USER}|g" "$f"
    echo "---"
done | kubectl apply -f -
