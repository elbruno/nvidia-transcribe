# Async Mode Implementation Guide

## Overview

The Scenario 4 client-server architecture implements **async mode** using modern asynchronous patterns to handle long-running transcription operations efficiently. This document explains the async implementation details across the server and clients.

## Table of Contents

1. [Server-Side Async Pattern (FastAPI)](#server-side-async-pattern-fastapi)
2. [Background Task Processing](#background-task-processing)
3. [Client-Side Async Patterns](#client-side-async-patterns)
4. [Performance Benefits](#performance-benefits)
5. [Implementation Details](#implementation-details)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Server-Side Async Pattern (FastAPI)

### What is Async Mode?

The FastAPI server uses **async/await** patterns to handle HTTP requests asynchronously. This allows the server to:

- Process multiple requests concurrently without blocking
- Return responses quickly while cleanup tasks run in the background
- Scale efficiently under load
- Avoid blocking the event loop during I/O operations

### Async Endpoint Definition

**File**: `scenario4/server/app.py` (Lines 164-246)

```python
@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Transcribe an audio file asynchronously.
    
    The function returns immediately after transcription completes,
    while cleanup tasks run in the background.
    """
```

### Key Async Components

#### 1. Async Function Declaration

```python
async def transcribe_audio(...):
```

The `async` keyword marks this as an asynchronous function that can be awaited and doesn't block the event loop.

#### 2. FastAPI Background Tasks

```python
background_tasks: BackgroundTasks
```

FastAPI's `BackgroundTasks` allows scheduling cleanup operations that run **after** the response is sent to the client.

#### 3. Model Startup

```python
@app.on_event("startup")
async def load_model():
    """Load the ASR model on server startup."""
    global asr_model
    asr_model = nemo_asr.models.ASRModel.from_pretrained(MODEL_NAME)
```

The model is loaded once at startup using an async startup event, ensuring it's ready before accepting requests.

---

## Background Task Processing

### Why Background Tasks?

Transcription generates temporary files that need cleanup:
- Uploaded audio file
- Converted WAV file (if original was MP3/FLAC)

Instead of blocking the response while cleaning up these files, we schedule cleanup tasks to run **after** sending the response to the client.

### Implementation Pattern

```python
# Schedule cleanup tasks (don't block response)
background_tasks.add_task(cleanup_file, temp_upload_path)
if temp_wav:
    background_tasks.add_task(cleanup_file, temp_wav)

# Return response immediately
return TranscriptionResponse(...)
```

### Benefits

1. **Faster Response Times**: Client receives results immediately
2. **Resource Cleanup**: Files are still cleaned up reliably
3. **Better UX**: Users don't wait for cleanup operations
4. **Scalability**: Server can handle more concurrent requests

### Cleanup Function

```python
def cleanup_file(file_path: Path):
    """Remove temporary file (runs in background)."""
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {e}")
```

---

## Client-Side Async Patterns

### C# Console Client

**File**: `scenario4/clients/console/Program.cs`

The console client uses async/await for HTTP operations:

```csharp
static async Task Main(string[] args)
{
    using var client = new HttpClient();
    
    // Async health check
    var healthResponse = await client.GetAsync($"{apiUrl}/health");
    
    // Async file upload
    using var form = new MultipartFormDataContent();
    using var fileContent = new StreamContent(fileStream);
    form.Add(fileContent, "file", fileName);
    
    var response = await client.PostAsync($"{apiUrl}/transcribe", form);
    
    // Async response reading
    var responseContent = await response.Content.ReadAsStringAsync();
    var result = JsonSerializer.Deserialize<TranscriptionResult>(responseContent);
}
```

**Key Points**:
- `async Task Main`: Entry point supports async
- `await`: Non-blocking HTTP calls
- `HttpClient`: Reuses connections efficiently
- Exception handling: Catches network and API errors

### Blazor Web Client

**File**: `scenario4/clients/webapp/Components/Pages/Transcribe.razor`

```csharp
private async Task HandleSubmit()
{
    if (selectedFile == null) return;
    
    isProcessing = true;
    errorMessage = null;
    
    try
    {
        // Async file upload with progress
        using var content = new MultipartFormDataContent();
        var streamContent = new StreamContent(selectedFile.OpenReadStream(maxFileSize));
        content.Add(streamContent, "file", selectedFile.Name);
        
        // Async POST request
        var response = await Http.PostAsync("api/transcribe", content);
        response.EnsureSuccessStatusCode();
        
        // Async response parsing
        transcriptionResult = await response.Content
            .ReadFromJsonAsync<TranscriptionResult>();
    }
    catch (Exception ex)
    {
        errorMessage = $"Error: {ex.Message}";
    }
    finally
    {
        isProcessing = false;
    }
}
```

**Key Points**:
- `async Task`: Async event handler
- Progress indicator: `isProcessing` flag
- Error handling: User-friendly error messages
- Resource cleanup: `finally` block

---

## Performance Benefits

### Response Time Comparison

| Operation | Synchronous | Async with Background Tasks |
|-----------|-------------|----------------------------|
| Transcription | 5-60 seconds | 5-60 seconds |
| File cleanup | 0.1-0.5 seconds | 0 seconds (background) |
| **Total response time** | **5-60.5 seconds** | **5-60 seconds** |

### Concurrency Benefits

**Synchronous Server**:
```
Request 1: [========] (blocks thread)
Request 2:            [========] (waits)
Request 3:                       [========] (waits)
```

**Async Server**:
```
Request 1: [========]
Request 2: [========] (concurrent)
Request 3: [========] (concurrent)
```

Async mode allows the server to handle multiple requests simultaneously without blocking threads.

### Memory Efficiency

- **Thread per request**: Synchronous servers need one thread per request (~1MB stack per thread)
- **Event loop**: Async servers use a single event loop with minimal overhead
- **Result**: Can handle 1000s of concurrent connections with lower memory footprint

---

## Implementation Details

### Server Architecture

```
┌─────────────────────────────────────┐
│        FastAPI Application          │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Async Endpoint Handler     │  │
│  │   async def transcribe()     │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             ├─> 1. Receive file    │
│             ├─> 2. Save to temp    │
│             ├─> 3. Transcribe      │
│             │    (blocking sync)   │
│             ├─> 4. Schedule cleanup│
│             └─> 5. Return response │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Background Tasks Queue     │  │
│  │   (runs after response)      │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             └─> Cleanup files      │
│                                     │
└─────────────────────────────────────┘
```

### Transcription is Synchronous

**Important**: The actual transcription operation is **synchronous** (CPU/GPU-bound), but it runs within an async function:

```python
async def transcribe_audio(...):
    # ... setup code ...
    
    # This is a synchronous, blocking operation
    output = asr_model.transcribe([str(audio_path)], timestamps=True)
    
    # But cleanup happens in background
    background_tasks.add_task(cleanup_file, temp_path)
    
    return result  # Response sent immediately
```

**Why is this okay?**
- Transcription is CPU/GPU-bound, not I/O-bound
- There's no benefit to making the model inference async
- The model uses threading/multiprocessing internally
- Background tasks still provide value for cleanup

### When Async Provides Value

✅ **File I/O**: Reading/writing files asynchronously
✅ **Network requests**: HTTP calls, database queries
✅ **Background tasks**: Cleanup, logging, notifications
✅ **Multiple concurrent requests**: Server scalability

❌ **CPU-bound work**: Model inference, heavy computation
❌ **GPU operations**: CUDA operations are already optimized

---

## Best Practices

### 1. Use Async for I/O Operations

```python
# Good: Async file operations (if using aiofiles)
async with aiofiles.open('file.txt', 'r') as f:
    content = await f.read()

# Good: Async HTTP requests (if using httpx)
async with httpx.AsyncClient() as client:
    response = await client.get('https://api.example.com')
```

### 2. Schedule Background Tasks for Cleanup

```python
# Good: Non-blocking cleanup
background_tasks.add_task(cleanup_file, temp_path)
background_tasks.add_task(send_metrics, result)

# Bad: Blocking cleanup
cleanup_file(temp_path)  # Delays response
```

### 3. Handle Errors Gracefully

```python
try:
    result = asr_model.transcribe([str(audio_path)])
except Exception as e:
    # Clean up even on error
    if temp_path and temp_path.exists():
        cleanup_file(temp_path)
    raise HTTPException(status_code=500, detail=str(e))
```

### 4. Use Appropriate Timeouts

**Client-side** (C#):
```csharp
http.AddStandardResilienceHandler(options =>
{
    options.AttemptTimeout.Timeout = TimeSpan.FromMinutes(5);
    options.TotalRequestTimeout.Timeout = TimeSpan.FromMinutes(5);
});
```

**Server-side** (FastAPI):
```python
# FastAPI doesn't have built-in timeouts
# Use uvicorn with --timeout-keep-alive flag
# uvicorn app:app --timeout-keep-alive 300
```

### 5. Monitor Background Tasks

```python
import logging

def cleanup_file(file_path: Path):
    try:
        if file_path.exists():
            file_path.unlink()
            logging.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logging.error(f"Cleanup failed for {file_path}: {e}")
```

---

## Common Patterns

### Pattern 1: Async Endpoint with Sync Processing

**Use case**: API endpoint that does CPU-bound work

```python
@app.post("/process")
async def process_data(
    background_tasks: BackgroundTasks,
    data: DataModel
):
    # Sync CPU-bound work
    result = expensive_computation(data)
    
    # Async cleanup
    background_tasks.add_task(cleanup_resources)
    
    return result
```

### Pattern 2: Async Endpoint with Async Processing

**Use case**: API endpoint that does I/O-bound work

```python
@app.post("/fetch")
async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### Pattern 3: Mixed Async/Sync

**Use case**: Combination of I/O and CPU work

```python
@app.post("/analyze")
async def analyze_file(
    background_tasks: BackgroundTasks,
    file: UploadFile
):
    # Async I/O
    content = await file.read()
    
    # Sync CPU work
    analysis = run_ml_model(content)
    
    # Background cleanup
    background_tasks.add_task(cleanup_temp_files)
    
    return analysis
```

---

## Troubleshooting

### Issue 1: "RuntimeWarning: coroutine was never awaited"

**Cause**: Calling an async function without `await`

```python
# Bad
result = async_function()

# Good
result = await async_function()
```

### Issue 2: Background tasks not running

**Cause**: Server shutdown before tasks complete

**Solution**: Use startup/shutdown events for critical cleanup

```python
@app.on_event("shutdown")
async def shutdown_event():
    # Ensure critical cleanup completes
    await cleanup_critical_resources()
```

### Issue 3: Timeout errors

**Cause**: Transcription takes longer than client timeout

**Solution**: Increase client timeouts (see OPTION2_IMPLEMENTATION.md)

```csharp
// Extend timeout to 5 minutes
options.AttemptTimeout.Timeout = TimeSpan.FromMinutes(5);
```

### Issue 4: Memory leaks

**Cause**: Temporary files not cleaned up

**Solution**: Always use background tasks for cleanup

```python
# Ensure cleanup even on error
try:
    result = process_file(temp_path)
    background_tasks.add_task(cleanup_file, temp_path)
    return result
except Exception:
    cleanup_file(temp_path)  # Immediate cleanup on error
    raise
```

---

## Performance Tuning

### Server Configuration

**Uvicorn workers** (production):
```bash
uvicorn app:app --workers 4 --timeout-keep-alive 300
```

**Docker** (multi-worker):
```dockerfile
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Client Configuration

**C# HttpClient** (reuse):
```csharp
// Good: Singleton HttpClient
private static readonly HttpClient client = new HttpClient();

// Bad: New HttpClient per request
using var client = new HttpClient();  // Don't do this repeatedly
```

**Blazor** (HTTP resilience):
```csharp
builder.Services.AddHttpClient<TranscriptionService>()
    .AddStandardResilienceHandler(options =>
    {
        options.AttemptTimeout.Timeout = TimeSpan.FromMinutes(5);
    });
```

---

## Additional Resources

### Related Documentation
- **OPTION2_IMPLEMENTATION.md**: HTTP resilience timeouts
- **ARCHITECTURE.md**: System architecture overview
- **USAGE_EXAMPLES.md**: Practical client examples

### FastAPI Resources
- [FastAPI Async](https://fastapi.tiangolo.com/async/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Uvicorn Workers](https://www.uvicorn.org/deployment/)

### C# Async Resources
- [Async/Await Best Practices](https://docs.microsoft.com/en-us/archive/msdn-magazine/2013/march/async-await-best-practices-in-asynchronous-programming)
- [HttpClient Guidelines](https://docs.microsoft.com/en-us/dotnet/fundamentals/networking/http/httpclient-guidelines)

---

## Summary

**Async Mode** in Scenario 4 provides:

✅ **Non-blocking I/O**: Server handles multiple requests concurrently
✅ **Background cleanup**: Files cleaned up after response sent
✅ **Better performance**: Reduced response times
✅ **Scalability**: More concurrent connections with fewer resources
✅ **Modern patterns**: Industry-standard async/await

The implementation balances async benefits (I/O, cleanup) with practical constraints (sync model inference) to provide an efficient, scalable transcription service.

---

**Version**: 1.0  
**Last Updated**: February 2026
