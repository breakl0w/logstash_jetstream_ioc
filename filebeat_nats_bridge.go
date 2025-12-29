// filebeat_nats_bridge.go
package main

import (
    "encoding/json"
    "log"
    "net/http"
    "github.com/nats-io/nats.go"
)

type IoC struct {
    Value      string   `json:"value"`
    Type       string   `json:"type"`
    ThreatType string   `json:"threat_type"`
    Source     string   `json:"source"`
    Confidence int      `json:"confidence"`
    Timestamp  string   `json:"timestamp"`
    Tags       []string `json:"tags"`
}

func main() {
    // Подключение к NATS
    nc, err := nats.Connect("nats://localhost:4222")
    if err != nil {
        log.Fatal(err)
    }
    defer nc.Close()
    
    js, err := nc.JetStream()
    if err != nil {
        log.Fatal(err)
    }
    
    // HTTP endpoint для приема данных от Filebeat
    http.HandleFunc("/ioc", func(w http.ResponseWriter, r *http.Request) {
        var ioc IoC
        if err := json.NewDecoder(r.Body).Decode(&ioc); err != nil {
            http.Error(w, err.Error(), http.StatusBadRequest)
            return
        }
        
        // Публикация в NATS
        subject := "ioc." + ioc.Type
        data, _ := json.Marshal(ioc)
        
        _, err := js.Publish(subject, data)
        if err != nil {
            http.Error(w, err.Error(), http.StatusInternalServerError)
            return
        }
        
        log.Printf("Published IoC: %s to %s", ioc.Value, subject)
        w.WriteHeader(http.StatusOK)
    })
    
    log.Println("Listening on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
