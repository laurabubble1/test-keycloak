# Keycloak Performance Testing Suite

## Overview

This professional performance testing suite provides isolated load testing for Keycloak using a two-Docker architecture. The setup separates the target system (Keycloak + monitoring) from the load generator (Locust), simulating realistic external load while maintaining clean resource isolation.

## Architecture

### Target System (`docker-compose-target.yml`)
- Keycloak + PostgreSQL database
- Monitoring Stack: Prometheus, Grafana, Netdata, cAdvisor, Node-exporter
- Purpose: The system under test

### Load Generator (`docker-compose-locust.yml`) 
- Locust Master + Multiple Workers
- Purpose: Generate external load against target system
- Network: Separate Docker network for true isolation

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation & Setup](#installation--setup)
3. [Architecture Details](#architecture-details)
4. [API Endpoints Tested](#api-endpoints-tested)
5. [Load Test Scenarios](#load-test-scenarios)
6. [Monitoring Configuration](#monitoring-configuration)
7. [Usage Instructions](#usage-instructions)
8. [Performance Analysis](#performance-analysis)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Docker and Docker Compose
- Python 3.8+ with pip
- At least 8GB RAM (16GB recommended for stress tests)
- 20GB free disk space
- Network access for downloading Docker images

### Files Structure

```
test-keycloak/
├── control.sh                    # Main control script
├── docker-compose-target.yml     # Target system (Keycloak + monitoring)
├── docker-compose-locust.yml     # Load generator (Locust)
├── locustfile-external.py        # Load test scenarios for external access
├── prometheus.yml                # Metrics collection config
├── keycloak-dashboard.json       # Grafana dashboard
└── README.md                     # This file
```

## Installation & Setup

### 1. Clone or Download the Test Suite

Ensure you have all files in your test directory:

```bash
git clone https://github.com/laurabubble1/test-keycloak.git
cd test-keycloak
```

### 2. Start Target System (Keycloak + Monitoring)

```bash
./control.sh start-target
```

### 3. Wait for Keycloak to Initialize (30-60 seconds)

```bash
./control.sh logs-target  # Watch startup logs
```

### 4. Start Load Generator

```bash
./control.sh start-locust
```

### 5. Access Your Systems

- Locust Web Interface: http://localhost:8089
- Keycloak Admin: http://localhost:8080/admin (admin/admin)
- Grafana Dashboard: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Netdata: http://localhost:19999

## Architecture Details

### Two-Docker Design Benefits

- **Resource Isolation**: Load generator doesn't consume target system resources
- **Realistic Testing**: Simulates external traffic patterns
- **Independent Scaling**: Scale load generators separately from target
- **Clean Monitoring**: Target system metrics aren't polluted by load generator
- **Production-Like**: Mirrors real-world deployment scenarios

### Control Script Commands

```bash
./control.sh start-target    # Start Keycloak + monitoring
./control.sh start-locust    # Start load generator
./control.sh stop-target     # Stop target system
./control.sh stop-locust     # Stop load generator
./control.sh status          # Show status of both systems
./control.sh logs-target     # Show Keycloak logs
./control.sh logs-locust     # Show Locust logs
./control.sh restart-all     # Restart everything
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

## Usage Instructions

### Step-by-Step Testing Process

#### 1. System Startup

```bash
# Start target system (Keycloak + monitoring)
./control.sh start-target

# Wait for Keycloak to fully initialize (30-60 seconds)
./control.sh logs-target

# Start load generator
./control.sh start-locust

# Verify everything is running
./control.sh status
```

#### 2. Configure Load Test

1. Open Locust Web Interface: http://localhost:8089
2. Set Test Parameters:
   - Number of Users: Start with 50 for first test
   - Spawn Rate: 5 users per second
   - Host: Should already be set to `http://host.docker.internal:8080`
3. Click "Start swarming"

#### 3. Monitor Performance

- Locust Dashboard: Real-time request statistics at http://localhost:8089
- Grafana Dashboard: System metrics at http://localhost:3000
- Prometheus: Raw metrics at http://localhost:9090

#### 4. Test Progression

```bash
# Start small and scale up
Test 1: 50 users,  5/sec spawn rate   (5 minutes)
Test 2: 100 users, 10/sec spawn rate  (10 minutes)
Test 3: 200 users, 15/sec spawn rate  (15 minutes)
Test 4: 500 users, 20/sec spawn rate  (20 minutes)
```

### Alternative Testing Methods

For legacy compatibility, these scripts also exist:

```bash
# Standalone load testing (without Docker separation)
./alt_run_load_test.sh light    # 20 users
./alt_run_load_test.sh medium   # 100 users
./alt_run_load_test.sh heavy    # 500 users
```

### System Control Commands

```bash
# Start/stop individual systems
./control.sh start-target     # Start only Keycloak + monitoring
./control.sh start-locust     # Start only load generator
./control.sh stop-target      # Stop target system
./control.sh stop-locust      # Stop load generator

# System monitoring
./control.sh status           # Show all container status
./control.sh logs-target      # Watch Keycloak logs
./control.sh logs-locust      # Watch Locust logs

# Complete restart
./control.sh restart-all      # Restart everything cleanly
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

### Common Issues and Solutions

#### Issue: Network Recreation Errors

```bash
ERROR: Network "test-keycloak_default" needs to be recreated
```

**Solution:**

```bash
./control.sh stop-target
./control.sh stop-locust
./control.sh start-target
./control.sh start-locust
```

#### Issue: Keycloak Connection Refused

```bash
ConnectionRefusedError(111, 'Connection refused')
```

**Solutions:**

1. Wait for startup: Keycloak takes 30-60 seconds to initialize
2. Check logs: `./control.sh logs-target`
3. Verify port: http://localhost:8080 should be accessible
4. Restart if needed: `./control.sh restart-all`

#### Issue: Locust Can't Reach Keycloak

**Problem**: Load generator can't connect to target system
**Solution**: Verify `host.docker.internal` is working:

```bash
# Test from locust container
docker exec locust-master ping host.docker.internal
```

### System Health Checks

#### Verify All Services Running

```bash
./control.sh status
# All services should show "Up" status
```

#### Check Service Accessibility

```bash
# Target system endpoints
curl -s http://localhost:8080/realms/master/.well-known/openid_configuration
curl -s http://localhost:9000/metrics | head -5
curl -s http://localhost:9090/-/healthy
curl -s http://localhost:3000/api/health

# Load generator endpoint
curl -s http://localhost:8089/
```

### Log Locations

- Keycloak logs: `./control.sh logs-target`
- Locust logs: `./control.sh logs-locust`
- All system logs: `docker stats --no-stream`

### Support and Resources

- Keycloak Documentation: <https://www.keycloak.org/documentation>
- Locust Documentation: <https://docs.locust.io/>
- Prometheus Documentation: <https://prometheus.io/docs/>
- Grafana Documentation: <https://grafana.com/docs/>

---

## Quick Start Checklist

- [ ] Install Docker and Docker Compose (latest versions)
- [ ] Clone/download all project files to your directory
- [ ] Make control script executable: `chmod +x control.sh`
- [ ] Start target system: `./control.sh start-target`
- [ ] Wait for initialization: Watch logs for "Keycloak started" message
- [ ] Start load generator: `./control.sh start-locust`
- [ ] Verify services: `./control.sh status` shows all "Up"
- [ ] Access Locust: http://localhost:8089 loads successfully
- [ ] Access Grafana: http://localhost:3000 (admin/admin)
- [ ] Import dashboard: Upload `keycloak-dashboard.json` to Grafana
- [ ] Run first test: 50 users, 5/sec spawn rate, 5 minutes
- [ ] Monitor results: Watch both Locust stats and Grafana metrics

**Success Indicators:**

- Locust shows green success rates (>95%)
- Grafana displays real-time metrics
- Response times under 500ms for 95th percentile
- No container restarts or errors in logs

For issues, start with `./control.sh restart-all` and check the troubleshooting section above.
