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

            string audioFilePath = args[0];
            string? apiUrl = args.Length > 1 ? args[1] : null;

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

                // Transcribe audio
                Console.WriteLine($"Uploading and transcribing: {Path.GetFileName(audioFilePath)}");
                var result = await TranscribeAudio(client, audioFilePath);

                // Display results
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
            Console.WriteLine("Usage: TranscriptionClient <audio_file> [api_url]");
            Console.WriteLine("\nArguments:");
            Console.WriteLine("  audio_file  Path to audio file (.wav, .mp3, or .flac)");
            Console.WriteLine("  api_url     Optional. API server URL (default: http://localhost:8000)");
            Console.WriteLine("              When running via Aspire, service discovery is automatic");
            Console.WriteLine("\nExamples:");
            Console.WriteLine("  TranscriptionClient audio.mp3");
            Console.WriteLine("  TranscriptionClient audio.wav http://server:8000");
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
}
