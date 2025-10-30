#!/bin/bash
# Control script for two-Docker setup

case "$1" in
    "start-target")
        echo "Starting Target System (Keycloak + Monitoring)..."
        # Clean up any existing network issues first
        docker-compose -f docker-compose-target.yml down 2>/dev/null || true
        docker-compose -f docker-compose-target.yml up -d
        if [ $? -eq 0 ]; then
            echo "Target system running:"
            echo "   - Keycloak: http://localhost:8080"
            echo "   - Keycloak Metrics: http://localhost:9000/metrics"
            echo "   - Prometheus: http://localhost:9090"
            echo "   - Grafana: http://localhost:3000"
            echo "   - Netdata: http://localhost:19999"
        else
            echo "Failed to start target system"
        fi
        ;;
    
    "start-locust")
        echo "🔫 Starting Load Generator (Locust)..."
        # Clean up any existing network issues first
        docker-compose -f docker-compose-locust.yml down 2>/dev/null || true
        docker-compose -f docker-compose-locust.yml up -d
        if [ $? -eq 0 ]; then
            echo "Load generator running:"
            echo "   - Locust Web: http://localhost:8089"
        else
            echo "Failed to start load generator"
        fi
        ;;
    
    "stop-target")
        echo "Stopping Target System..."
        docker-compose -f docker-compose-target.yml down
        ;;
        
    "stop-locust")
        echo "Stopping Load Generator..."
        docker-compose -f docker-compose-locust.yml down
        ;;
        
    "status")
        echo "Target System Status:"
        docker-compose -f docker-compose-target.yml ps
        echo ""
        echo "Load Generator Status:"
        docker-compose -f docker-compose-locust.yml ps
        ;;
        
    "logs-target")
        docker-compose -f docker-compose-target.yml logs -f keycloak
        ;;
        
    "logs-locust")
        docker-compose -f docker-compose-locust.yml logs -f locust-master
        ;;
        
    "restart-all")
        echo "Restarting everything..."
        docker-compose -f docker-compose-target.yml down
        docker-compose -f docker-compose-locust.yml down
        sleep 2
        docker-compose -f docker-compose-target.yml up -d
        sleep 5
        docker-compose -f docker-compose-locust.yml up -d
        ;;
        
    *)
        echo "Two-Docker Performance Testing Setup"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start-target    Start Keycloak + Monitoring stack"
        echo "  start-locust    Start Locust load generator"
        echo "  stop-target     Stop target system"
        echo "  stop-locust     Stop load generator"
        echo "  status          Show status of both systems"
        echo "  logs-target     Show Keycloak logs"
        echo "  logs-locust     Show Locust logs"
        echo "  restart-all     Restart everything"
        echo ""
        echo "Typical workflow:"
        echo "  1. $0 start-target"
        echo "  2. Wait for Keycloak to start (check logs)"
        echo "  3. $0 start-locust" 
        echo "  4. Open http://localhost:8089 for load testing"
        echo "  5. Open http://localhost:3000 for monitoring"
        ;;
esac