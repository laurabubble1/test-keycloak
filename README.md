# Keycloak Load Testing - User Manual

## Overview

This comprehensive load testing suite is designed to evaluate Keycloak's performance under various load conditions using Locust, with integrated monitoring via Prometheus, Grafana, and system monitoring tools.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation & Setup](#installation--setup)
3. [API Endpoints Tested](#api-endpoints-tested)
4. [Load Test Scenarios](#load-test-scenarios)
5. [Monitoring Configuration](#monitoring-configuration)
6. [Execution Instructions](#execution-instructions)
7. [Performance Analysis](#performance-analysis)
8. [Quality Goals & Metrics](#quality-goals--metrics)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Docker and Docker Compose
- Python 3.8+ with pip
- At least 8GB RAM (16GB recommended for stress tests)
- 20GB free disk space
- Network access for downloading Docker images

### Required Python Packages (if you intend on running the load tests using your local python installation)

```bash
pip install locust psutil matplotlib pandas numpy requests
```

### Optional Python Packages (for enhanced visualizations)

```bash
pip install seaborn plotly
```

## Installation & Setup

### 1. Clone or Download the Test Suite

Ensure you have all files in your test directory:

```bash
test-keycloak/
├── docker-compose.yml
├── prometheus.yml
├── locustfile.py
├── load_scenarios.py
├── run_load_test.sh
├── performance_monitor.py
└── README.md
```

### 2. Start the Infrastructure

```bash
# Start all monitoring and Keycloak services
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 3. Verify Services

- Keycloak Admin Console: <http://localhost:8080/admin> (admin/admin)
- Grafana Dashboard: <http://localhost:3000> (admin/admin)
- Prometheus: <http://localhost:9090>
- Netdata: <http://localhost:19999>
- cAdvisor: <http://localhost:8081>
- locust Web UI: <http://localhost:8089>

### 4. Wait for Keycloak to Initialize

Keycloak may take 2-3 minutes to fully start. Check the logs:

```bash
docker-compose logs keycloak
```

## API Endpoints Tested

The load testing suite covers 20 API endpoints across 5 Keycloak components:

### Create Operations (5 endpoints)

1. **Create User** - `/admin/realms/{realm}/users`
   - Creates new users with credentials and profile information
   - Includes firstName, lastName, email, username, and password

2. **Create Client** - `/admin/realms/{realm}/clients`
   - Creates OAuth2/OpenID Connect clients
   - Configures protocol, flow settings, and client properties

3. **Create Realm Role** - `/admin/realms/{realm}/roles`
   - Creates realm-level roles for authorization
   - Sets role names, descriptions, and composite settings

4. **Create Group** - `/admin/realms/{realm}/groups`
   - Creates user groups for organization
   - Sets group names and attributes

5. **Create Client Scope** - `/admin/realms/{realm}/client-scopes`
   - Creates client scopes for fine-grained permissions
   - Configures OpenID Connect protocol mappings

### Read Operations (5 endpoints)

1. **Read Users** - `/admin/realms/{realm}/users`
   - Retrieves paginated user lists
   - Tests with max=20, first=0 parameters

2. **Read Clients** - `/admin/realms/{realm}/clients`
   - Lists all clients in the realm
   - Retrieves client configurations and settings

3. **Read Realm Roles** - `/admin/realms/{realm}/roles`
   - Gets all realm roles and their definitions
   - Most frequently accessed endpoint (weight: 5)

4. **Read Groups** - `/admin/realms/{realm}/groups`
   - Retrieves group hierarchy and membership
   - Tests group structure and attributes

5. **Read Realm Info** - `/admin/realms/{realm}`
   - Gets realm configuration and settings
   - High-frequency operation (weight: 4)

### Update Operations (5 endpoints)

1. **Update User** - `/admin/realms/{realm}/users/{id}`
   - Modifies user profile and attributes
   - Updates firstName and custom attributes

2. **Update Client** - `/admin/realms/{realm}/clients/{id}`
   - Changes client configuration
   - Modifies descriptions and client attributes

3. **Update Realm Role** - `/admin/realms/{realm}/roles/{name}`
   - Updates role descriptions and properties
   - Manages role metadata

4. **Update Group** - `/admin/realms/{realm}/groups/{id}`
   - Modifies group attributes and descriptions
   - Updates group metadata and properties

5. **Update Realm Settings** - `/admin/realms/{realm}`
   - Changes realm-level configuration
   - Updates display names and realm attributes

### Delete Operations (5 endpoints)

1. **Delete User** - `/admin/realms/{realm}/users/{id}`
   - Removes users from the realm
   - Maintains at least one user for continued testing

2. **Delete Client** - `/admin/realms/{realm}/clients/{id}`
   - Removes client configurations
   - Preserves essential clients for realm operation

3. **Delete Realm Role** - `/admin/realms/{realm}/roles/{name}`
   - Removes role definitions
   - Keeps core roles for system functionality

4. **Delete Group** - `/admin/realms/{realm}/groups/{id}`
   - Removes group structures
   - Maintains group hierarchy integrity

5. **Delete Client Scope** - `/admin/realms/{realm}/client-scopes/{id}`
   - Removes client scope definitions
   - Cleans up test-created scopes

## Load Test Scenarios

### Scenario Configuration

| Scenario | Users | Spawn Rate | Duration | Purpose |
|----------|-------|------------|----------|---------|
| **Light Load** | 20 | 2/sec | 5 min | Baseline performance |
| **Medium Load** | 100 | 5/sec | 10 min | Normal production load |
| **Heavy Load** | 500 | 10/sec | 15 min | Peak usage simulation |
| **Stress Test** | 2000 | 20/sec | 20 min | System limits testing |

### Think Time Configuration

- **Base wait time**: 2-5 seconds between requests
- **Realistic user behavior**: Simulates human interaction patterns
- **Authentication overhead**: Token refresh every 4 minutes
- **Resource cleanup**: Automatic cleanup prevents resource exhaustion

### Task Weight Distribution

- **Read operations**: 70% (most common in production)
- **Create operations**: 20% (moderate frequency)
- **Update operations**: 7% (occasional modifications)
- **Delete operations**: 3% (least frequent operations)

## Monitoring Configuration

### Prometheus Metrics Collection

- **Scrape interval**: 5 seconds
- **Data sources**:
  - Node Exporter: System-level metrics (CPU, memory, disk, network)
  - cAdvisor: Container-level resource usage
  - Netdata: Detailed system performance metrics
  - Keycloak: Application-specific metrics (when enabled)

### Key Performance Indicators (KPIs)

#### System Metrics

1. **CPU Usage**
   - Definition: Percentage of CPU time spent on non-idle tasks
   - Target: < 70% average, < 90% peak
   - Collection: `node_cpu_seconds_total` counter

2. **Memory Usage**
   - Definition: RAM utilization including buffers and cache
   - Target: < 80% average, < 90% peak
   - Collection: `node_memory_MemAvailable_bytes`

3. **Load Average**
   - Definition: Average system load over 1, 5, and 15 minutes
   - Target: < CPU core count * 1.5
   - Collection: `node_load1`, `node_load5`, `node_load15`

4. **Disk I/O**
   - Definition: Read/write operations per second and throughput
   - Target: < 1000 IOPS, < 100 MB/s sustained
   - Collection: `node_disk_io_time_seconds_total`

5. **Network I/O**
   - Definition: Network traffic in bytes per second
   - Target: < 100 MB/s combined throughput
   - Collection: `node_network_receive_bytes_total`

### Grafana Dashboards

Access dashboards at <http://localhost:3000>:

- System Overview: CPU, memory, disk, network
- Container Metrics: Docker container resource usage
- Keycloak Performance: Application-specific metrics
- Load Test Results: Request rates, response times, errors

## Execution Instructions (if you don't want to use the locust Web UI)

### Method 1: Using Python Script

```bash
# Install dependencies
pip install locust psutil matplotlib pandas numpy requests

# Run specific scenario
python load_scenarios.py light_load    # 20 users
python load_scenarios.py medium_load   # 100 users
python load_scenarios.py heavy_load    # 500 users
python load_scenarios.py stress_test   # 2000 users

# Run all scenarios sequentially
python load_scenarios.py all
```

### Method 2: Using Bash Script (for Linux/MacOS)

```bash
# Make script executable
chmod +x run_load_test.sh

# Run specific scenario
./run_load_test.sh light    # 20 users
./run_load_test.sh medium   # 100 users
./run_load_test.sh heavy    # 500 users
./run_load_test.sh stress   # 2000 users

# Run all scenarios
./run_load_test.sh all
```

### Method 3: Manual Locust Execution

```bash
# Basic command structure
locust -f locustfile.py \
       --host http://localhost:8080 \
       --users 100 \
       --spawn-rate 5 \
       --run-time 10m \
       --html results.html \
       --headless ## Run without the web UI

# Web UI mode (for interactive testing)
locust -f locustfile.py --host http://localhost:8080
# Then open http://localhost:8089
```

### Performance Monitoring During Tests

```bash
# Start performance monitoring
python performance_monitor.py &

# Run your load test
python load_scenarios.py medium_load

# Stop monitoring (or it stops automatically after test duration)
```

## Performance Analysis

> Should be changed because Copilot generated this not sure it works as intended and is probably wrong

### Automated Analysis

The performance monitor automatically generates:

1. **Performance Reports** (`*_performance_report.png`)
   - CPU usage over time
   - Memory consumption patterns
   - System load averages
   - Network I/O rates
   - Disk I/O activity
   - Statistical summaries

2. **Raw Data Files** (`*_system_metrics.csv`)
   - Timestamped metric data
   - Suitable for custom analysis
   - Compatible with Excel, R, Python

3. **Bottleneck Analysis** (`*_bottleneck_analysis.txt`)
   - Identifies performance constraints
   - Suggests optimization areas
   - Provides threshold-based alerts

### Manual Analysis Tools

#### Locust Results

- HTML reports with request statistics
- CSV files with detailed timing data
- Real-time statistics during execution

#### System Monitoring

```bash
# Real-time CPU monitoring
top -p $(pgrep -f keycloak)

# Memory usage tracking
free -m -s 5

# I/O statistics
iostat -x 5

# Network monitoring
nethogs

# Container statistics
docker stats
```

#### Prometheus Queries

Access Prometheus at <http://localhost:9090> for custom queries:

```promql
# CPU usage
rate(node_cpu_seconds_total[5m])

# Memory usage
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes

# Disk I/O rate
rate(node_disk_read_bytes_total[5m])

# Network traffic
rate(node_network_receive_bytes_total[5m])
```

## Troubleshooting

### Common Issues

#### URL for localhost services

Use `http://host.docker.internal:PORT` instead of `http://localhost:PORT` when accessing services from within Docker containers on Windows or MacOS.

### Log Locations

- Keycloak logs: `docker-compose logs keycloak`
- Prometheus logs: `docker-compose logs prometheus`
- Grafana logs: `docker-compose logs grafana`
- Load test results: `./test_results/`
- Performance analysis: `./performance_analysis/`

### Support and Resources

- Keycloak Documentation: <https://www.keycloak.org/documentation>
- Locust Documentation: <https://docs.locust.io/>
- Prometheus Documentation: <https://prometheus.io/docs/>
- Grafana Documentation: <https://grafana.com/docs/>

---

## Quick Start Checklist

- [ ] Install Docker and Docker Compose
- [ ] Install Python dependencies: `pip install locust psutil matplotlib pandas numpy requests`
- [ ] Start services: `docker-compose up -d`
- [ ] Wait for Keycloak initialization (2-3 minutes)
- [ ] Verify services are accessible (Keycloak, Grafana, Prometheus)
- [ ] Run test: `python load_scenarios.py light_load`
- [ ] Check results in `./test_results/` directory
- [ ] Review performance analysis in `./performance_analysis/` directory

For questions or issues, refer to the troubleshooting section or check service logs using `docker-compose logs [service-name]`.
