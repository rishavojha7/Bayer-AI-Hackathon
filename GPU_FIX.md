# Quick Fix: Enable GPU for Ollama

## Issue
Ollama is running on CPU (100% CPU) instead of GPU, even though:
- NVIDIA RTX 3050 Laptop GPU is available
- CUDA 13.0 is installed
- Drivers are up to date

## Solution

### Step 1: Stop Ollama
```bash
# Stop Ollama service
taskkill /F /IM ollama.exe

# Or if running as service
net stop ollama
```

### Step 2: Set Environment Variable (Force GPU)
```bash
# In PowerShell
$env:OLLAMA_GPU_LAYERS = "999"

# Make it permanent (optional)
[System.Environment]::SetEnvironmentVariable('OLLAMA_GPU_LAYERS', '999', 'User')
```

### Step 3: Restart Ollama
```bash
# Start Ollama service
ollama serve
```

### Step 4: Verify GPU Usage
In a **new terminal**, run:
```bash
# Pull and run model
ollama run qwen3:8b "What is 2+2?"
```

In **another terminal**, monitor GPU:
```bash
nvidia-smi -l 1
```

You should see:
- GPU Memory Usage increase to ~4-5GB
- GPU Utilization spike to 80-100%
- Much faster responses (5-10 seconds instead of 45-60 seconds)

### Step 5: Check Ollama Status
```bash
ollama ps
```

Should now show: `100% GPU` instead of `100% CPU`

## Alternative: Reinstall Ollama

If the above doesn't work:

1. **Uninstall Ollama**
   - Go to Settings > Apps > Ollama > Uninstall

2. **Download latest Ollama**
   - Visit: https://ollama.ai/download
   - Download Windows installer

3. **Install Ollama**
   - Run installer
   - Ollama will auto-detect GPU on first run

4. **Verify**
   ```bash
   ollama pull qwen3:8b
   ollama run qwen3:8b "Test"
   ```

## Expected Performance After Fix

| Metric | Before (CPU) | After (GPU) |
|--------|--------------|-------------|
| qwen3:1.7b | 10-15s | 2-3s |
| qwen3:8b | 45-60s | 5-10s |
| Full workflow | 4-6 min | 40-80s |

## Troubleshooting

### If still using CPU:
```bash
# Check Ollama logs
ollama logs

# Check CUDA availability
nvidia-smi

# Verify CUDA path
echo $env:CUDA_PATH
```

### If GPU memory error:
Your RTX 3050 has 6GB VRAM:
- `qwen3:8b` needs ~5GB → **Should work**
- `qwen3:1.7b` needs ~2GB → **Will definitely work**

If 8B model doesn't fit, use 1.7B model (still much faster on GPU).
