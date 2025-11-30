package main

import (
	"log"
	"net/http"
	"time"
	"io"
	"net/url"
	"sync"
	"strings"
)

const pythonServiceHost = "http://localhost:8001" 

type Client struct {
	lastRequest time.Time
}

var clients = make(map[string]*Client)
var mu sync.Mutex

const rateLimitDuration = 3 * time.Second 

func getClientIP(r *http.Request) string {

    if ip := r.Header.Get("X-Forwarded-For"); ip != "" {

        parts := strings.Split(ip, ",")
        return strings.TrimSpace(parts[0])
    }
    return r.RemoteAddr
}

func rateLimitMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ip := getClientIP(r)
		mu.Lock()
		defer mu.Unlock()

		client, exists := clients[ip]
		now := time.Now()

		if !exists {
			clients[ip] = &Client{lastRequest: now}
			next(w, r)
			return
		}

		if now.Sub(client.lastRequest) < rateLimitDuration {
		
			http.Error(w, "429 Too Many Requests: Rate limit exceeded. Try again later.", http.StatusTooManyRequests)
			return
		}

		client.lastRequest = now
		next(w, r)
	}
}


func handleAnalysis(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	target := r.URL.Query().Get("target")
	if target == "" {
		http.Error(w, "Query parameter 'target' is required.", http.StatusBadRequest)
		return
	}

	pythonURL, err := url.Parse(pythonServiceHost + "/analyze")
	if err != nil {
		log.Printf("Error parsing URL: %v", err)
		http.Error(w, "Internal configuration error", http.StatusInternalServerError)
		return
	}

	q := pythonURL.Query()
	q.Set("target", target)
	pythonURL.RawQuery = q.Encode()

	client := http.Client{
		Timeout: 40 * time.Second, 
	}

	resp, err := client.Get(pythonURL.String())
	if err != nil {
		log.Printf("Error contacting Python service: %v", err)
		http.Error(w, "503 Service Unavailable (Python backend timeout or error)", http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)

	if _, err := io.Copy(w, resp.Body); err != nil {
		log.Printf("Error writing response to client: %v", err)
	}
}

func main() {
	http.HandleFunc("/analyze", rateLimitMiddleware(handleAnalysis))

	log.Println("Go API Gateway (Rate Limited) listening on :8080. Proxying requests to Python on :8001")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal("ListenAndServe failed: ", err)
	}
}