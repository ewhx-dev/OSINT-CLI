FROM golang:1.20-bullseye

WORKDIR /app

COPY services/gateway /app

RUN go build -o gateway main.go

EXPOSE 8080

CMD ["./gateway"]