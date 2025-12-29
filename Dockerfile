FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY nats_logstash_bridge.go ./
RUN go build -o nats-bridge

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/nats-bridge .
CMD ["./nats-bridge"]
