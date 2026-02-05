using System.Net.Http.Headers;
using System.Text.Json;
using Microsoft.AspNetCore.Components.Forms;

namespace TranscriptionWebApp2.Services;

/// <summary>
/// Service for communicating with the NVIDIA ASR Transcription API.
/// </summary>
public class TranscriptionApiService
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<TranscriptionApiService> _logger;
    private const long MaxFileSize = 50 * 1024 * 1024; // 50MB

    public TranscriptionApiService(
        IHttpClientFactory httpClientFactory,
        ILogger<TranscriptionApiService> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    /// <summary>
    /// Transcribes an audio file using the API.
    /// </summary>
    public async Task<TranscriptionResponse> TranscribeAsync(IBrowserFile file)
    {
        var client = _httpClientFactory.CreateClient("api");

        // Buffer file content to support retry on transient failures
        // (StreamContent cannot be re-read after the first attempt)
        await using var stream = file.OpenReadStream(maxAllowedSize: MaxFileSize);
        using var memoryStream = new MemoryStream();
        await stream.CopyToAsync(memoryStream);
        var fileBytes = memoryStream.ToArray();

        using var content = new MultipartFormDataContent();
        var fileContent = new ByteArrayContent(fileBytes);
        fileContent.Headers.ContentType = new MediaTypeHeaderValue(GetContentType(file.Name));
        content.Add(fileContent, "file", file.Name);

        _logger.LogInformation("Transcribing file: {FileName}", file.Name);

        var response = await client.PostAsync("/transcribe", content);
        
        if (!response.IsSuccessStatusCode)
        {
            var errorContent = await response.Content.ReadAsStringAsync();
            _logger.LogError("Transcription failed: {StatusCode} - {Error}", response.StatusCode, errorContent);
            throw new HttpRequestException($"Server returned {response.StatusCode}: {errorContent}");
        }

        var json = await response.Content.ReadAsStringAsync();
        var result = JsonSerializer.Deserialize<TranscriptionResponse>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        return result ?? throw new InvalidOperationException("Failed to deserialize response");
    }

    /// <summary>
    /// Checks the health of the API server.
    /// </summary>
    public async Task<HealthResponse> CheckHealthAsync()
    {
        var client = _httpClientFactory.CreateClient("api");
        var response = await client.GetAsync("/health");
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        var result = JsonSerializer.Deserialize<HealthResponse>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        return result ?? throw new InvalidOperationException("Failed to deserialize health response");
    }

    /// <summary>
    /// Starts an asynchronous transcription job.
    /// </summary>
    public async Task<JobStartResponse> StartTranscriptionJobAsync(IBrowserFile file)
    {
        var client = _httpClientFactory.CreateClient("api");

        // Buffer file content to support retry on transient failures
        // (StreamContent cannot be re-read after the first attempt)
        await using var stream = file.OpenReadStream(maxAllowedSize: MaxFileSize);
        using var memoryStream = new MemoryStream();
        await stream.CopyToAsync(memoryStream);
        var fileBytes = memoryStream.ToArray();

        using var content = new MultipartFormDataContent();
        var fileContent = new ByteArrayContent(fileBytes);
        fileContent.Headers.ContentType = new MediaTypeHeaderValue(GetContentType(file.Name));
        content.Add(fileContent, "file", file.Name);

        _logger.LogInformation("Starting async transcription job for: {FileName}", file.Name);

        var response = await client.PostAsync("/transcribe/async", content);
        
        if (!response.IsSuccessStatusCode)
        {
            var errorContent = await response.Content.ReadAsStringAsync();
            _logger.LogError("Failed to start job: {StatusCode} - {Error}", response.StatusCode, errorContent);
            throw new HttpRequestException($"Server returned {response.StatusCode}: {errorContent}");
        }

        var json = await response.Content.ReadAsStringAsync();
        var result = JsonSerializer.Deserialize<JobStartResponse>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        return result ?? throw new InvalidOperationException("Failed to deserialize job start response");
    }

    /// <summary>
    /// Gets the status of a transcription job.
    /// </summary>
    public async Task<JobInfo> GetJobStatusAsync(string jobId)
    {
        var client = _httpClientFactory.CreateClient("api");
        var response = await client.GetAsync($"/jobs/{jobId}/status");
        
        if (!response.IsSuccessStatusCode)
        {
            var errorContent = await response.Content.ReadAsStringAsync();
            _logger.LogError("Failed to get job status: {StatusCode} - {Error}", response.StatusCode, errorContent);
            throw new HttpRequestException($"Server returned {response.StatusCode}: {errorContent}");
        }

        var json = await response.Content.ReadAsStringAsync();
        var result = JsonSerializer.Deserialize<JobInfo>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        return result ?? throw new InvalidOperationException("Failed to deserialize job info");
    }

    /// <summary>
    /// Gets the result of a completed transcription job.
    /// </summary>
    public async Task<TranscriptionResponse> GetJobResultAsync(string jobId)
    {
        var client = _httpClientFactory.CreateClient("api");
        var response = await client.GetAsync($"/jobs/{jobId}/result");
        
        if (!response.IsSuccessStatusCode)
        {
            var errorContent = await response.Content.ReadAsStringAsync();
            _logger.LogError("Failed to get job result: {StatusCode} - {Error}", response.StatusCode, errorContent);
            throw new HttpRequestException($"Server returned {response.StatusCode}: {errorContent}");
        }

        var json = await response.Content.ReadAsStringAsync();
        var result = JsonSerializer.Deserialize<TranscriptionResponse>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        return result ?? throw new InvalidOperationException("Failed to deserialize transcription response");
    }

    /// <summary>
    /// Cancels a transcription job.
    /// </summary>
    public async Task<CancelJobResponse> CancelJobAsync(string jobId)
    {
        var client = _httpClientFactory.CreateClient("api");
        var response = await client.PostAsync($"/jobs/{jobId}/cancel", null);
        
        if (!response.IsSuccessStatusCode)
        {
            var errorContent = await response.Content.ReadAsStringAsync();
            _logger.LogError("Failed to cancel job: {StatusCode} - {Error}", response.StatusCode, errorContent);
            throw new HttpRequestException($"Server returned {response.StatusCode}: {errorContent}");
        }

        var json = await response.Content.ReadAsStringAsync();
        var result = JsonSerializer.Deserialize<CancelJobResponse>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        return result ?? throw new InvalidOperationException("Failed to deserialize cancel response");
    }

    private static string GetContentType(string fileName)
    {
        var extension = Path.GetExtension(fileName).ToLowerInvariant();
        return extension switch
        {
            ".mp3" => "audio/mpeg",
            ".wav" => "audio/wav",
            ".flac" => "audio/flac",
            _ => "application/octet-stream"
        };
    }
}

