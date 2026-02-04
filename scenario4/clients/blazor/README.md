# Blazor Web App Client for NVIDIA ASR Transcription

## Description

Browser-based web application for audio transcription using the NVIDIA ASR API.

## Requirements

- .NET 8.0 SDK
- Modern web browser (Chrome, Edge, Firefox, Safari)

## Installation

```bash
cd scenario4/clients/blazor
dotnet restore
```

## Configuration

Edit `wwwroot/appsettings.json` to set the API URL:
```json
{
  "ApiUrl": "http://your-server:8000"
}
```

## Usage

**Development mode:**
```bash
dotnet run
```

**Watch mode (auto-reload):**
```bash
dotnet watch run
```

Then open your browser to the displayed URL (typically `http://localhost:5000`)

## Building for Production

```bash
dotnet publish -c Release -o ./publish
```

The output in `./publish/wwwroot` can be hosted on any static web server.

## Features

- 🎙️ Audio file upload (WAV, MP3, FLAC)
- ⏳ Real-time progress indication
- 📝 Full transcription text display
- ⏱️ Timestamp segments with time codes
- ⚠️ Error handling and user feedback
- 📱 Responsive design

## Deployment

### Azure Static Web Apps

```bash
# Build
dotnet publish -c Release -o ./publish

# Deploy to Azure
az staticwebapp create \
  --name nvidia-asr-client \
  --resource-group <your-rg> \
  --source ./publish/wwwroot \
  --location westus2
```

### Static Web Server

Serve the `publish/wwwroot` directory with any static web server:

```bash
# Python
python -m http.server -d publish/wwwroot 8080

# Node.js
npx serve publish/wwwroot

# nginx (configure to serve from publish/wwwroot)
```

## Customization

### Styling
Edit `wwwroot/css/app.css` to customize the appearance.

### API Client
Modify `Pages/Index.razor` to adjust API communication logic.

## Troubleshooting

### CORS Errors
Ensure the server has CORS enabled for your web app origin.

### File Upload Size Limit
The default maximum file size is 50MB. Adjust in `Pages/Index.razor`:
```csharp
selectedFile.OpenReadStream(maxAllowedSize: 50 * 1024 * 1024)
```

### API URL
Check that `wwwroot/appsettings.json` has the correct server URL.
