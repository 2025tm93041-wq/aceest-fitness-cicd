#!/usr/bin/env bash
# Creates the Git history for Assignment 2: commits, release tags and a feature branch.
# Usage:  ./scripts/git_setup.sh <your-github-username>
# Run it ONCE, from the project folder. Works in a fresh folder (lab VM: create the empty
# GitHub repo "aceest-fitness-cicd" first) and inside a Codespace opened on that repo.
# On the lab VM git asks for a password: paste your GitHub token.
set -euo pipefail

user="${1:?usage: git_setup.sh <github-username>}"
remote="${REMOTE_URL:-https://github.com/${user}/aceest-fitness-cicd.git}"

[ -f ACEest_Fitness.py ] || { echo "Run this from the project folder (the one containing ACEest_Fitness.py)."; exit 1; }
if git rev-parse -q --verify refs/tags/v1.0.0 >/dev/null 2>&1; then
    echo "The release history already exists - nothing to do."; exit 1
fi

if [ -d .git ]; then
    # Codespaces / an existing clone: keep its remote and its first commit
    git remote get-url origin >/dev/null 2>&1 || git remote add origin "$remote"
    git checkout -q main
else
    git init -q -b main
    git remote add origin "$remote"
fi

git add legacy .gitignore
git commit -q -m "chore: add original Tkinter versions as reference"

git add versions/ACEest_Fitness_v1.py requirements.txt .flake8
git commit -q -m "feat: release 1.0.0 program catalogue API"
git tag -a v1.0.0 -m "Release 1.0.0"

git add versions/ACEest_Fitness_v2.py
git commit -q -m "feat: release 2.0.0 client management, calories and BMI"
git tag -a v2.0.0 -m "Release 2.0.0"

git add ACEest_Fitness.py
git commit -q -m "feat: release 3.0.0 progress, workouts and membership"
git tag -a v3.0.0 -m "Release 3.0.0"

echo "Pushing main and release tags..."
git push -u origin main --tags

git checkout -q -b feature/devops-pipeline
git add tests pytest.ini .coveragerc requirements-dev.txt
git commit -q -m "test: add Pytest suite for all releases"
git add Dockerfile .dockerignore
git commit -q -m "build: add multi-release non-root Dockerfile"
git add k8s scripts
git commit -q -m "feat: add Kubernetes manifests for five deployment strategies"
git add sonar-project.properties Jenkinsfile .github .devcontainer README.md
git commit -q -m "ci: add Jenkins pipeline, SonarQube config and GitHub Actions"

echo "Pushing the feature branch..."
git push -u origin feature/devops-pipeline

echo
echo "Done. Now open https://github.com/${user}/aceest-fitness-cicd and click"
echo "'Compare & pull request' -> Create pull request -> Merge pull request."
echo "Then run:  git checkout main && git pull origin main"
