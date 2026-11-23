pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    // Jenkins polls GitHub every ~2 minutes and builds when it sees a new commit.
    triggers { pollSCM('H/2 * * * *') }

    parameters {
        string(name: 'RELEASE_VERSION', defaultValue: '3.0.0',
               description: 'Image tag the Deploy stage rolls out to Kubernetes')
        booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: false,
                     description: 'Tick to run the Deploy stage (needs the kubeconfig credential)')
    }

    environment {
        // CHANGE THIS to your Docker Hub username
        DOCKERHUB_USER = '2025tm93041'
        IMAGE = "${DOCKERHUB_USER}/aceest-fitness"
        // release_tag:application_file pairs, one Docker image per release
        RELEASES = '1.0.0:versions/ACEest_Fitness_v1.py 2.0.0:versions/ACEest_Fitness_v2.py 3.0.0:ACEest_Fitness.py'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Clean Build Environment') {
            steps {
                sh 'rm -rf .venv reports artifacts coverage.xml .scannerwork'
                sh 'python3 -m venv .venv'
                sh '.venv/bin/pip install -q -r requirements-dev.txt'
                sh 'mkdir -p reports artifacts'
            }
        }

        stage('Lint') {
            steps { sh '.venv/bin/flake8 .' }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    .venv/bin/pytest -q --junitxml=reports/junit.xml \
                        --cov=. --cov-config=.coveragerc --cov-report=xml
                '''
            }
        }

        stage('SonarQube Analysis & Quality Gate') {
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        export PATH=/opt/sonar-scanner/bin:$PATH
                        sonar-scanner \
                            -Dsonar.host.url=http://sonarqube:9000 \
                            -Dsonar.token=$SONAR_TOKEN \
                            -Dsonar.qualitygate.wait=true \
                            -Dsonar.qualitygate.timeout=300
                    '''
                    // Keep a copy of the key results as a build artifact (best effort)
                    sh '''
                        curl -s -u "$SONAR_TOKEN:" \
                          "http://sonarqube:9000/api/measures/component?component=aceest-fitness-cicd&metricKeys=alert_status,bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,security_hotspots,ncloc" \
                          -o artifacts/sonar-summary.json || true
                    '''
                }
            }
        }

        stage('Build Docker Images (all releases)') {
            steps {
                sh '''
                    for entry in $RELEASES; do
                        v=${entry%%:*}; f=${entry#*:}
                        docker build --build-arg APP_FILE=$f --build-arg APP_VERSION=$v \
                                     -t $IMAGE:$v -t $IMAGE:$v-build$BUILD_NUMBER .
                    done
                    docker tag $IMAGE:3.0.0 $IMAGE:latest
                '''
            }
        }

        stage('Test Inside Containers') {
            steps {
                sh '''
                    for entry in $RELEASES; do
                        v=${entry%%:*}
                        docker run --rm --user root -e EXPECTED_VERSION=$v \
                            -v "$PWD/tests:/app/tests:ro,Z" -v "$PWD/pytest.ini:/app/pytest.ini:ro,Z" \
                            $IMAGE:$v \
                            sh -c "pip install -q pytest==8.3.3 && pytest -q tests/test_container_smoke.py"
                    done
                '''
            }
        }

        stage('Package Build Artifacts') {
            steps {
                sh '''
                    for entry in $RELEASES; do
                        v=${entry%%:*}; f=${entry#*:}
                        tar czf artifacts/aceest-fitness-$v-src.tar.gz $f Dockerfile requirements.txt
                        printf '{"version":"%s","build":"%s","commit":"%s","image":"%s:%s"}\\n' \
                            "$v" "$BUILD_NUMBER" "$GIT_COMMIT" "$IMAGE" "$v" > artifacts/build-info-$v.json
                    done
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        for entry in $RELEASES; do
                            v=${entry%%:*}
                            docker push $IMAGE:$v
                            docker push $IMAGE:$v-build$BUILD_NUMBER
                        done
                        docker push $IMAGE:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes (Rolling Update + auto rollback)') {
            when { expression { return params.DEPLOY_TO_K8S } }
            environment { RELEASE_VERSION = "${params.RELEASE_VERSION}" }
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        NS=aceest-rolling
                        kubectl -n $NS get deploy aceest >/dev/null 2>&1 || ./scripts/apply.sh k8s/rolling
                        kubectl -n $NS set image deployment/aceest aceest=$IMAGE:$RELEASE_VERSION
                        if ! kubectl -n $NS rollout status deployment/aceest --timeout=120s; then
                            echo "Rollout failed - rolling back to the last stable version"
                            kubectl -n $NS rollout undo deployment/aceest
                            kubectl -n $NS rollout status deployment/aceest --timeout=120s
                            exit 1
                        fi
                    '''
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts artifacts: 'artifacts/**, coverage.xml', allowEmptyArchive: true, fingerprint: true
            sh 'docker image prune -f || true'
        }
        success { echo 'BUILD SUCCESS' }
        failure { echo 'BUILD FAILED - check the console output' }
    }
}
