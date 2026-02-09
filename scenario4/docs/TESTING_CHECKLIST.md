# Option 2 Testing Checklist

This checklist helps verify that Option 2 (Extended HTTP Resilience Timeouts) is working correctly.

## Prerequisites

Before testing, ensure:
- [x] ✅ Option 2 is implemented in `ServiceDefaults/Extensions.cs`
- [x] ✅ All projects build successfully (`dotnet build`)
- [x] ✅ Documentation is updated (README.md, OPTION2_IMPLEMENTATION.md)

## Testing Steps

### 1. Restart Aspire Application

Since Option 2 changes the .NET ServiceDefaults configuration, you need to restart Aspire:

```bash
# Stop any running Aspire instance (Ctrl+C if running in terminal)

# Navigate to AppHost directory
cd scenario4/AppHost

# Start Aspire
dotnet run
```

**Expected Result**: 
- Aspire dashboard opens in browser
- Server container starts and loads model
- Webapp starts successfully
- No timeout-related errors in logs

### 2. Test Short Audio File (< 1 minute)

1. Open the Blazor webapp from Aspire dashboard
2. Navigate to `/transcribe` page
3. Upload a short audio file (e.g., 30-60 seconds)
4. Click "Transcribe"

**Expected Result**:
- ✅ Transcription completes in < 30 seconds (GPU) or < 2 minutes (CPU)
- ✅ Full text displayed
- ✅ Timestamp segments shown
- ✅ No timeout errors

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

### 3. Test Medium Audio File (3-5 minutes)

1. Upload a medium-length audio file (3-5 minutes)
2. Click "Transcribe"
3. Observe processing time

**Expected Result**:
- ✅ Transcription completes within 5 minutes
- ✅ No "request timeout" or "circuit breaker" errors
- ✅ Processing time on GPU: ~15-75 seconds
- ✅ Processing time on CPU: ~1.5-7.5 minutes
- ✅ Results displayed correctly

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

### 4. Test Long Audio File (~10 minutes)

1. Upload a longer audio file (8-10 minutes)
2. Click "Transcribe"
3. Monitor both webapp and server logs in Aspire dashboard

**Expected Result**:
- ✅ On GPU: Completes in ~1-2.5 minutes (well within 5-minute timeout)
- ⚠️ On CPU: Will likely exceed 5-minute timeout (4-15 minutes to process)
  - This is expected behavior - CPU mode is not suitable for very long files
  - Option 2 ensures timeout happens at 5 minutes (not 30 seconds)
  - For long files on CPU, consider enabling GPU or splitting the audio
- ✅ No premature timeout errors (request allowed full 5 minutes)
- ✅ If timeout occurs, it's after 5 minutes, not 30 seconds

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

**Note**: This test validates that Option 2 extends the timeout window, not that all files complete within it. Success means timeouts occur at 5 minutes rather than 30 seconds.

### 5. Monitor Aspire Dashboard

While transcribing, check Aspire dashboard:

1. **Server Logs**: Watch for processing messages
   - ✅ "Transcribing: [filename]" appears
   - ✅ Model processes audio
   - ✅ Response sent successfully

2. **Webapp Logs**: Monitor HTTP client activity
   - ✅ POST request to /transcribe sent
   - ✅ Request waits for response (doesn't timeout at 30s)
   - ✅ Response received successfully

3. **Traces**: Check OpenTelemetry traces
   - ✅ Request duration shown
   - ✅ No timeout or circuit breaker failures

**Status**: ⬜ Not Tested | ✅ Passed | ❌ Failed

### 6. Verify Timeout Configuration

Confirm the timeout values in the running application:

```bash
# Check ServiceDefaults/Extensions.cs lines 34-39
cat scenario4/ServiceDefaults/Extensions.cs | grep -A 5 "AddStandardResilienceHandler"
```

**Expected Output**:
```csharp
http.AddStandardResilienceHandler(options =>
{
    options.AttemptTimeout.Timeout = TimeSpan.FromMinutes(5);
    options.TotalRequestTimeout.Timeout = TimeSpan.FromMinutes(5);
    options.CircuitBreaker.SamplingDuration = TimeSpan.FromMinutes(5);
});
```

**Status**: ⬜ Not Checked | ✅ Verified | ❌ Incorrect

## Common Issues and Solutions

### Issue: Still Getting Timeout After 30 Seconds

**Cause**: Old .NET assemblies cached or Aspire not restarted

**Solution**:
```bash
# Clean build
cd scenario4
dotnet clean
dotnet build

# Restart Aspire
cd AppHost
dotnet run
```

### Issue: Request Timeout After 5 Minutes on CPU

**Cause**: Audio file too long for CPU processing within timeout

**Solution**:
- ✅ This is expected behavior for very long files on CPU
- Enable GPU acceleration (see GPU_SETUP_GUIDE.md)
- Or use shorter audio files
- Or increase timeout further in Extensions.cs (not recommended)

### Issue: Docker Container Not Using GPU

**Cause**: NVIDIA Container Toolkit not installed or configured

**Solution**:
- See GPU_SETUP_GUIDE.md for setup instructions
- CPU fallback will work but is slower
- Transcription will take longer and may approach timeout limits

## Results Summary

| Test Case | Expected Duration (GPU) | Expected Duration (CPU) | Status |
|-----------|------------------------|-------------------------|--------|
| Short file (1 min) | < 30s | < 2m | ⬜ |
| Medium file (5 min) | ~1m | ~4-5m | ⬜ |
| Long file (10 min) | ~2m | > 5m (will timeout) | ⬜ |
| No premature timeout | 5 min max (not 30s) | 5 min max (not 30s) | ⬜ |

## Success Criteria

Option 2 is working correctly if:

- ✅ All projects build without errors
- ✅ Aspire starts successfully
- ✅ Short audio files transcribe without errors
- ✅ Medium audio files complete within 5 minutes (on GPU or CPU)
- ✅ No timeout errors before 5 minutes
- ✅ Webapp displays results correctly
- ✅ Server logs show successful processing

## Next Steps After Testing

Once testing confirms Option 2 is working:

1. ✅ Mark this issue as resolved
2. 📝 Document any specific timing observations
3. 🚀 Deploy to production environment (if applicable)
4. 📊 Monitor production logs for any timeout-related issues

## Additional Resources

- [OPTION2_IMPLEMENTATION.md](OPTION2_IMPLEMENTATION.md) - Technical details
- [README.md](../README.md) - General usage guide
- [GPU_SETUP_GUIDE.md](GPU_SETUP_GUIDE.md) - GPU acceleration setup
- [Troubleshooting](../README.md#troubleshooting) - Common issues

## Notes

- GPU mode significantly reduces transcription time and makes timeout less likely
- CPU mode is slower but functional for shorter files
- The 5-minute timeout is a balance between reliability and user experience
- For production, consider queueing very long files or splitting them
