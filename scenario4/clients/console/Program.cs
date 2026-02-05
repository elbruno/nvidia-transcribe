using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.ServiceDiscovery;

namespace TranscriptionClient
{
    class Program
    {
        private const string DEFAULT_API_URL = "http://localhost:8000";

        static async Task Main(string[] args)
        {
            Console.WriteLine("=== NVIDIA ASR Transcription Client ===\n");

            if (args.Length < 1)
            {
                ShowUsage();
                return;
            }

            // Check for async mode flag
            bool useAsyncMode = args.Any(a => a == "--async" || a == "-a");
            
            // Filter out flags from arguments
            var fileArgs = args.Where(a => !a.StartsWith("-")).ToArray();
            
            if (fileArgs.Length < 1)
            {
                ShowUsage();
                return;
            }

            string audioFilePath = fileArgs[0];
            string? apiUrl = fileArgs.Length > 1 ? fileArgs[1] : null;

            // Validate file exists
            if (!File.Exists(audioFilePath))
            {
                Console.WriteLine($"Error: File not found: {audioFilePath}");
                return;
            }

            // Validate file extension
            string extension = Path.GetExtension(audioFilePath).ToLower();
            if (extension != ".wav" && extension != ".mp3" && extension != ".flac")
            {
                Console.WriteLine($"Error: Unsupported file format. Supported: .wav, .mp3, .flac");
                return;
            }

            // Create HttpClient with optional service discovery support
            HttpClient client;
            if (apiUrl != null)
            {
                // Standalone mode - use provided URL
                client = new HttpClient { BaseAddress = new Uri(apiUrl) };
            }
            else
            {
                // Try Aspire service discovery first, fall back to default URL
                client = CreateHttpClientWithServiceDiscovery();
            }

            try
            {
                // Check server health
                var effectiveUrl = apiUrl ?? Environment.GetEnvironmentVariable("services__apiserver__http__0") ?? DEFAULT_API_URL;
                Console.WriteLine($"Checking server at {effectiveUrl}...");
                await CheckHealth(client);
                Console.WriteLine("Server is healthy ✓\n");

                if (useAsyncMode)
                {
                    // Use async job mode
                    Console.WriteLine($"Starting async transcription job for: {Path.GetFileName(audioFilePath)}");
                    await TranscribeAsyncMode(client, audioFilePath);
                }
                else
                {
                    // Use synchronous mode (original behavior)
                    Console.WriteLine($"Uploading and transcribing: {Path.GetFileName(audioFilePath)}");
                    var result = await TranscribeAudio(client, audioFilePath);
                    DisplayResult(result);
                }

                Console.WriteLine("\n✓ Transcription completed successfully");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n✗ Error: {ex.Message}");
                Environment.Exit(1);
            }
            finally
            {
                client.Dispose();
            }
        }

        static HttpClient CreateHttpClientWithServiceDiscovery()
        {
            // Check if running under Aspire (service discovery available)
            var serviceEndpoint = Environment.GetEnvironmentVariable("services__apiserver__http__0");

            if (!string.IsNullOrEmpty(serviceEndpoint))
            {
                // Running under Aspire - use service discovery
                Console.WriteLine("Using Aspire service discovery");
                return new HttpClient { BaseAddress = new Uri(serviceEndpoint) };
            }
            else
            {
                // Standalone mode - use default URL
                Console.WriteLine($"Using default API URL: {DEFAULT_API_URL}");
                return new HttpClient { BaseAddress = new Uri(DEFAULT_API_URL) };
            }
        }

        static void ShowUsage()
        {
            Console.WriteLine("Usage: TranscriptionClient <audio_file> [api_url] [--async]");
            Console.WriteLine("\nArguments:");
            Console.WriteLine("  audio_file  Path to audio file (.wav, .mp3, or .flac)");
            Console.WriteLine("  api_url     Optional. API server URL (default: http://localhost:8000)");
            Console.WriteLine("              When running via Aspire, service discovery is automatic");
            Console.WriteLine("  --async, -a Optional. Use async job mode with status polling");
            Console.WriteLine("\nExamples:");
            Console.WriteLine("  TranscriptionClient audio.mp3");
            Console.WriteLine("  TranscriptionClient audio.wav --async");
            Console.WriteLine("  TranscriptionClient audio.wav http://server:8000");
            Console.WriteLine("  TranscriptionClient audio.mp3 http://server:8000 --async");
        }

        static async Task CheckHealth(HttpClient client)
        {
            var response = await client.GetAsync("/health");
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var health = JsonSerializer.Deserialize<HealthResponse>(json);

            if (health == null || !health.model_loaded)
            {
                throw new Exception("Server model not loaded");
            }
        }

        static async Task<TranscriptionResponse> TranscribeAudio(HttpClient client, string filePath)
        {
            using var form = new MultipartFormDataContent();
            using var fileStream = File.OpenRead(filePath);
            using var fileContent = new StreamContent(fileStream);

            fileContent.Headers.ContentType = new MediaTypeHeaderValue("audio/mpeg");
            form.Add(fileContent, "file", Path.GetFileName(filePath));

            var response = await client.PostAsync("/transcribe", form);
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<TranscriptionResponse>(json);
            return result ?? throw new Exception("Failed to deserialize response");
        }

