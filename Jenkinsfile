pipeline {

    agent any

    environment {
        DOCKER_USER = "ishakumarii"
    }

    stages {

        stage('Build Images') {

            steps {

                sh '''
                docker build -t $DOCKER_USER/firewall:v1 ./firewall-service
                docker build -t $DOCKER_USER/switch:v2 ./switch-service
                docker build -t $DOCKER_USER/monitor:v1 ./monitor-service
                '''
            }
        }

        stage('Push Images') {

            steps {

                sh '''
                docker push $DOCKER_USER/firewall:v1
                docker push $DOCKER_USER/switch:v2
                docker push $DOCKER_USER/monitor:v1
                '''
            }
        }

        stage('Deploy to Kubernetes') {

            steps {

                sh 'chmod +x deploy.sh'
                sh './deploy.sh'
            }
        }
    }

    post {

        success {
            echo 'Deployment Successful'
        }

        failure {
            echo 'Pipeline Failed'
        }
    }
}
