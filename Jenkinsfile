pipeline {

    agent any

    environment {
        DOCKER_USER = "dknights"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/dikshax86/NFV_SPE_MajorProject1.git'
            }
        }

        stage('Build Images') {
            steps {
                sh '''
                docker build -t $DOCKER_USER/firewall:v1 ./firewall-service
                docker build -t $DOCKER_USER/switch:v1 ./switch-service
                docker build -t $DOCKER_USER/monitor:v1 ./monitor-service
                '''
            }
        }

        stage('Login to DockerHub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                    sh 'echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin'
                }
            }
        }

        stage('Push Images') {
            steps {
                sh '''
                docker push $DOCKER_USER/firewall:v1
                docker push $DOCKER_USER/switch:v1
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
