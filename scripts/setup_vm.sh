#!/usr/bin/env bash
# Re-creates the lab VM tooling after a reset (only ~/workspace survives a reset).
# UNTESTED helper: run the parts you need, one at a time, and read the output.
set -euo pipefail

install_kubectl() {
    cd /tmp
    curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -m 0755 kubectl /usr/local/bin/kubectl
    kubectl version --client
}

install_minikube() {
    cd /tmp
    curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
    sudo install minikube-linux-amd64 /usr/local/bin/minikube
    minikube version
}

start_minikube() {
    minikube start --driver=docker --cpus=2 --memory=2048
    kubectl get nodes
}

start_sonarqube() {
    docker rm -f sonarqube 2>/dev/null || true
    docker run -d --name sonarqube -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true -p 9000:9000 sonarqube:latest
    echo "SonarQube is starting - open http://localhost:9000 in a minute or two"
}

install_sonar_scanner() {
    cd /tmp
    wget -q https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-8.0.1.6346-linux-x64.zip
    sudo dnf install -y unzip
    unzip -oq sonar-scanner-cli-8.0.1.6346-linux-x64.zip
    sudo rm -rf /opt/sonar-scanner
    sudo mv sonar-scanner-8.0.1.6346-linux-x64 /opt/sonar-scanner
    /opt/sonar-scanner/bin/sonar-scanner --version
}

allow_jenkins_docker() {
    sudo usermod -aG docker jenkins
    sudo systemctl restart jenkins
    sudo -u jenkins docker ps
}

"${1:?usage: setup_vm.sh <install_kubectl|install_minikube|start_minikube|start_sonarqube|install_sonar_scanner|allow_jenkins_docker>}"
