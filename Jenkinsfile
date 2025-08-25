pipeline {
    agent any

    stages {
        stage('Build & Dockerize Booking-Service') {
            when {
                changeset "booking_service/**"
            }
            steps {
                echo 'Booking-service klasöründe değişiklik yapıldı, imaj oluşturuluyor...'
                sh 'docker build -t atakandockerdevops/booking_service:latest -f booking_service/Dockerfile booking_service'
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'docker login -u $DOCKER_USER -p $DOCKER_PASS'
                    sh 'docker push atakandockerdevops/booking_service:latest'
                }
            }
        }

        stage('Build & Dockerize User-Service') {
            when {
                changeset "user_service/**"
            }
            steps {
                echo 'User-service klasöründe değişiklik yapıldı, imaj oluşturuluyor...'
                // Buraya user-service'i build eden docker komutlarını yazın.
                // Örnek:
                sh 'docker build -t atakandockerdevops/user_service:latest -f user_service/Dockerfile user_service'
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'docker login -u $DOCKER_USER -p $DOCKER_PASS'
                    sh 'docker push atakandockerdevops/user_service:latest'
                }
            }
        }

        stage('Build & Dockerize Car-Service') {
            when {
                changeset "car_service/**"
            }
            steps {
                echo 'Car-service klasöründe değişiklik yapıldı, imaj oluşturuluyor...'
                // Buraya car-service'i build eden docker komutlarını yazın.
                // Örnek:
                sh 'docker build -t atakandockerdevops/car_service:latest -f car_service/Dockerfile car_service'
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'docker login -u $DOCKER_USER -p $DOCKER_PASS'
                    sh 'docker push atakandockerdevops/car_service:latest'
                }
            }
        }
    }
}