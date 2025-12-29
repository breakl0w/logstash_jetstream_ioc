// nats_logstash_bridge.go
package main

import (
    "bytes"
    "encoding/json"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    
    "github.com/nats-io/nats.go"
)

func main() {
    // Подключение к NATS
    nc, err := nats.Connect(getEnv("NATS_URL", "nats://localhost:4222"))
    if err != nil {
        log.Fatal(err)
    }
    defer nc.Close()
    
    js, err := nc.JetStream()
    if err != nil {
        log.Fatal(err)
    }
    
    logstashURL := getEnv("LOGSTASH_URL", "http://localhost:8080")
    
    // Подписка на все IoC
    _, err = js.Subscribe("ioc.>", func(msg *nats.Msg) {
        log.Printf("Received from %s: %s", msg.Subject, string(msg.Data))
        
        // Отправка в Logstash HTTP input
        resp, err := http.Post(
            logstashURL,
            "application/json",
            bytes.NewBuffer(msg.Data),
        )
        
        if err != nil {
            log.Printf("Error sending to Logstash: %v", err)
            return
        }
        defer resp.Body.Close()
        
        if resp.StatusCode == 200 {
            msg.Ack()
            log.Printf("✓ Forwarded to Logstash and ACKed")
        } else {
            log.Printf("✗ Logstash returned: %d", resp.StatusCode)
        }
    }, nats.Durable("logstash-consumer"), nats.ManualAck())
    
    if err != nil {
        log.Fatal(err)
    }
    
    log.Println("🚀 Bridge started, waiting for messages...")
    
    // Graceful shutdown
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
    <-sigChan
    
    log.Println("Shutting down...")
}

func getEnv(key, fallback string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return fallback
}
