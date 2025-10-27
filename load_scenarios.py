#!/usr/bin/env python3
"""
Keycloak Load Testing Scenarios
Automates running different load scenarios with varying user counts
"""

import subprocess
import time
import os
import sys
import json
from datetime import datetime

class LoadTestRunner:
    def __init__(self):
        base_dir = os.getcwd()
        self.results_dir = f"{base_dir}/test_results"
        self.scenarios = {
            "light_load": {"users": 20, "spawn_rate": 2, "run_time": "5m"},
            "medium_load": {"users": 100, "spawn_rate": 5, "run_time": "10m"},
            "heavy_load": {"users": 500, "spawn_rate": 10, "run_time": "15m"},
            "stress_test": {"users": 2000, "spawn_rate": 20, "run_time": "20m"}
        }
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_scenario(self, scenario_name, scenario_config):
        """Run a specific load test scenario"""
        print(f"\n{'='*60}")
        print(f"Running {scenario_name.upper()} scenario")
        print(f"Users: {scenario_config['users']}, Spawn Rate: {scenario_config['spawn_rate']}")
        print(f"Duration: {scenario_config['run_time']}")
        print(f"{'='*60}")
        
        # Create timestamp for this test run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"{self.results_dir}/{scenario_name}_{timestamp}.html"
        
        # Build locust command
        cmd = [
            "locust",
            "-f", f"{self.base_dir}/locustfile.py",
            "--host", "http://localhost:8080",
            "--users", str(scenario_config['users']),
            "--spawn-rate", str(scenario_config['spawn_rate']),
            "--run-time", scenario_config['run_time'],
            "--html", result_file,
            "--headless",
            "--print-stats",
            "--csv", f"{self.results_dir}/{scenario_name}_{timestamp}"
        ]
        
        print(f"Command: {' '.join(cmd)}")
        print("Starting test...")
        
        try:
            # Run the test
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode == 0:
                print(f"✅ {scenario_name} completed successfully!")
                print(f"Results saved to: {result_file}")
            else:
                print(f"❌ {scenario_name} failed!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running {scenario_name}: {e}")
            return False
    
    def wait_for_keycloak(self, max_attempts=30):
        """Wait for Keycloak to be ready"""
        import requests
        
        print("Waiting for Keycloak to be ready...")
        for i in range(max_attempts):
            try:
                response = requests.get("http://localhost:8080/realms/master", timeout=5)
                if response.status_code == 200:
                    print("✅ Keycloak is ready!")
                    return True
            except:
                pass
            
            print(f"Attempt {i+1}/{max_attempts}... waiting 10 seconds")
            time.sleep(10)
        
        print("❌ Keycloak is not responding")
        return False
    
    def start_monitoring(self):
        """Start monitoring services"""
        print("Starting monitoring services...")
        cmd = ["docker-compose", "up", "-d", "prometheus", "grafana", "node-exporter", "netdata"]
        subprocess.run(cmd, cwd=self.base_dir)
        print("Monitoring services started")
        time.sleep(10)  # Wait for services to initialize
    
    def run_all_scenarios(self):
        """Run all load test scenarios"""
        print("🚀 Starting Keycloak Load Testing Suite")
        print(f"Results will be saved in: {self.results_dir}")
        
        # Ensure monitoring is running
        self.start_monitoring()
        
        # Wait for Keycloak to be ready
        if not self.wait_for_keycloak():
            print("❌ Keycloak is not ready. Please start Keycloak and try again.")
            return False
        
        results = {}
        
        for scenario_name, config in self.scenarios.items():
            print(f"\n⏳ Preparing for {scenario_name}...")
            time.sleep(30)  # Cool-down period between tests
            
            success = self.run_scenario(scenario_name, config)
            results[scenario_name] = success
            
            if success:
                print(f"✅ {scenario_name} completed")
            else:
                print(f"❌ {scenario_name} failed")
        
        # Print summary
        print(f"\n{'='*60}")
        print("TEST SUITE SUMMARY")
        print(f"{'='*60}")
        
        for scenario, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{scenario:<15} {status}")
        
        print(f"\nResults location: {self.results_dir}")
        return all(results.values())

def main():
    if len(sys.argv) > 1:
        scenario_name = sys.argv[1]
        runner = LoadTestRunner()
        
        if scenario_name == "all":
            runner.run_all_scenarios()
        elif scenario_name in runner.scenarios:
            runner.start_monitoring()
            if runner.wait_for_keycloak():
                runner.run_scenario(scenario_name, runner.scenarios[scenario_name])
            else:
                print("Keycloak not ready")
        else:
            print(f"Unknown scenario: {scenario_name}")
            print(f"Available scenarios: {', '.join(runner.scenarios.keys())}, all")
    else:
        print("Usage: python load_scenarios.py [scenario_name|all]")
        print("Available scenarios:")
        runner = LoadTestRunner()
        for name, config in runner.scenarios.items():
            print(f"  {name}: {config['users']} users, {config['run_time']} duration")
        print("  all: Run all scenarios sequentially")

if __name__ == "__main__":
    main()