/// <summary>
/// Response model for transcription results.
/// </summary>
public class TranscriptionResponse
{
    public string Text { get; set; } = string.Empty;
    public Segment[] Segments { get; set; } = [];
    public string Filename { get; set; } = string.Empty;
    public string Timestamp { get; set; } = string.Empty;
}

/// <summary>
/// Segment model representing a timestamped portion of the transcription.
/// </summary>
public class Segment
{
    public double Start { get; set; }
    public double End { get; set; }
    public string Text { get; set; } = string.Empty;
}

/// <summary>
/// Response model for health check.
/// </summary>
public class HealthResponse
{
    public string Status { get; set; } = string.Empty;
    public bool ModelLoaded { get; set; }
    public string ModelName { get; set; } = string.Empty;
}

/// <summary>
/// Response model when starting a new job.
/// </summary>
public class JobStartResponse
{
    public string JobId { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
}

/// <summary>
/// Information about a transcription job.
/// </summary>
public class JobInfo
{
    public string JobId { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string Filename { get; set; } = string.Empty;
    public string CreatedAt { get; set; } = string.Empty;
    public string? CompletedAt { get; set; }
    public string? Error { get; set; }
    public TranscriptionResponse? Result { get; set; }
}

/// <summary>
/// Response model for job cancellation.
/// </summary>
public class CancelJobResponse
{
    public string Message { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
}
