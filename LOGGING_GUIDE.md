# Logging Guide for Debugging

## Overview
The Autonomous Incident Commander now has comprehensive logging at every phase of execution. This guide helps you understand the log output for debugging.

## Log Levels
- **INFO**: Normal execution flow, phase transitions, LLM invocations
- **DEBUG**: Detailed step-by-step information (plan steps, etc.)
- **WARNING**: Non-critical issues (missing log files, fallback to simulated data)
- **ERROR**: Critical failures

## Log Flow

### 1. Application Startup
```
######################################################################
AUTONOMOUS INCIDENT COMMANDER STARTING
######################################################################
Incident ID: inc-2026-02-06-113742
Environment: production
Service: checkout-service
Creating incident commander graph...
Initializing Ollama LLM with qwen2.5:7b model...
LLM initialized successfully
Graph created successfully
Invoking graph with initial state...
```

**What to check:**
- ✅ Incident ID is correct
- ✅ LLM initializes without errors
- ✅ Graph creation succeeds

---

### 2. DETECT Phase
```
======================================================================
DETECT PHASE STARTED
======================================================================
Incident ID: inc-2026-02-06-113742
Service: checkout-service v2.18.4
Severity: critical
```

**What to check:**
- ✅ Incident details are captured correctly
- ✅ Severity matches expected level

---

### 3. PLAN Phase
```
======================================================================
PLAN PHASE STARTED
======================================================================
Invoking LLM to create investigation plan...
Investigation plan created with 5 steps
Plan step 1: Analyze metrics for anomalies
Plan step 2: Review log patterns
...
```

**What to check:**
- ✅ LLM responds successfully
- ✅ Plan has reasonable number of steps (3-7)
- ✅ Plan steps are relevant to the incident

---

### 4. INVESTIGATE Phase

#### Metrics Analysis
```
======================================================================
METRICS ANALYSIS STARTED
======================================================================
Analyzing metrics snapshot...
```

**What to check:**
- ✅ Metrics are being analyzed
- ✅ No errors accessing metrics data

#### Log Analysis
```
======================================================================
LOG ANALYSIS STARTED
======================================================================
Starting log analysis with anomaly detection...
Log file path: sample_logs.json
Running hybrid anomaly detection (Z-Score + Isolation Forest)...
Found 15 anomalies, selecting top 10 for LLM analysis
Invoking LLM for anomaly analysis...
LLM analysis complete
```

**What to check:**
- ✅ Log file path is correct
- ✅ Anomalies are detected (if expected)
- ✅ LLM analysis completes successfully
- ⚠️ If "No log file provided, using simulated analysis" - check if log file exists

#### Deployment Analysis
```
======================================================================
DEPLOYMENT ANALYSIS STARTED
======================================================================
Analyzing deployment context...
```

**What to check:**
- ✅ Deployment context is available
- ✅ Recent deployments are identified

---

### 5. DECIDE Phase
```
======================================================================
DECIDE PHASE STARTED
======================================================================
Synthesizing findings from all agents...
```

**What to check:**
- ✅ All agent findings are available
- ✅ Root cause is determined
- ✅ Confidence score is reasonable (0.0-1.0)

---

### 6. ACT Phase
```
======================================================================
ACT PHASE STARTED
======================================================================
Root cause: Memory leak in promotion rules engine
Confidence: 85.0%
```

**What to check:**
- ✅ Root cause is specific and actionable
- ✅ Confidence score is high enough (>60%)
- ✅ Remediation actions are generated

---

### 7. REPORT Phase
```
======================================================================
REPORT PHASE STARTED
======================================================================
Compiling final incident report...
```

**What to check:**
- ✅ Report is generated successfully
- ✅ All sections are populated

---

### 8. Completion
```
Graph execution complete
######################################################################
INCIDENT COMMANDER FINISHED
######################################################################
```

**What to check:**
- ✅ No errors during execution
- ✅ Final state contains all expected data

---

## Common Issues and Solutions

### Issue: "Could not connect to Ollama"
**Solution:**
```bash
# Start Ollama server
ollama serve

# In another terminal, verify it's running
curl http://localhost:11434/api/tags
```

### Issue: "Model qwen2.5:7b not found"
**Solution:**
```bash
ollama pull qwen2.5:7b
```

### Issue: "No log file provided, using simulated analysis"
**Solution:**
- Check if `log_file_path` is set in incident data
- Verify the log file exists at the specified path
- Ensure the file is readable

### Issue: "Baseline stats file not found"
**Solution:**
- Run baseline calculation first:
```python
from log_analyzer import StreamingLogAnalyzer, save_baseline_stats

analyzer = StreamingLogAnalyzer()
stats = analyzer.calculate_baseline_stats('sample_logs.json')
save_baseline_stats(stats, 'baseline_stats.json')
```

### Issue: LLM responses are slow
**Solution:**
- Use a smaller model: `ollama pull qwen2.5:3b`
- Update `main.py` to use `model="qwen2.5:3b"`
- Or use a faster model like `llama3.2:3b`

---

## Debugging Tips

### 1. Enable Debug Logging
In `main.py`, change:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. Save Logs to File
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('incident_commander.log'),
        logging.StreamHandler()
    ]
)
```

### 3. Check LLM Responses
Add after each LLM invocation:
```python
logger.debug(f"LLM Response: {response.content[:200]}...")
```

### 4. Monitor Graph State
Add at phase transitions:
```python
logger.debug(f"State keys: {list(state.keys())}")
logger.debug(f"Next action: {state.get('next_action')}")
```

---

## Performance Monitoring

Track these metrics in logs:
- **Phase Duration**: Time between phase start/end logs
- **LLM Latency**: Time between "Invoking LLM" and "complete" logs
- **Anomaly Count**: Number of anomalies detected
- **Confidence Score**: Final confidence in root cause

---

## Log File Locations
- **Console Output**: stdout/stderr
- **Optional Log File**: `incident_commander.log` (if configured)
- **Baseline Stats**: `baseline_stats.json`
- **Isolation Forest Model**: `iso_forest_model.joblib`