        static async Task TranscribeAsyncMode(HttpClient client, string filePath)
        {
            // Start the job
            using var form = new MultipartFormDataContent();
            using var fileStream = File.OpenRead(filePath);
            using var fileContent = new StreamContent(fileStream);

            fileContent.Headers.ContentType = new MediaTypeHeaderValue("audio/mpeg");
            form.Add(fileContent, "file", Path.GetFileName(filePath));

            Console.WriteLine("Uploading file...");
            var response = await client.PostAsync("/transcribe/async", form);
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var jobStart = JsonSerializer.Deserialize<JobStartResponse>(json);
            
            if (jobStart == null)
                throw new Exception("Failed to start job");

            Console.WriteLine($"✓ Job started: {jobStart.job_id}");
            Console.WriteLine($"Status: {jobStart.status}");
            Console.WriteLine("\nMonitoring job progress (Ctrl+C to cancel)...");

            // Poll for completion
            const int maxAttempts = 120; // 10 minutes
            int attempts = 0;

            while (attempts < maxAttempts)
            {
                await Task.Delay(5000); // Poll every 5 seconds
                attempts++;

                var statusResponse = await client.GetAsync($"/jobs/{jobStart.job_id}/status");
                statusResponse.EnsureSuccessStatusCode();

                var statusJson = await statusResponse.Content.ReadAsStringAsync();
                var jobInfo = JsonSerializer.Deserialize<JobInfo>(statusJson);

                if (jobInfo == null)
                    throw new Exception("Failed to get job status");

                if (jobInfo.status == "completed")
                {
                    Console.WriteLine("\n✓ Job completed! Retrieving results...");
                    
                    var resultResponse = await client.GetAsync($"/jobs/{jobStart.job_id}/result");
                    resultResponse.EnsureSuccessStatusCode();

                    var resultJson = await resultResponse.Content.ReadAsStringAsync();
                    var result = JsonSerializer.Deserialize<TranscriptionResponse>(resultJson);
                    
                    if (result == null)
                        throw new Exception("Failed to get job result");

                    DisplayResult(result);
                    return;
                }
                else if (jobInfo.status == "failed")
                {
                    throw new Exception($"Job failed: {jobInfo.error ?? "Unknown error"}");
                }
                else if (jobInfo.status == "cancelled")
                {
                    throw new Exception("Job was cancelled");
                }
                else
                {
                    // Still processing
                    if (attempts % 6 == 0) // Log every 30 seconds
                    {
                        Console.WriteLine($"Status: {jobInfo.status} (elapsed: {attempts * 5}s)");
                    }
                }
            }

            throw new Exception("Job polling timeout after 10 minutes");
        }

        static void DisplayResult(TranscriptionResponse result)
        {
            Console.WriteLine("\n=== TRANSCRIPTION RESULT ===");
            Console.WriteLine($"File: {result.filename}");
            Console.WriteLine($"Timestamp: {result.timestamp}");
            Console.WriteLine($"\nText:\n{result.text}");

            if (result.segments != null && result.segments.Length > 0)
            {
                Console.WriteLine($"\n=== SEGMENTS ({result.segments.Length}) ===");
                for (int i = 0; i < Math.Min(5, result.segments.Length); i++)
                {
                    var seg = result.segments[i];
                    Console.WriteLine($"[{FormatTime(seg.start)} - {FormatTime(seg.end)}] {seg.text}");
                }
                if (result.segments.Length > 5)
                {
                    Console.WriteLine($"... and {result.segments.Length - 5} more segments");
                }
            }
        }

        static string FormatTime(double seconds)
        {
            TimeSpan ts = TimeSpan.FromSeconds(seconds);
            return ts.ToString(@"hh\:mm\:ss\.fff");
        }
    }

    // Response models
    class HealthResponse
    {
        public string status { get; set; } = "";
        public bool model_loaded { get; set; }
        public string model_name { get; set; } = "";
    }

    class TranscriptionResponse
    {
        public string text { get; set; } = "";
        public Segment[] segments { get; set; } = Array.Empty<Segment>();
        public string filename { get; set; } = "";
        public string timestamp { get; set; } = "";
    }

    class Segment
    {
        public double start { get; set; }
        public double end { get; set; }
        public string text { get; set; } = "";
    }

    class JobStartResponse
    {
        public string job_id { get; set; } = "";
        public string status { get; set; } = "";
        public string message { get; set; } = "";
    }

    class JobInfo
    {
        public string job_id { get; set; } = "";
        public string status { get; set; } = "";
        public string filename { get; set; } = "";
        public string created_at { get; set; } = "";
        public string? completed_at { get; set; }
        public string? error { get; set; }
        public TranscriptionResponse? result { get; set; }
    }
}
