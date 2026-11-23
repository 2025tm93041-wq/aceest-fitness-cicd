#!/usr/bin/env bash
# Helper for running the whole assignment inside GitHub Codespaces.
# Usage: ./scripts/codespace.sh <command>
#   bootstrap          one-time: install unzip, sonar-scanner and the Jenkins program
#   start_all          start Minikube, SonarQube and Jenkins (run after every restart)
#   start_minikube | start_sonarqube | start_jenkins | stop_sonarqube
#   jenkins_password   print Jenkins' first-time unlock password
#   expose             forward the five strategy endpoints to ports 8081-8085
#   status             show what is running
# Codespaces keeps your files when it stops, but NOT running programs, so use
# start_all each time you come back.
set -euo pipefail

JENKINS_HOME_DIR="$HOME/jenkins_home"
JENKINS_WAR="$HOME/jenkins.war"

install_sonar_scanner() {
    [ -x /opt/sonar-scanner/bin/sonar-scanner ] && { echo "sonar-scanner already installed"; return; }
    cd /tmp
    wget -q https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-8.0.1.6346-linux-x64.zip
    unzip -oq sonar-scanner-cli-8.0.1.6346-linux-x64.zip
    sudo rm -rf /opt/sonar-scanner
    sudo mv sonar-scanner-8.0.1.6346-linux-x64 /opt/sonar-scanner
    /opt/sonar-scanner/bin/sonar-scanner --version
}

install_jenkins() {
    command -v java >/dev/null || sudo apt-get install -y -qq openjdk-17-jre-headless
    [ -f "$JENKINS_WAR" ] || curl -fL -o "$JENKINS_WAR" https://get.jenkins.io/war-stable/latest/jenkins.war
    echo "Jenkins program ready: $JENKINS_WAR"
}

bootstrap() {
    sudo apt-get update -qq
    sudo apt-get install -y -qq unzip curl wget
    install_sonar_scanner
    install_jenkins
}

start_minikube() {
    if minikube status >/dev/null 2>&1; then echo "Minikube already running"; return; fi
    minikube start --driver=docker --cpus=2 --memory=2048
    kubectl get nodes
}

start_sonarqube() {
    if docker ps --format '{{.Names}}' | grep -qx sonarqube; then echo "SonarQube already running"; return; fi
    if docker ps -a --format '{{.Names}}' | grep -qx sonarqube; then
        docker start sonarqube
    else
        docker run -d --name sonarqube -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true -p 9000:9000 sonarqube:latest
    fi
    echo "SonarQube is starting (1-3 minutes). Open port 9000 from the Ports tab."
}

stop_sonarqube() { docker stop sonarqube; }

start_jenkins() {
    if pgrep -f jenkins.war >/dev/null; then echo "Jenkins already running"; return; fi
    install_jenkins
    mkdir -p "$JENKINS_HOME_DIR"
    JENKINS_HOME="$JENKINS_HOME_DIR" nohup java \
        -Dhudson.security.csrf.DefaultCrumbIssuer.EXCLUDE_SESSION_ID=true \
        -jar "$JENKINS_WAR" --httpPort=8080 > "$HOME/jenkins.log" 2>&1 &
    echo "Jenkins is starting (1-2 minutes). Open port 8080 from the Ports tab."
    echo "Log: tail -f ~/jenkins.log     First-time password: ./scripts/codespace.sh jenkins_password"
}

jenkins_password() { cat "$JENKINS_HOME_DIR/secrets/initialAdminPassword"; }

start_all() { start_minikube; start_sonarqube; start_jenkins; }

forward() {  # forward <namespace> <service> <local-port>
    if kubectl -n "$1" get svc "$2" >/dev/null 2>&1; then
        nohup kubectl -n "$1" port-forward "svc/$2" "$3:80" --address 0.0.0.0 \
            > "$HOME/pf-$3.log" 2>&1 &
        echo "port $3 -> $1/$2"
    else
        echo "skipping port $3: $1/$2 is not deployed yet"
    fi
}

expose() {
    pkill -f "kubectl.*port-forward" 2>/dev/null || true
    sleep 1
    forward aceest-rolling   aceest  8081
    forward aceest-bluegreen aceest  8082
    forward aceest-canary    aceest  8083
    forward aceest-ab        gateway 8084
    forward aceest-shadow    gateway 8085
    echo "In the Ports tab, right-click each port -> Port Visibility -> Public to get a shareable URL."
}

status() {
    echo "--- containers"; docker ps --format '{{.Names}}\t{{.Status}}'
    echo "--- minikube";   minikube status 2>&1 | head -5 || true
    echo "--- jenkins";    pgrep -f jenkins.war >/dev/null && echo running || echo stopped
    echo "--- memory";     free -h | head -2
}

"${1:?usage: codespace.sh <bootstrap|start_all|start_minikube|start_sonarqube|start_jenkins|jenkins_password|expose|status>}"
