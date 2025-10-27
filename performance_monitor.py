#!/usr/bin/env python3
"""
Performance Analysis and Visualization Tool for Keycloak Load Tests
Collects and analyzes system metrics during load testing
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import requests
import time
import json
import os
from datetime import datetime, timedelta
import subprocess
import psutil
import threading
import queue

class PerformanceMonitor:
    def __init__(self, prometheus_url="http://localhost:9090", 
                 output_dir="./performance_analysis"):
        self.prometheus_url = prometheus_url
        self.output_dir = output_dir
        self.monitoring_active = False
        self.metrics_queue = queue.Queue()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure matplotlib for better plots
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def collect_system_metrics(self, duration_seconds=300, interval_seconds=5):
        """Collect system metrics using psutil"""
        print(f"Collecting system metrics for {duration_seconds} seconds...")
        
        metrics = []
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        while time.time() < end_time and self.monitoring_active:
            timestamp = datetime.now()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            disk_usage = psutil.disk_usage('/')
            
            # Network I/O metrics
            net_io = psutil.net_io_counters()
            
            metric_point = {
                'timestamp': timestamp,
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_1min': load_avg[0],
                'load_5min': load_avg[1],
                'load_15min': load_avg[2],
                'memory_total': memory.total,
                'memory_used': memory.used,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent,
                'disk_read_bytes': disk_io.read_bytes if disk_io else 0,
                'disk_write_bytes': disk_io.write_bytes if disk_io else 0,
                'disk_read_count': disk_io.read_count if disk_io else 0,
                'disk_write_count': disk_io.write_count if disk_io else 0,
                'disk_total': disk_usage.total,
                'disk_used': disk_usage.used,
                'disk_free': disk_usage.free,
                'net_bytes_sent': net_io.bytes_sent,
                'net_bytes_recv': net_io.bytes_recv,
                'net_packets_sent': net_io.packets_sent,
                'net_packets_recv': net_io.packets_recv
            }
            
            metrics.append(metric_point)
            self.metrics_queue.put(metric_point)
            
            time.sleep(interval_seconds)
        
        return pd.DataFrame(metrics)
    
    def collect_prometheus_metrics(self, queries, duration_seconds=300, interval_seconds=5):
        """Collect metrics from Prometheus"""
        print(f"Collecting Prometheus metrics for {duration_seconds} seconds...")
        
        all_metrics = []
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        while time.time() < end_time and self.monitoring_active:
            timestamp = datetime.now()
            metric_point = {'timestamp': timestamp}
            
            for query_name, query in queries.items():
                try:
                    response = requests.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params={'query': query},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data['status'] == 'success' and data['data']['result']:
                            # Take the first result value
                            value = float(data['data']['result'][0]['value'][1])
                            metric_point[query_name] = value
                        else:
                            metric_point[query_name] = 0
                    else:
                        metric_point[query_name] = 0
                        
                except Exception as e:
                    print(f"Error collecting {query_name}: {e}")
                    metric_point[query_name] = 0
            
            all_metrics.append(metric_point)
            time.sleep(interval_seconds)
        
        return pd.DataFrame(all_metrics)
    
    def start_monitoring(self, test_duration=300):
        """Start comprehensive monitoring"""
        self.monitoring_active = True
        
        # Define Prometheus queries for key metrics
        prometheus_queries = {
            'node_cpu_utilization': 'rate(node_cpu_seconds_total[1m])',
            'node_memory_usage': 'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes',
            'node_load1': 'node_load1',
            'node_network_receive_bytes_rate': 'rate(node_network_receive_bytes_total[1m])',
            'node_network_transmit_bytes_rate': 'rate(node_network_transmit_bytes_total[1m])',
            'container_cpu_usage': 'rate(container_cpu_usage_seconds_total[1m])',
            'container_memory_usage': 'container_memory_usage_bytes'
        }
        
        # Start collecting metrics in parallel
        system_thread = threading.Thread(
            target=lambda: setattr(self, 'system_metrics', 
                                  self.collect_system_metrics(test_duration))
        )
        
        prometheus_thread = threading.Thread(
            target=lambda: setattr(self, 'prometheus_metrics',
                                  self.collect_prometheus_metrics(prometheus_queries, test_duration))
        )
        
        system_thread.start()
        prometheus_thread.start()
        
        return system_thread, prometheus_thread
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
    
    def create_performance_report(self, test_name, system_df, prometheus_df=None):
        """Create comprehensive performance analysis report"""
        print(f"Creating performance report for {test_name}...")
        
        # Create figure with subplots
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle(f'Performance Analysis Report - {test_name}', fontsize=16, fontweight='bold')
        
        # CPU Usage
        axes[0,0].plot(system_df['timestamp'], system_df['cpu_percent'], 'b-', linewidth=2)
        axes[0,0].set_title('CPU Usage (%)')
        axes[0,0].set_ylabel('CPU %')
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].set_ylim(0, 100)
        
        # Memory Usage
        memory_gb = system_df['memory_used'] / (1024**3)
        axes[0,1].plot(system_df['timestamp'], memory_gb, 'g-', linewidth=2)
        axes[0,1].set_title('Memory Usage (GB)')
        axes[0,1].set_ylabel('Memory (GB)')
        axes[0,1].grid(True, alpha=0.3)
        
        # Load Average
        axes[1,0].plot(system_df['timestamp'], system_df['load_1min'], 'r-', linewidth=2, label='1min')
        axes[1,0].plot(system_df['timestamp'], system_df['load_5min'], 'orange', linewidth=2, label='5min')
        axes[1,0].plot(system_df['timestamp'], system_df['load_15min'], 'purple', linewidth=2, label='15min')
        axes[1,0].set_title('System Load Average')
        axes[1,0].set_ylabel('Load')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        
        # Network I/O
        net_sent_mb = system_df['net_bytes_sent'].diff() / (1024*1024)
        net_recv_mb = system_df['net_bytes_recv'].diff() / (1024*1024)
        axes[1,1].plot(system_df['timestamp'], net_sent_mb, 'cyan', linewidth=2, label='Sent')
        axes[1,1].plot(system_df['timestamp'], net_recv_mb, 'magenta', linewidth=2, label='Received')
        axes[1,1].set_title('Network I/O Rate (MB/s)')
        axes[1,1].set_ylabel('MB/s')
        axes[1,1].legend()
        axes[1,1].grid(True, alpha=0.3)
        
        # Disk I/O
        disk_read_mb = system_df['disk_read_bytes'].diff() / (1024*1024)
        disk_write_mb = system_df['disk_write_bytes'].diff() / (1024*1024)
        axes[2,0].plot(system_df['timestamp'], disk_read_mb, 'brown', linewidth=2, label='Read')
        axes[2,0].plot(system_df['timestamp'], disk_write_mb, 'olive', linewidth=2, label='Write')
        axes[2,0].set_title('Disk I/O Rate (MB/s)')
        axes[2,0].set_ylabel('MB/s')
        axes[2,0].legend()
        axes[2,0].grid(True, alpha=0.3)
        
        # System Resource Summary
        axes[2,1].text(0.1, 0.9, f"Performance Summary - {test_name}", 
                      transform=axes[2,1].transAxes, fontsize=12, fontweight='bold')
        
        # Calculate statistics
        stats_text = f"""
