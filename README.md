Установка зависимостей для паблишера:

pip install nats-py

Запуск:
python publish_ioc.py


Так как у Logstash нет нативного NATS input, нам нужно создать мост -

# Компиляция
go mod init nats-bridge
go get github.com/nats-io/nats.go
go build -o nats-bridge nats_logstash_bridge.go

проверка:

nats stream info IOC_STREAM

# Проверка consumer
nats consumer info IOC_STREAM logstash-consumer

# Одиночный IoC
curl -X POST http://localhost:8000/api/v1/ioc \
  -H "Content-Type: application/json" \
  -d '{
    "value": "192.168.1.100",
    "type": "ip",
    "threat_type": "malware",
    "source": "manual",
    "confidence": 90,
    "tags": ["c2", "botnet"]
  }'

# Массовая загрузка
curl -X POST http://localhost:8000/api/v1/ioc/bulk \
  -H "Content-Type: application/json" \
  -d '[
    {"value": "evil.com", "type": "domain", "threat_type": "phishing", "source": "feed", "confidence": 85},
    {"value": "bad.ip.address", "type": "ip", "threat_type": "scanner", "source": "feed", "confidence": 70}
  ]
