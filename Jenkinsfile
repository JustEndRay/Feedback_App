pipeline {
    agent any
    
    parameters {
        booleanParam(name: 'FORCE_ROLLBACK', description: '''Примусовий ролбек до образу з DockerHub
Гайд по ролбеку:
1. Ролбек на останній тег:
   • Встановіть цю галочку
   • Залиште ROLLBACK_TAG порожнім
   • Запустіть пайплайн

2. Ролбек на конкретний тег:
   • Встановіть цю галочку
   • Введіть номер тегу в ROLLBACK_TAG
   • Запустіть пайплайн''', defaultValue: false)
        string(name: 'ROLLBACK_TAG', defaultValue: '', description: 'Тег DockerHub для ручного ролбеку (залишити порожнім для latest)')
        string(name: 'EC2_IP', description: 'IP адреса EC2 інстансу', defaultValue: '13.38.124.210')
        string(name: 'EC2_USER', description: 'Користувач EC2', defaultValue: 'ubuntu')
        booleanParam(name: 'FORCE_REBUILD', description: '''М'яке очищення для перезапуску застосунку:
• Зупиняє тільки контейнери поточного застосунку
• Видаляє тільки томи поточного застосунку
• Очищує тільки образи поточного застосунку
• Зберігає всі інші Docker ресурси

Коли використовувати:
• При проблемах з поточним застосунком
• Для перезапуску з чистими томами
• Коли потрібно зберегти інші контейнери на сервері

Стандартне оновлення (без FORCE_REBUILD):
• Зупиняє тільки контейнери поточного застосунку
• Зберігає всі томи та дані
• Оновлює тільки код застосунку
• Ідеально для звичайних оновлень без втрати даних''', defaultValue: false)
        booleanParam(name: 'FORCE_CLEANUP', description: '''Повне очищення EC2 перед розгортанням:
• Видаляє ВСІ Docker контейнери на сервері
• Видаляє ВСІ Docker образи на сервері
• Видаляє ВСІ Docker томи на сервері
• Очищує весь Docker кеш
• Видаляє всі тимчасові файли

Коли використовувати:
• При критичних проблемах з місцем на диску
• Коли потрібно повністю очистити сервер
• При міграції на новий сервер
• Коли інші методи не допомогли

⚠️ УВАГА: Це видалить ВСІ Docker ресурси на сервері!''', defaultValue: false)
        booleanParam(name: 'SKIP_DOCKERHUB', description: 'Пропустити створення та пуш образу в DockerHub (пришвидшить розгортання)', defaultValue: false)
    }

    environment {
        // Jenkins Credentials
        AWS_SSH_KEY = credentials('aws-ec2-ssh-key')
        SECRET_KEY = credentials('flask-secret-key')
        POSTGRES_PASSWORD = credentials('postgres-password')
        DOCKERHUB_CREDENTIALS = credentials('dockerhub_push')

        // Щляхи на EC2
        DEPLOY_DIR = "/home/${params.EC2_USER}/feedback-app-deploy"
        BUILD_NUMBER_TAG = "${env.BUILD_NUMBER}"
        APP_NAME = "feedback-app"
        COMPOSE_FILE = "docker-compose.prod.yml"
        BACKUP_FILE = "previous_version.txt"

        // Змінні середовища для розгортання
        DOCKER_IMAGE = 'justendray/feedback_app'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('🔍 Validate EC2 Connection') {
            steps {
                script {
                    echo "🔍 Перевірка підключення до EC2..."
                    
                    // Перевірка доступності EC2
                    def maxRetries = 3
                    def retryCount = 0
                    def connected = false
                    
                    while (retryCount < maxRetries && !connected) {
                        try {
                            def result = sh(
                                script: """
                                    timeout 10 ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no -o ConnectTimeout=5 ${EC2_USER}@${EC2_IP} 'echo "Connection successful"' || exit 1
                                """,
                                returnStdout: true
                            ).trim()
                            
                            if (result.contains("Connection successful")) {
                                connected = true
                                echo "✅ Підключення до EC2 успішне"
                            }
                        } catch (Exception e) {
                            retryCount++
                            if (retryCount < maxRetries) {
                                echo "⚠️ Спроба ${retryCount} не вдалася. Очікування перед повторною спробою..."
                                sleep(5)
                            }
                        }
                    }
                    
                    if (!connected) {
                        error """
                        ❌ Не вдалося підключитися до EC2 після ${maxRetries} спроб.
                        
                        Можливі причини:
                        1. EC2 інстанс не запущений
                        2. Неправильна IP адреса: ${EC2_IP}
                        3. Security Group не дозволяє SSH (порт 22)
                        4. Неправильний SSH ключ
                        
                        Перевірте:
                        • Статус EC2 інстансу в AWS Console
                        • Налаштування Security Group
                        • Правильність IP адреси
                        • Валідність SSH ключа
                        """
                    }
                }
            }
        }

        stage('🧹 Force Cleanup on EC2') {
            when {
                expression { return params.FORCE_CLEANUP }
            }
            steps {
                script {
                    echo "🧹 Виконуємо повне очищення EC2 перед копіюванням файлів..."
                    def composeFile = COMPOSE_FILE
                    sh "ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_IP} 'set -e; echo \"🧹 Повне очищення EC2...\"; docker-compose -f ${composeFile} down -v || true; docker rm -f \$(docker ps -aq) || true; docker rmi -f \$(docker images -q) || true; docker volume rm \$(docker volume ls -q) || true; docker system prune -af --volumes'"
                }
            }
        }

        stage('🔍 Get Last DockerHub Tag Info') {
            when {
                expression { return !params.SKIP_DOCKERHUB }
            }
            steps {
                script {
                    def tagInfo = sh(
                        script: """
                            curl -s https://hub.docker.com/v2/repositories/justendray/feedback_app/tags?page_size=1 | jq -r '.results[0] | "Тег: \\(.name), Дата: \\(.last_updated)"'
                        """,
                        returnStdout: true
                    ).trim()
                    echo "Останній образ у DockerHub: ${tagInfo}"
                }
            }
        }

        stage('🔍 Get DockerHub Tags List') {
            when {
                expression { return !params.SKIP_DOCKERHUB }
            }
            steps {
                script {
                    def tagsList = sh(
                        script: """
                            curl -s https://hub.docker.com/v2/repositories/justendray/feedback_app/tags?page_size=5 | jq -r '.results[] | "\\(.name) | \\(.last_updated)"' | paste -sd ';' -
                        """,
                        returnStdout: true
                    ).trim()
                    echo "Останні теги у DockerHub: ${tagsList}"
                }
            }
        }

        stage('✅ Validate Parameters') {
            steps {
                script {
                    if (!params.EC2_IP) {
                        error("❌ Не вказано IP адресу EC2 інстансу")
                    }
                    
                    if (params.FORCE_ROLLBACK) {
                        echo "🔄 Режим примусового ролбеку з DockerHub активовано"
                    }
                    
                    echo "✅ Параметри валідні. Розгортання на: ${params.EC2_IP}"
                }
            }
        }

        stage('🔄 Force Rollback from DockerHub') {
            when {
                expression { return params.FORCE_ROLLBACK }
            }
            steps {
                script {
                    def rollbackTag = params.ROLLBACK_TAG?.trim() ? params.ROLLBACK_TAG.trim() : 'latest'
                    echo "🔄 Виконуємо ролбек на тег: ${rollbackTag}"
                    sh """
                        ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_IP} '
                            set -e
                            cd ${DEPLOY_DIR}
                            docker-compose -f ${COMPOSE_FILE} down || true
                            echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                            docker pull justendray/feedback_app:${rollbackTag}
                            echo "DOCKER_IMAGE=justendray/feedback_app:${rollbackTag}" > .env
                            echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> .env
                            echo "SECRET_KEY=${SECRET_KEY}" >> .env
                            IMAGE_TAG=${rollbackTag} docker-compose -f ${COMPOSE_FILE} up -d
                            echo "✅ Ролбек завершено. Запущено образ з тегом: ${rollbackTag}"
                        '
                    """
                }
            }
        }

        stage('📦 Prepare Source Code') {
            when {
                expression { return !params.FORCE_ROLLBACK }
            }
            steps {
                script {
                    echo "📦 Підготовка вихідного коду..."

                    sh """
                        # Створення тимчасової директорії
                        TEMP_DIR=\$(mktemp -d)
                        echo "📁 Створення тимчасової директорії: \${TEMP_DIR}"
                        
                        # Копіювання файлів у тимчасову директорію
                        echo "📋 Копіювання файлів..."
                        rsync -av --exclude='.git' \
                            --exclude='*.tar.gz' \
                            --exclude='*.log' \
                            --exclude='__pycache__' \
                            --exclude='.pytest_cache' \
                            --exclude='venv' \
                            --exclude='.venv' \
                            --exclude='\${workspace}' \
                            --exclude='\${workspace}@tmp' \
                            --exclude='app@tmp' \
                            . \${TEMP_DIR}/
                        
                        # Створення архіву
                        echo "📦 Створення архіву..."
                        cd \${TEMP_DIR}
                        tar -czf \${WORKSPACE}/feedback-app-source-${env.BUILD_NUMBER}.tar.gz .
                        cd \${WORKSPACE}
                        
                        # Перевірка архіву
                        echo "📋 Перевірка включення необхідних файлів:"
                        tar -tzf feedback-app-source-${env.BUILD_NUMBER}.tar.gz | grep -E "(init_db.py|create_admin_user.py)" || true
                        
                        echo "📊 Розмір архіву:"
                        ls -lh feedback-app-source-${env.BUILD_NUMBER}.tar.gz
                        
                        # Перевірка існування архіву
                        if [ ! -f feedback-app-source-${env.BUILD_NUMBER}.tar.gz ]; then
                            echo "❌ Архів не створено!"
                            exit 1
                        fi
                        
                        # Очищення тимчасової директорії
                        rm -rf \${TEMP_DIR}
                    """
                }
            }
        }

        stage('🚀 Transfer Files to EC2') {
            steps {
                script {
                    echo "🚀 Передача файлів на EC2..."

                    // Перевірка місця на диску та прав доступу
                    sh """
                        echo "🔍 Перевірка місця на диску та прав доступу..."
                        ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_IP} '
                            echo "📊 Стан диску:"
                            df -h
                            
                            echo "📊 Вільне місце в /tmp:"
                            df -h /tmp
                            
                            echo "🔑 Права доступу до /tmp:"
                            ls -la /tmp
                            
                            echo "🧹 Очищення /tmp..."
                            sudo rm -rf /tmp/* || true
                            
                            echo "📊 Стан диску після очищення:"
                            df -h
                            
                            echo "🔑 Перевірка прав на запис:"
                            touch /tmp/test_write && rm /tmp/test_write && echo "✅ Права на запис OK" || echo "❌ Немає прав на запис"
                        '
                    """

                    sh """
                        echo "📤 Копіювання архіву на EC2..."
                        scp -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no \
                            feedback-app-source-${env.BUILD_NUMBER}.tar.gz \
                            ${params.EC2_USER}@${params.EC2_IP}:/tmp/

                        echo "✅ Файли передано на EC2"
                    """
                }
            }
        }

        stage('🔧 Setup EC2 Environment') {
            steps {
                script {
                    echo "🔧 Налаштування середовища EC2..."
                    sh """
                        ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_IP} '
                            set -e
                            
                            echo "🔧 Підготовка робочої директорії..."
                            
                            # Створення робочої директорії
                            sudo mkdir -p ${DEPLOY_DIR}
                            sudo chown -R ${EC2_USER}:${EC2_USER} ${DEPLOY_DIR}
                            cd ${DEPLOY_DIR}
                            
                            # Очищення старих файлів
                            rm -rf * .* 2>/dev/null || true
                            
                            # Розпакування нового коду
                            echo "📦 Розпакування вихідного коду..."
                            tar -xzf /tmp/feedback-app-source-${env.BUILD_NUMBER}.tar.gz
                            
                            # Видалення тимчасового архіву
                            rm -f /tmp/feedback-app-source-${env.BUILD_NUMBER}.tar.gz
                            
                            # Надання прав виконання для скриптів
                            chmod +x init_db.py 2>/dev/null || true
                            chmod +x create_admin_user.py 2>/dev/null || true
                            
                            # Надання прав на logs для nginx
                            sudo mkdir -p logs
                            sudo chown 101:101 logs
                            sudo chmod 775 logs
                            
                            echo "✅ Середовище EC2 налаштовано"
                        '
                    """
                }
            }
        }

        stage('🐳 Setup Docker Environment') {
            steps {
                script {
                    echo "🐳 Налаштування Docker середовища..."

                    sh """
                        ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_IP} '
                            set -e
                            cd ${DEPLOY_DIR}

                            # Перевірка та встановлення Docker
                            if ! command -v docker &> /dev/null; then
                                echo "🐳 Встановлення Docker..."
                                sudo apt-get update
                                sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
                                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                                echo "deb [arch=\$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                                sudo apt-get update
                                sudo apt-get install -y docker-ce docker-ce-cli containerd.io
                                sudo systemctl start docker
                                sudo systemctl enable docker
                                sudo usermod -aG docker \$(whoami)
                            fi

                            # Перевірка та встановлення Docker Compose
                            if ! command -v docker-compose &> /dev/null; then
                                echo "🔧 Встановлення Docker Compose..."
                                DOCKER_COMPOSE_VERSION=\$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep "tag_name" | cut -d\\" -f4)
                                sudo curl -L "https://github.com/docker/compose/releases/download/\${DOCKER_COMPOSE_VERSION}/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
                                sudo chmod +x /usr/local/bin/docker-compose
                            fi

                            # Очищення при примусовій перезбірці
                            if [ "${params.FORCE_REBUILD}" = "true" ]; then
                                echo "🗑️ Очищення Docker кешу..."
                                docker system prune -f || true
                                docker images | grep "${APP_NAME}" | awk '{print \$3}' | xargs -r docker rmi -f || true
                            fi

                            echo "✅ Docker середовище налаштовано"
                        '
                    """
                }
            }
        }

        stage('🏗️ Build Application') {
            steps {
                script {
                    echo "🏗️ Збірка застосунку..."

                    // Очищення диску перед збіркою
                    sh """
                        echo "🧹 Очищення диску перед збіркою..."
                        
                        # Очищення Docker
                        echo "🗑️ Очищення Docker..."
                        docker system prune -af --volumes || true
                        
                        # Очищення кешу apt
                        echo "🧹 Очищення apt кешу..."
                        sudo apt-get clean || true
                        sudo apt-get autoremove -y || true
                        
                        # Очищення логів
                        echo "📋 Очищення логів..."
                        sudo find /var/log -type f -name "*.log" -exec truncate -s 0 {} \\; || true
                        sudo find /var/log -type f -name "*.gz" -delete || true
                        sudo journalctl --vacuum-time=1d || true
                        
                        # Очищення тимчасових файлів
                        echo "🗑️ Очищення тимчасових файлів..."
                        sudo rm -rf /tmp/* || true
                        sudo rm -rf /var/tmp/* || true
                        
                        # Очищення кешу pip
                        echo "🧹 Очищення pip кешу..."
                        sudo rm -rf ~/.cache/pip || true
                        
                        # Очищення кешу npm
                        echo "🧹 Очищення npm кешу..."
                        sudo rm -rf ~/.npm || true
                        
                        # Очищення кешу yarn
                        echo "🧹 Очищення yarn кешу..."
                        sudo rm -rf ~/.yarn || true
                        
                        # Очищення кешу composer
                        echo "🧹 Очищення composer кешу..."
                        sudo rm -rf ~/.composer || true
                        
                        # Очищення кешу maven
                        echo "🧹 Очищення maven кешу..."
                        sudo rm -rf ~/.m2 || true
                        
                        # Очищення кешу gradle
                        echo "🧹 Очищення gradle кешу..."
                        sudo rm -rf ~/.gradle || true
                        
                        # Очищення кешу sbt
                        echo "🧹 Очищення sbt кешу..."
                        sudo rm -rf ~/.sbt || true
                        
                        # Очищення кешу cargo
                        echo "🧹 Очищення cargo кешу..."
                        sudo rm -rf ~/.cargo || true
                        
                        # Очищення кешу go
                        echo "🧹 Очищення go кешу..."
                        sudo rm -rf ~/go/pkg || true
                        
                        # Очищення кешу rust
                        echo "🧹 Очищення rust кешу..."
                        sudo rm -rf ~/.rustup || true
                        
                        # Очищення кешу node
                        echo "🧹 Очищення node кешу..."
                        sudo rm -rf ~/.node-gyp || true
                        
                        # Очищення кешу python
                        echo "🧹 Очищення python кешу..."
                        sudo find / -type d -name "__pycache__" -exec rm -rf {} + || true
                        sudo find / -type d -name "*.pyc" -delete || true
                        
                        # Очищення кешу systemd
                        echo "🧹 Очищення systemd кешу..."
                        sudo systemctl daemon-reload || true
                        sudo systemctl reset-failed || true
                        
                        # Очищення кешу journald
                        echo "🧹 Очищення journald кешу..."
                        sudo journalctl --vacuum-time=1d || true
                        
                        # Очищення кешу snap
                        echo "🧹 Очищення snap кешу..."
                        sudo snap list --all | awk '/disabled/{print \$1, \$3}' | while read snapname revision; do sudo snap remove "\$snapname" --revision="\$revision"; done || true
                        
                        # Показуємо стан диску після очищення
                        echo "📊 Стан диску після очищення:"
                        df -h
                    """

                    // Підготовка аргументів збірки
                    def buildDate = sh(
                        script: 'date -u +"%Y-%m-%dT%H:%M:%SZ"',
                        returnStdout: true
                    ).trim()

                    // Створення .dockerignore для зменшення контексту
                    sh """
                        echo "📝 Створення .dockerignore..."
                        cat > .dockerignore << 'EOL'
                        .git
                        .gitignore
                        .env
                        *.pyc
                        __pycache__
                        .pytest_cache
                        venv
                        .venv
                        *.log
                        *.tar.gz
                        Jenkinsfile
                        README.md
                        monitoring/
                        nginx/
                        EOL
                    """

                    // Збірка Docker образу на Jenkins з оптимізованими налаштуваннями
                    sh """
                        echo "🔨 Збірка Docker образу..."
                        DOCKER_BUILDKIT=1 docker build \\
                            --no-cache \\
                            --progress=plain \\
                            --memory=4g \\
                            --memory-swap=4g \\
                            -t ${APP_NAME}:${env.BUILD_NUMBER} \\
                            -t ${APP_NAME}:latest \\
                            --build-arg BUILD_DATE="${buildDate}" \\
                            --build-arg BUILD_NUMBER="${env.BUILD_NUMBER}" \\
                            .

                        echo "✅ Збірка завершена"
                    """
                }
            }
        }

        stage('🚀 Deploy Application') {
            steps {
                script {
                    echo "🚀 Розгортання застосунку..."

                    // Пушимо образ на DockerHub перед деплоєм
                    withCredentials([usernamePassword(credentialsId: 'dockerhub_push', usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_PASS')]) {
                        sh """
                            docker login -u $DOCKERHUB_USER -p $DOCKERHUB_PASS
                            docker tag ${APP_NAME}:${env.BUILD_NUMBER} justendray/feedback_app:${env.BUILD_NUMBER}
                            docker tag ${APP_NAME}:${env.BUILD_NUMBER} justendray/feedback_app:latest
                            docker push justendray/feedback_app:${env.BUILD_NUMBER}
                            docker push justendray/feedback_app:latest
                        """
                    }

                    // Деплой на EC2 через pull з DockerHub
                    sh """
                        ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_IP} '
                            set -e
                            cd ${DEPLOY_DIR}

                            # Зберігаємо поточну версію перед розгортанням
                            if [ -f "${COMPOSE_FILE}" ]; then
                                echo "📦 Збереження поточної версії..."
                                docker-compose -f ${COMPOSE_FILE} ps | grep ${APP_NAME} | awk "{print \$2}" | cut -d: -f2 > ${BACKUP_FILE}
                            fi

                            echo "🚀 Запуск застосунку через Docker Compose..."

                            # Створюємо .env файл з змінними середовища
                            echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" > .env
                            echo "SECRET_KEY=${SECRET_KEY}" >> .env
                            echo "BUILD_NUMBER=${BUILD_NUMBER}" >> .env
                            echo "DOCKER_IMAGE=justendray/feedback_app:${env.BUILD_NUMBER}" >> .env

                            # Завантажуємо образ з DockerHub
                            echo "📥 Завантаження Docker образу з DockerHub..."
                            echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                            docker pull justendray/feedback_app:${env.BUILD_NUMBER}

                            # Запуск через Docker Compose
                            echo "🚀 Запуск контейнерів..."
                            docker-compose -f docker-compose.prod.yml up -d

                            # Чекаємо 10 секунд для ініціалізації
                            echo "⏳ Чекаємо 10 секунд для ініціалізації..."
                            sleep 10

                            # Перевірка статусу контейнерів
                            echo "📊 Статус контейнерів:"
                            docker-compose -f docker-compose.prod.yml ps

                            # Перевірка логів бази даних
                            echo "📋 Логи бази даних:"
                            docker-compose -f docker-compose.prod.yml logs db

                            # Перевірка доступності бази даних
                            echo "🔍 Перевірка доступності бази даних:"
                            docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres -d feedback || true

                            echo "✅ Розгортання завершено"
                        '
                    """
                }
            }
        }

        stage('📊 Final Status Check') {
            steps {
                script {
                    echo "📊 Перевірка фінального статусу..."

                    sh """
                        ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no \
                            ${params.EC2_USER}@${params.EC2_IP} \
                            '
                            cd \${DEPLOY_DIR}
                            echo "📊 Статус контейнерів:"
                            docker-compose -f \${COMPOSE_FILE} ps

                            echo "🔍 Перевірка портів:"
                            netstat -tlnp | grep -E ":(80|5000|5432)" || echo "Порти не прослуховуються"
                            '
                    """
                }
            }
        }
    }

    post {
        always {
            script {
                echo "🧹 Очищення тимчасових файлів на Jenkins..."
                sh """
                    rm -f feedback-app-source-${env.BUILD_NUMBER}.tar.gz || true
                """
            }
        }

        failure {
            script {
                echo "⚠️ Розгортання не вдалося. Запуск ролбеку з DockerHub..."
                def rollbackTag = params.ROLLBACK_TAG?.trim() ? params.ROLLBACK_TAG.trim() : 'latest'
                sh """
                    ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_IP} '
                        set -e
                        cd ${DEPLOY_DIR}
                        docker-compose -f ${COMPOSE_FILE} down || true
                        echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                        docker pull justendray/feedback_app:${rollbackTag}
                        # Створюємо .env з усіма змінними
                        echo "DOCKER_IMAGE=justendray/feedback_app:${rollbackTag}" > .env
                        echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> .env
                        echo "SECRET_KEY=${SECRET_KEY}" >> .env
                        IMAGE_TAG=${rollbackTag} docker-compose -f ${COMPOSE_FILE} up -d
                        echo "✅ Ролбек завершено. Запущено образ з тегом: ${rollbackTag}"
                        echo "\n📊 Статус контейнерів після ролбеку:"
                        docker-compose -f ${COMPOSE_FILE} ps
                        echo "\n📋 Логи web-контейнера (останні 20 рядків):"
                        docker-compose -f ${COMPOSE_FILE} logs --tail=20 web || true
                        echo "\n📋 Логи db-контейнера (останні 20 рядків):"
                        docker-compose -f ${COMPOSE_FILE} logs --tail=20 db || true
                        echo "\n🔗 Доступні сервіси після ролбеку:"
                        echo "• Головний сайт:   http://${EC2_IP}"
                        echo "• Prometheus:      http://${EC2_IP}:9090"
                        echo "• Grafana:         http://${EC2_IP}:3000"
                    '
                """
                echo "\n⚠️ Основний деплой не вдався, але rollback виконано успішно!"
                echo "✅ Сайт і моніторинг підняті з DockerHub. Перевірте роботу сервісів вручну за посиланнями вище."
            }
        }

        success {
            script {
                echo "🎉 Розгортання успішно завершено!"

                def publicIp = ""
                try {
                    publicIp = sh(
                        script: """
                            ssh -i ${AWS_SSH_KEY} -o StrictHostKeyChecking=no \
                                ${params.EC2_USER}@${params.EC2_IP} \
                                'curl -s http://checkip.amazonaws.com 2>/dev/null || echo ${params.EC2_IP}'
                        """,
                        returnStdout: true
                    ).trim()
                } catch (Exception e) {
                    publicIp = params.EC2_IP
                }

                def tagInfo = "Пропущено (SKIP_DOCKERHUB=true)"
                def tagsList = "Пропущено (SKIP_DOCKERHUB=true)"

                if (!params.SKIP_DOCKERHUB) {
                    // Отримуємо інформацію про теги DockerHub
                    tagInfo = sh(
                        script: """
                            curl -s https://hub.docker.com/v2/repositories/justendray/feedback_app/tags?page_size=1 | jq -r '.results[0] | "Тег: \\(.name), Дата: \\(.last_updated)"'
                        """,
                        returnStdout: true
                    ).trim()

                    tagsList = sh(
                        script: """
                            curl -s https://hub.docker.com/v2/repositories/justendray/feedback_app/tags?page_size=5 | jq -r '.results[] | "\\(.name) | \\(.last_updated)"' | paste -sd ';' -
                        """,
                        returnStdout: true
                    ).trim()
                }

                echo """
🎉 РОЗГОРТАННЯ УСПІШНО ЗАВЕРШЕНО!

📊 Інформація про розгортання:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Додаток: http://${publicIp}
🔐 Адмін панель: http://${publicIp}/feedback_page
🏥 Health Check: http://${publicIp}/health
🔍 Prometheus: http://${publicIp}:9090
🔍 Grafana: http://${publicIp}:3000

🔧 Деталі збірки:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Номер збірки: ${env.BUILD_NUMBER}
• EC2 IP: ${params.EC2_IP}
• DockerHub: ${params.SKIP_DOCKERHUB ? 'Пропущено' : 'Оновлено'}

🐳 DockerHub інформація:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Останній тег: ${tagInfo}
• Доступні теги:
${tagsList.split(';').collect { "  - ${it}" }.join('\n')}

🛠️ Команди для управління на EC2:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ssh -i your-key.pem ${params.EC2_USER}@${params.EC2_IP}
cd ${DEPLOY_DIR}

• Статус: docker-compose -f ${COMPOSE_FILE} ps
• Логи: docker-compose -f ${COMPOSE_FILE} logs
• Перезапуск: docker-compose -f ${COMPOSE_FILE} restart
• Зупинка: docker-compose -f ${COMPOSE_FILE} down
• Очищення: docker system prune -f

⚠️  ВАЖЛИВО: Перевірте Security Groups EC2!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Моніторинг та діагностика:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Перевірка логів Flask: docker-compose -f ${COMPOSE_FILE} logs flask
• Перевірка логів DB: docker-compose -f ${COMPOSE_FILE} logs postgres
• Статистика контейнерів: docker stats
• Вільне місце: df -h
• Перевірка портів: netstat -tulpn | grep -E ":(80|443|5000|5432|9090|3000)"

📅 Дата розгортання: ${new Date().format('yyyy-MM-dd HH:mm:ss')}
"""
            }
        }
    }
}