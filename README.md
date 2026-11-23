# ACEest Fitness & Gym - CI/CD Pipeline (Assignment 2)

A Flask REST API for gym management, delivered through a fully automated pipeline:
**Git/GitHub -> Jenkins -> Pytest -> SonarQube -> Docker -> Docker Hub -> Kubernetes (Minikube)**.

## Application releases

| Release | Image tag | Source file | Adds |
|---------|-----------|-------------|------|
| 1.0.0 | `1.0.0` | `versions/ACEest_Fitness_v1.py` | Program catalogue, `/health`, `/version` |
| 2.0.0 | `2.0.0` | `versions/ACEest_Fitness_v2.py` | Clients, calorie targets, BMI |
| 3.0.0 | `3.0.0`, `latest` | `ACEest_Fitness.py` | Progress, workouts, membership |

The original Tkinter versions the API was ported from are kept in `legacy/`.
Releases are marked with Git tags `v1.0.0`, `v2.0.0`, `v3.0.0`.

## Repository layout

```
ACEest_Fitness.py        latest release (3.0.0)
versions/                earlier release snapshots (1.0.0, 2.0.0)
tests/                   Pytest suite (+ container smoke test)
Dockerfile               one multi-stage, non-root image definition for every release
Jenkinsfile              CI/CD pipeline
k8s/                     manifests: rolling, blue-green, canary, ab-testing, shadow
scripts/                 apply.sh (deploy manifests), setup_vm.sh (lab VM helpers)
sonar-project.properties SonarQube configuration
.github/workflows/       GitHub Actions CI (lint, tests, image build per release)
```

## Run locally

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
pytest -q --cov=. --cov-config=.coveragerc     # unit tests + coverage
flake8 .                                        # lint
python ACEest_Fitness.py                        # http://localhost:5000/version
```

## Docker

```bash
docker build -t aceest-fitness:3.0.0 .                                  # latest release
docker build --build-arg APP_FILE=versions/ACEest_Fitness_v1.py \
             --build-arg APP_VERSION=1.0.0 -t aceest-fitness:1.0.0 .    # an older release
docker run -d -p 5000:5000 aceest-fitness:3.0.0
```

## CI/CD architecture

```
Developer -> GitHub -> Jenkins (poll SCM every ~2 min)
   Checkout -> clean venv -> flake8 -> Pytest + coverage
   -> SonarQube analysis + quality gate (build fails if the gate fails)
   -> docker build (1.0.0, 2.0.0, 3.0.0) -> tests inside each container
   -> package per-version artifacts -> push all tags to Docker Hub
   -> (optional) kubectl rolling update with automatic rollback -> Minikube
```

Jenkins credentials used: `dockerhub-creds` (username/password), `sonar-token` (secret text),
`kubeconfig` (secret file, only for the deploy stage).

## Kubernetes deployment strategies

Each strategy lives in its own namespace and NodePort. Set your Docker Hub user first:
`export DOCKERHUB_USER=<username>` and `IP=$(minikube ip)`.

| Strategy | Namespace | NodePort | Apply |
|----------|-----------|----------|-------|
| Rolling update | `aceest-rolling` | 30081 | `./scripts/apply.sh k8s/rolling` |
| Blue-green | `aceest-bluegreen` | 30082 (live), 30092 (green preview) | `./scripts/apply.sh k8s/blue-green` |
| Canary | `aceest-canary` | 30083 | `./scripts/apply.sh k8s/canary` |
| A/B testing | `aceest-ab` | 30084 | `./scripts/apply.sh k8s/ab-testing` |
| Shadow | `aceest-shadow` | 30085 | `./scripts/apply.sh k8s/shadow` |

**Rolling update + rollback**
```bash
kubectl -n aceest-rolling set image deploy/aceest aceest=$DOCKERHUB_USER/aceest-fitness:3.0.0
kubectl -n aceest-rolling rollout status deploy/aceest
kubectl -n aceest-rolling rollout undo deploy/aceest        # revert to the last stable version
```
**Blue-green + rollback** (instant switch, old version stays warm)
```bash
kubectl -n aceest-bluegreen patch svc aceest -p '{"spec":{"selector":{"app":"aceest","slot":"green"}}}'
kubectl -n aceest-bluegreen patch svc aceest -p '{"spec":{"selector":{"app":"aceest","slot":"blue"}}}'   # rollback
```
**Canary** (about 1 in 5 requests reach 3.0.0)
```bash
for i in $(seq 20); do curl -s $IP:30083/version | grep -o '"version":"[0-9.]*"'; done | sort | uniq -c
kubectl -n aceest-canary scale deploy/aceest-canary --replicas=0                        # rollback
```
**A/B testing** (header decides the variant)
```bash
curl -si $IP:30084/version | grep -iE 'x-served|version'                                 # variant A
curl -si -H "X-User-Group: b" $IP:30084/version | grep -iE 'x-served|version'            # variant B
```
**Shadow** (users see production; every request is mirrored to the shadow)
```bash
curl -s $IP:30085/version
kubectl -n aceest-shadow logs deploy/aceest-shadow --tail=5                              # mirrored traffic
```

## Version control strategy

Feature branches merged by pull request, conventional commit messages
(`feat:`, `fix:`, `test:`, `build:`, `ci:`, `docs:`), annotated release tags `vX.Y.Z`.

## Running everything in GitHub Codespaces

The repo includes a `.devcontainer/` setup (Python 3.12, Docker-in-Docker, kubectl, Minikube, Java 17).
After opening a Codespace on this repo:

```bash
./scripts/codespace.sh bootstrap    # one-time: sonar-scanner + Jenkins program
./scripts/codespace.sh start_all    # Minikube, SonarQube, Jenkins (after every restart)
./scripts/codespace.sh expose       # forward strategy endpoints to ports 8081-8085
```

Jenkins is on port 8080 and SonarQube on 9000 (Ports tab). Set a port's visibility to
*Public* in the Ports tab to get a shareable URL for a deployed strategy.
