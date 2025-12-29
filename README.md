Установка зависимостей для паблишера:

pip install nats-py

Запуск:
python publish_ioc.py


Так как у Logstash нет нативного NATS input, нам нужно создать мост -

# Компиляция
go mod init nats-bridge
go get github.com/nats-io/nats.go
go build -o nats-bridge nats_logstash_bridge.go
