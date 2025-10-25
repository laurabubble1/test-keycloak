#!/bin/bash
# Quick test scenario scripts for manual execution

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/test_results"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Function to run a test scenario
run_scenario() {
    local scenario_name=$1
    local users=$2
    local spawn_rate=$3
    local run_time=$4
    
    echo "=================================================="
    echo "Running $scenario_name"
    echo "Users: $users, Spawn Rate: $spawn_rate, Duration: $run_time"
    echo "=================================================="
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    
    locust \
        -f "$SCRIPT_DIR/locustfile.py" \
        --host "http://localhost:8080" \
        --users $users \
        --spawn-rate $spawn_rate \
        --run-time $run_time \
        --html "$RESULTS_DIR/${scenario_name}_${timestamp}.html" \
        --csv "$RESULTS_DIR/${scenario_name}_${timestamp}" \
        --headless \
        --print-stats
    
    echo "Results saved to: $RESULTS_DIR/${scenario_name}_${timestamp}.html"
    echo ""
}

# Check if specific scenario is requested
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
        echo "Running all scenarios with cool-down periods..."
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
        echo ""
        echo "Available scenarios:"
        echo "  light (20):    20 users, 2 spawn/sec, 5 minutes"
        echo "  medium (100):  100 users, 5 spawn/sec, 10 minutes"
        echo "  heavy (500):   500 users, 10 spawn/sec, 15 minutes"
        echo "  stress (2000): 2000 users, 20 spawn/sec, 20 minutes"
        echo "  all:           Run all scenarios sequentially"
        exit 1
        ;;
esac