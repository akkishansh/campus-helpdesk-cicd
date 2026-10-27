pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        APP_NAME = 'campus-helpdesk'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Build and Test') {
            steps {
                sh 'python3 -m unittest discover -s tests -v'
                sh 'python3 -m py_compile app.py tests/test_app.py'
            }
        }

        stage('Build Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')]) {
                    script {
                        env.IMAGE_REPO = "docker.io/${env.DOCKERHUB_USER}/campus-helpdesk"
                        env.IMAGE_TAG = "${env.BUILD_NUMBER}"
                    }
                    sh 'docker build --pull -t "$IMAGE_REPO:$IMAGE_TAG" -t "$IMAGE_REPO:latest" .'
                }
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')]) {
                    sh '''
                        set +x
                        echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USER" --password-stdin
                        docker push "$IMAGE_REPO:$IMAGE_TAG"
                        docker push "$IMAGE_REPO:latest"
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh '''
                    kubectl apply -f k8s/pvc.yaml
                    sed "s|docker.io/DOCKERHUB_USERNAME/campus-helpdesk:latest|$IMAGE_REPO:$IMAGE_TAG|" k8s/deployment.yaml | kubectl apply -f -
                    kubectl apply -f k8s/service.yaml
                    kubectl rollout status deployment/$APP_NAME --timeout=180s
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    kubectl get pods -l app=$APP_NAME -o wide
                    kubectl get deployment,service $APP_NAME
                    kubectl get endpoints $APP_NAME
                    kubectl run helpdesk-smoke-$BUILD_NUMBER --rm -i --restart=Never --image=curlimages/curl:8.10.1 -- curl --fail --silent http://campus-helpdesk/health
                '''
            }
        }
    }

    post {
        always { sh 'docker image prune -f || true' }
        success { echo "Campus Helpdesk deployed as ${IMAGE_REPO}:${IMAGE_TAG}" }
        failure { echo 'Pipeline failed. Review the failed stage in the Jenkins console output.' }
    }
}