CPU Usage:
  Mean: {system_df['cpu_percent'].mean():.1f}%
  Max: {system_df['cpu_percent'].max():.1f}%
  
Memory Usage:
  Mean: {system_df['memory_percent'].mean():.1f}%
  Max: {system_df['memory_percent'].max():.1f}%
  
Load Average (1min):
  Mean: {system_df['load_1min'].mean():.2f}
  Max: {system_df['load_1min'].max():.2f}
  
Network I/O:
  Total Sent: {(system_df['net_bytes_sent'].iloc[-1] - system_df['net_bytes_sent'].iloc[0]) / (1024**2):.1f} MB
  Total Recv: {(system_df['net_bytes_recv'].iloc[-1] - system_df['net_bytes_recv'].iloc[0]) / (1024**2):.1f} MB
        """
        
        axes[2,1].text(0.1, 0.1, stats_text, transform=axes[2,1].transAxes, 
                      fontsize=10, verticalalignment='bottom', fontfamily='monospace')
        axes[2,1].axis('off')
        
        # Format x-axes
        for ax in axes.flat[:-1]:  # Skip the text plot
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.output_dir, f"{test_name}_performance_report.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save raw data
        csv_path = os.path.join(self.output_dir, f"{test_name}_system_metrics.csv")
        system_df.to_csv(csv_path, index=False)
        
        print(f"Report saved: {plot_path}")
        print(f"Data saved: {csv_path}")
        
        return plot_path, csv_path
    
    def analyze_bottlenecks(self, system_df, test_name):
        """Analyze potential performance bottlenecks"""
        print(f"Analyzing bottlenecks for {test_name}...")
        
        bottlenecks = []
        
        # CPU bottleneck analysis
        high_cpu_threshold = 80
        cpu_high_time = (system_df['cpu_percent'] > high_cpu_threshold).sum()
        if cpu_high_time > len(system_df) * 0.1:  # More than 10% of time
            bottlenecks.append(f"CPU: High CPU usage (>{high_cpu_threshold}%) detected for {cpu_high_time} measurements")
        
        # Memory bottleneck analysis
        high_memory_threshold = 85
        memory_high_time = (system_df['memory_percent'] > high_memory_threshold).sum()
        if memory_high_time > 0:
            bottlenecks.append(f"Memory: High memory usage (>{high_memory_threshold}%) detected for {memory_high_time} measurements")
        
        # Load average analysis
        cpu_count = system_df['cpu_count'].iloc[0]
        high_load_time = (system_df['load_1min'] > cpu_count * 1.5).sum()
        if high_load_time > 0:
            bottlenecks.append(f"Load: System overload detected (load > {cpu_count * 1.5}) for {high_load_time} measurements")
        
        # I/O analysis
        disk_read_rate = system_df['disk_read_bytes'].diff().mean() / (1024*1024)  # MB/s
        disk_write_rate = system_df['disk_write_bytes'].diff().mean() / (1024*1024)  # MB/s
        
        if disk_read_rate > 100 or disk_write_rate > 100:  # High I/O threshold
            bottlenecks.append(f"Disk I/O: High disk activity detected (Read: {disk_read_rate:.1f} MB/s, Write: {disk_write_rate:.1f} MB/s)")
        
        # Network analysis
        net_rate = (system_df['net_bytes_sent'].diff().mean() + system_df['net_bytes_recv'].diff().mean()) / (1024*1024)
        if net_rate > 100:  # High network threshold
            bottlenecks.append(f"Network: High network activity detected ({net_rate:.1f} MB/s combined)")
        
        # Save bottleneck analysis
        analysis_path = os.path.join(self.output_dir, f"{test_name}_bottleneck_analysis.txt")
        with open(analysis_path, 'w') as f:
            f.write(f"Bottleneck Analysis for {test_name}\n")
            f.write("=" * 50 + "\n\n")
            
            if bottlenecks:
                f.write("Potential Bottlenecks Detected:\n")
                for i, bottleneck in enumerate(bottlenecks, 1):
                    f.write(f"{i}. {bottleneck}\n")
            else:
                f.write("No significant bottlenecks detected.\n")
            
            f.write(f"\nPerformance Metrics Summary:\n")
            f.write(f"Average CPU Usage: {system_df['cpu_percent'].mean():.2f}%\n")
            f.write(f"Peak CPU Usage: {system_df['cpu_percent'].max():.2f}%\n")
            f.write(f"Average Memory Usage: {system_df['memory_percent'].mean():.2f}%\n")
            f.write(f"Peak Memory Usage: {system_df['memory_percent'].max():.2f}%\n")
            f.write(f"Average Load (1min): {system_df['load_1min'].mean():.2f}\n")
            f.write(f"Peak Load (1min): {system_df['load_1min'].max():.2f}\n")
        
        print(f"Bottleneck analysis saved: {analysis_path}")
        return bottlenecks, analysis_path

def main():
    """Example usage of the performance monitor"""
    monitor = PerformanceMonitor()
    
    print("Performance Monitor - Example Usage")
    print("1. Start monitoring")
    print("2. Run your load test")
    print("3. The monitor will collect metrics and generate reports")
    
    # Example monitoring for 60 seconds
    duration = 60
    test_name = f"example_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Start monitoring
    system_thread, prometheus_thread = monitor.start_monitoring(duration)
    
    print(f"Monitoring for {duration} seconds...")
    time.sleep(duration)
    
    # Stop monitoring
    monitor.stop_monitoring()
    system_thread.join()
    prometheus_thread.join()
    
    # Generate report
    if hasattr(monitor, 'system_metrics'):
        report_path, data_path = monitor.create_performance_report(test_name, monitor.system_metrics)
        bottlenecks, analysis_path = monitor.analyze_bottlenecks(monitor.system_metrics, test_name)
        
        print(f"\nAnalysis complete!")
        print(f"Report: {report_path}")
        print(f"Data: {data_path}")
        print(f"Analysis: {analysis_path}")
        
        if bottlenecks:
            print("\nBottlenecks detected:")
            for bottleneck in bottlenecks:
                print(f"- {bottleneck}")

if __name__ == "__main__":
    main()