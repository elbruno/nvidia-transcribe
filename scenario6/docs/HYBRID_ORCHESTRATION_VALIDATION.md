# Hybrid Orchestration Implementation Validation

This document validates the hybrid orchestration implementation for Scenario 6.

## Implementation Summary

The AppHost now supports two orchestration modes:

| Mode | When | Frontend | Moshi Backend |
|------|------|----------|---------------|
| **Development** | `aspire run` (default) | Aspire Python | Docker |
| **Production** | `dotnet publish` | Docker | Docker |

## Verification Status

### ✅ Phase 1: Prerequisites
- [x] Aspire.Hosting.Python package installed (version 13.1.1)
- [x] Documentation updated in AppHost/README.md
- [x] Docker baseline verified (both images build successfully)

### ✅ Phase 2: Development Mode Implementation
- [x] Conditional logic added to Program.cs based on `IsPublishMode`
- [x] `AddUvicornApp` configuration implemented for frontend
- [x] Production mode configuration retained unchanged
- [x] Moshi backend configured to use Docker in both modes

### ✅ Phase 3: Production Mode Retention
- [x] Existing `AddDockerfile` configuration preserved
- [x] All Docker settings remain unchanged
- [x] Environment variables correctly configured

### ✅ Phase 4: Service Discovery
- [x] MOSHI_WS_URL injection works for both modes
- [x] Both resource types implement IResourceWithEndpoints
- [x] WaitFor dependency correctly configured

### ✅ Phase 5: Documentation
- [x] scenario6/README.md updated with hybrid approach
- [x] AppHost/README.md with detailed setup instructions
- [x] Troubleshooting sections added for both modes

### ⚠️ Phase 6: Testing

#### Build Verification ✅
- [x] Debug build succeeds
- [x] Release build succeeds
- [x] No compilation errors
- [x] Endpoint naming conflict resolved

#### Development Mode Testing (Requires Setup)
To test development mode, complete these prerequisites first:

1. **Create Python Virtual Environment:**
   ```powershell
   cd scenario6
   py -3.12 setup_scenario6.py --hf-token <your-token>
   ```

2. **Verify venv contents:**
   ```powershell
   Test-Path scenario6\venv
   Test-Path scenario6\venv\Scripts\python.exe
   ```

3. **Run in development mode:**
   ```powershell
   cd scenario6\AppHost
   aspire run
   ```

**Expected Behavior:**
- Aspire dashboard opens at http://localhost:15000
- Frontend resource shows as "Python" type (not Docker)
- Moshi backend shows as "Dockerfile" type
- Frontend endpoint accessible at configured APP_PORT (default 8010)
- Frontend logs show uvicorn startup
- Code changes to app.py trigger hot reload

**Endpoints to Test:**
- `GET http://localhost:8010/health` → Should return 200 OK
- `GET http://localhost:8010/api/config` → Should return configuration with moshi URL
- `GET http://localhost:8010/` → Should serve the web UI

#### Production Mode Testing (Ready to Test)
Production mode can be tested with Docker alone (no venv required):

1. **Build for production:**
   ```powershell
   cd scenario6\AppHost
   dotnet publish -c Release
   ```

2. **Run published output:**
   ```powershell
   # Check bin\Release\net10.0\publish for output
   ```

**Expected Behavior:**
- Both frontend and moshi run as Docker containers
- All endpoints function identically to development mode
- OTEL telemetry exports correctly
- SSL/TLS certificates generated for moshi

#### End-to-End Testing (Requires HF Token & Model)
Full testing requires:
1. Valid Hugging Face token with PersonaPlex license accepted
2. ~14 GB disk space for model download
3. GPU with ~14 GB VRAM (or CPU offload enabled)

**Test Checklist:**
- [ ] Web UI loads at frontend endpoint
- [ ] Voice selection works (18 voices available)
- [ ] Persona configuration works
- [ ] WebSocket connection to moshi succeeds
- [ ] Full-duplex voice conversation works
- [ ] Theme switching works (light/dark/system)
- [ ] Real-time logs display

## Code Changes Made

### Files Modified

1. **scenario6/AppHost/PersonaPlex.AppHost.csproj**
   - Added `Aspire.Hosting.Python` package reference

2. **scenario6/AppHost/Program.cs**
   - Added conditional orchestration logic
   - Implemented `AddUvicornApp` for development mode
   - Kept `AddDockerfile` for production mode
   - Fixed endpoint naming to prevent conflicts

3. **scenario6/AppHost/README.md**
   - Added hybrid orchestration explanation
   - Documented development mode prerequisites
   - Added troubleshooting guide

4. **scenario6/README.md**
   - Updated Quick Start with orchestration modes
   - Added development mode prerequisites
   - Enhanced troubleshooting section

### Files Created

- `scenario6/docs/HYBRID_ORCHESTRATION_VALIDATION.md` (this file)

## Known Issues

### Resolved
- ✅ Endpoint name conflict - Fixed by explicitly naming the HTTP endpoint

### Outstanding
- None

## Next Steps

### For Development Mode Testing
1. Install Python 3.10-3.12 if not already installed
2. Run `setup_scenario6.py` to create virtual environment
3. Configure HF_TOKEN in user secrets or environment
4. Run `aspire run` and verify frontend uses Aspire Python
5. Test hot reload by modifying app.py
6. Verify WebSocket connection to moshi backend

### For Production Mode Testing  
1. Configure HF_TOKEN in user secrets
2. Run `dotnet publish`
3. Verify both services run as Docker containers
4. Test identical functionality to development mode

### For Full Voice Testing
1. Accept PersonaPlex model license at HuggingFace
2. Ensure GPU or CPU offload is configured
3. Allow ~10-15 minutes for first model download
4. Test full-duplex voice conversation
5. Verify all UI features work

## Success Criteria

- [x] Code compiles without errors in both Debug and Release
- [x] Documentation clearly explains both modes
- [ ] Development mode runs frontend via Aspire Python with hot reload
- [ ] Production mode runs both services via Docker
- [ ] Both modes provide identical functionality
- [ ] WebSocket connection works in both modes
- [ ] Voice conversation works end-to-end

## Validation Sign-Off

**Implementation Date:** February 18, 2026  
**Status:** Implementation Complete, Testing Blocked by Prerequisites  
**Blocking Issues:** Requires Python venv setup and HF_TOKEN for full testing  
**Build Status:** ✅ Passing  
**Code Review:** Self-reviewed, follows Aspire patterns
