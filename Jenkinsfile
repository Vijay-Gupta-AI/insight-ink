pipeline {
    agent any

    environment {
        // Define your Heroku app name and GitHub repo name
        HEROKU_APP_NAME = "insight-ink"
        HEROKU_API_KEY = credentials('heroku-api-key')  // Jenkins credentials ID for your Heroku API key
        HEROKU_EMAIL = "mevijaygupta2024@gmail.com"  // Heroku account email
       
    }

    stages {
        stage('Checkout Code') {
            
            steps {
                // Checkout code from GitHub repository
                checkout scm
            }
        }

        stage('Build Docker Image') {
            when {
                branch 'main'  // Only runs when changes are pushed to the 'main' branch
            }
            steps {
                script {
                    // Build the Docker image
                    sh 'docker build -t ${HEROKU_APP_NAME} .'
                }
            }
        }

        stage('Login to Heroku') {
            when {
                branch 'main'  // Only runs when changes are pushed to the 'main' branch
            }
            steps {
                script {
                    // Login to Heroku CLI using the API key stored in Jenkins credentials
                    withCredentials([string(credentialsId: 'heroku-api-key', variable: 'HEROKU_API_KEY')]) {
                        sh 'echo $HEROKU_API_KEY | docker login --username=_ --password-stdin registry.heroku.com'
                    }
                }
            }
        }

        stage('Push to Heroku Container Registry') {
            when {
                branch 'main'  // Only runs when changes are pushed to the 'main' branch
            }
            steps {
                script {
                    // Push the Docker image to Heroku container registry
                    sh "docker tag ${HEROKU_APP_NAME}:latest registry.heroku.com/${HEROKU_APP_NAME}/web"
                    sh "docker push registry.heroku.com/${HEROKU_APP_NAME}/web"
                }
            }
        }

        stage('Release on Heroku') {
            when {
                branch 'main'  // Only runs when changes are pushed to the 'main' branch
            }
            steps {
                script {
                    // Trigger a Heroku release using the Docker image pushed to the registry
                    sh "heroku releases:create --app ${HEROKU_APP_NAME}"
                }
            }
        }
    }

    post {
        always {
            // Clean up after the build
            sh 'docker system prune -f'
        }
    }
}

