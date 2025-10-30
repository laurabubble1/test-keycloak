#!/bin/bash
# Dockerized Locust Runner Script
# Usage: docker compose up -d --scale locust-worker=(nb of workers) ./alt_run_load_test.sh (light|medium|heavy|stress|all)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/test_results"
mkdir -p "$RESULTS_DIR"

timestamp=$(date +"%Y%m%d_%H%M%S")

run_scenario() {
    local scenario_name=$1
    local users=$2
    local spawn_rate=$3
    local run_time=$4

    echo "=================================================="
    echo "Running $scenario_name"
    echo "Users: $users, Spawn Rate: $spawn_rate, Duration: $run_time"
    echo "=================================================="

    docker exec -it locust-master locust \
        -f /mnt/locust/locustfile.py \
        --host http://host.docker.internal:8080 \
        --headless \
        -u $users \
        -r $spawn_rate \
        -t $run_time \
        --html /mnt/locust/test_results/${scenario_name}_${timestamp}.html \
        --csv /mnt/locust/test_results/${scenario_name}_${timestamp} \
        > "$RESULTS_DIR/${scenario_name}_${timestamp}_master.log" 2>&1

    echo "✅ $scenario_name complete. Results saved to: $RESULTS_DIR/${scenario_name}_${timestamp}.html"
    echo ""
}

if ! docker ps | grep -q locust-master; then
    echo "⚠️ Locust master container not running. Starting Docker Compose..."
    docker-compose up -d locust-master locust-worker
    sleep 10
fi

case "$1" in
    "light"|"20")
        run_scenario "light_load" 20 2 "5m"
        ;;
    "medium"|"100")
        run_scenario "medium_load" 100 5 "10m"
        ;;
    "heavy"|"500")
        run_scenario "heavy_load" 500 10 "15m"
        ;;
    "stress"|"2000")
        run_scenario "stress_test" 2000 20 "20m"
        ;;
    "all")
        run_scenario "light_load" 20 2 "5m"
        echo "Cooling down for 30 seconds..."
        sleep 30
        run_scenario "medium_load" 100 5 "10m"
        echo "Cooling down for 30 seconds..."
        sleep 30
        run_scenario "heavy_load" 500 10 "15m"
        echo "Cooling down for 30 seconds..."
        sleep 30
        run_scenario "stress_test" 2000 20 "20m"
        ;;
    *)
        echo "Usage: $0 [light|medium|heavy|stress|all]"
        ;;
esac