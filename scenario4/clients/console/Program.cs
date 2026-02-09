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
    /// <summary>
    /// Configuration options parsed from command-line arguments
    /// </summary>
    class TranscriptionConfig
    {
        public string AudioFilePath { get; set; } = string.Empty;
        public string? ApiUrl { get; set; }
        public bool UseAsyncMode { get; set; }
        public string ModelKey { get; set; } = "parakeet";
        public string? LanguageCode { get; set; }
        public bool IncludeTimestamps { get; set; } = true;
        public bool GenerateAssets { get; set; }
        public string? TranscriptFilePath { get; set; }
        public string? NimUrl { get; set; }
    }
    
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

            // Parse configuration from arguments
            var config = ParseArguments(args);

            // Standalone asset-generation mode: no audio file needed, just a transcript file
            if (config.GenerateAssets && !string.IsNullOrEmpty(config.TranscriptFilePath))
            {
                if (!File.Exists(config.TranscriptFilePath))
                {
                    Console.WriteLine($"Error: Transcript file not found: {config.TranscriptFilePath}");
                    return;
                }

                var transcriptContent = await File.ReadAllTextAsync(config.TranscriptFilePath);
                await RunPodcastAssetGeneration(config, transcriptContent);
                return;
            }
            
            if (string.IsNullOrEmpty(config.AudioFilePath))
            {
                ShowUsage();
                return;
            }

            // Validate file exists
            if (!File.Exists(config.AudioFilePath))
            {
                Console.WriteLine($"Error: File not found: {config.AudioFilePath}");
                return;
            }

            // Validate file extension
            string extension = Path.GetExtension(config.AudioFilePath).ToLower();
            if (extension != ".wav" && extension != ".mp3" && extension != ".flac")
            {
                Console.WriteLine($"Error: Unsupported file format. Supported: .wav, .mp3, .flac");
                return;
            }

            // Create HttpClient with optional service discovery support
            HttpClient client;
            if (config.ApiUrl != null)
            {
                // Standalone mode - use provided URL
                client = new HttpClient { BaseAddress = new Uri(config.ApiUrl) };
            }
            else
            {
                // Try Aspire service discovery first, fall back to default URL
                client = CreateHttpClientWithServiceDiscovery();
            }

            try
            {
                // Check server health
                var effectiveUrl = config.ApiUrl ?? Environment.GetEnvironmentVariable("services__apiserver__http__0") ?? DEFAULT_API_URL;
                Console.WriteLine($"Checking server at {effectiveUrl}...");
                await CheckHealth(client);
                Console.WriteLine("Server is healthy ✓\n");
                
                // Display configuration
                Console.WriteLine($"Configuration:");
                Console.WriteLine($"  Model: {config.ModelKey}");
                if (!string.IsNullOrEmpty(config.LanguageCode))
                {
                    Console.WriteLine($"  Language: {config.LanguageCode}");
                }
                Console.WriteLine($"  Timestamps: {config.IncludeTimestamps}");
                Console.WriteLine($"  Mode: {(config.UseAsyncMode ? "Async" : "Sync")}\n");

                string? transcribedText = null;

                if (config.UseAsyncMode)
                {
                    // Use async job mode
                    Console.WriteLine($"Starting async transcription job for: {Path.GetFileName(config.AudioFilePath)}");
                    transcribedText = await TranscribeAsyncMode(client, config);
                }
                else
                {
                    // Use synchronous mode (original behavior)
                    Console.WriteLine($"Uploading and transcribing: {Path.GetFileName(config.AudioFilePath)}");
                    var result = await TranscribeAudio(client, config);
                    DisplayResult(result);
                    transcribedText = result.text;
                }

                Console.WriteLine("\n✓ Transcription completed successfully");

                // If requested, generate podcast assets from the transcription output
                if (config.GenerateAssets && !string.IsNullOrEmpty(transcribedText))
                {
                    await RunPodcastAssetGeneration(config, transcribedText);
                }
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

        static TranscriptionConfig ParseArguments(string[] args)
        {
            var config = new TranscriptionConfig();
            var nonFlagArgs = new List<string>();
            
            for (int i = 0; i < args.Length; i++)
            {
                var arg = args[i];
                
                if (arg == "--async" || arg == "-a")
                {
                    config.UseAsyncMode = true;
                }
                else if (arg == "--model" || arg == "-m")
                {
                    if (i + 1 < args.Length)
                    {
                        config.ModelKey = args[++i];
                    }
                }
                else if (arg == "--language" || arg == "-l")
                {
                    if (i + 1 < args.Length)
                    {
                        config.LanguageCode = args[++i];
                    }
                }
                else if (arg == "--no-timestamps")
                {
                    config.IncludeTimestamps = false;
                }
                else if (arg == "--generate-assets")
                {
                    config.GenerateAssets = true;
                }
                else if (arg == "--transcript-file")
                {
                    if (i + 1 < args.Length)
                    {
                        config.TranscriptFilePath = args[++i];
                    }
                }
                else if (arg == "--nim-url")
                {
                    if (i + 1 < args.Length)
                    {
                        config.NimUrl = args[++i];
                    }
                }
                else if (!arg.StartsWith("-"))
                {
                    nonFlagArgs.Add(arg);
                }
            }
            
            // First non-flag arg is the audio file
            if (nonFlagArgs.Count > 0)
            {
                config.AudioFilePath = nonFlagArgs[0];
            }
            
            // Second non-flag arg (if present) is the API URL
            if (nonFlagArgs.Count > 1)
            {
                config.ApiUrl = nonFlagArgs[1];
            }
            
            return config;
        }
        
        static void ShowUsage()
        {
            Console.WriteLine("Usage: TranscriptionClient <audio_file> [api_url] [options]");
            Console.WriteLine("       TranscriptionClient --generate-assets --transcript-file <path>");
            Console.WriteLine("\nArguments:");
            Console.WriteLine("  audio_file  Path to audio file (.wav, .mp3, or .flac)");
            Console.WriteLine("  api_url     Optional. API server URL (default: http://localhost:8000)");
            Console.WriteLine("              When running via Aspire, service discovery is automatic");
            Console.WriteLine("\nOptions:");
            Console.WriteLine("  --async, -a          Use async job mode with status polling");
            Console.WriteLine("  --model, -m <model>  Model to use: 'parakeet' (default) or 'canary'");
            Console.WriteLine("  --language, -l <lng> Language for multilingual models: en, es, de, fr");
            Console.WriteLine("  --no-timestamps      Disable timestamp generation");
            Console.WriteLine("  --generate-assets    Generate podcast assets after transcription");
            Console.WriteLine("  --transcript-file <f> Use existing transcript file (with --generate-assets)");
            Console.WriteLine("  --nim-url <url>      NIM LLM endpoint (default: from Aspire env or localhost:8001)");
            Console.WriteLine("\nExamples:");
            Console.WriteLine("  TranscriptionClient audio.mp3");
            Console.WriteLine("  TranscriptionClient audio.wav --async");
            Console.WriteLine("  TranscriptionClient audio.wav --model canary --language es");
            Console.WriteLine("  TranscriptionClient audio.mp3 http://server:8000 --async");
            Console.WriteLine("  TranscriptionClient audio.flac --model canary -l de --async");
            Console.WriteLine("  TranscriptionClient audio.mp3 --generate-assets");
            Console.WriteLine("  TranscriptionClient --generate-assets --transcript-file transcript.txt");
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

        static async Task<TranscriptionResponse> TranscribeAudio(HttpClient client, TranscriptionConfig config)
        {
            using var form = new MultipartFormDataContent();
            using var fileStream = File.OpenRead(config.AudioFilePath);
            using var fileContent = new StreamContent(fileStream);

            fileContent.Headers.ContentType = new MediaTypeHeaderValue("audio/mpeg");
            form.Add(fileContent, "file", Path.GetFileName(config.AudioFilePath));
            
            // Add model parameter
            form.Add(new StringContent(config.ModelKey), "model");
            
            // Add language parameter if specified
            if (!string.IsNullOrEmpty(config.LanguageCode))
            {
                form.Add(new StringContent(config.LanguageCode), "language");
            }
            
            // Add timestamps parameter
            form.Add(new StringContent(config.IncludeTimestamps.ToString().ToLower()), "include_timestamps");

            var response = await client.PostAsync("/transcribe", form);
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<TranscriptionResponse>(json);
            return result ?? throw new Exception("Failed to deserialize response");
        }

        static async Task<string?> TranscribeAsyncMode(HttpClient client, TranscriptionConfig config)
        {
            // Start the job
            using var form = new MultipartFormDataContent();
            using var fileStream = File.OpenRead(config.AudioFilePath);
            using var fileContent = new StreamContent(fileStream);

            fileContent.Headers.ContentType = new MediaTypeHeaderValue("audio/mpeg");
            form.Add(fileContent, "file", Path.GetFileName(config.AudioFilePath));
            
            // Add model parameter
            form.Add(new StringContent(config.ModelKey), "model");
            
            // Add language parameter if specified
            if (!string.IsNullOrEmpty(config.LanguageCode))
            {
                form.Add(new StringContent(config.LanguageCode), "language");
            }
            
            // Add timestamps parameter
            form.Add(new StringContent(config.IncludeTimestamps.ToString().ToLower()), "include_timestamps");

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
                    return result.text;
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

        /// <summary>
        /// Calls the NVIDIA NIM LLM container to generate podcast episode metadata
        /// from the supplied transcript text.
        /// </summary>
        static async Task RunPodcastAssetGeneration(TranscriptionConfig config, string transcript)
        {
            Console.WriteLine("\n=== PODCAST ASSET GENERATION ===\n");

            // Resolve the NIM endpoint: explicit flag > Aspire env var > default
            var nimEndpoint = config.NimUrl
                ?? Environment.GetEnvironmentVariable("services__nim-llm__http__0")
                ?? "http://localhost:8001";

            Console.WriteLine($"NIM endpoint: {nimEndpoint}");
            Console.WriteLine($"Transcript length: {transcript.Length} characters");
            Console.WriteLine("Sending to NIM LLM for analysis...\n");

            var chatApi = new OpenAI.Chat.ChatClient(
                model: "meta/llama-3.2-3b-instruct",
                // NIM local containers don't validate API keys; the SDK requires a non-empty value
                credential: new System.ClientModel.ApiKeyCredential("not-required"),
                options: new OpenAI.OpenAIClientOptions
                {
                    Endpoint = new Uri(nimEndpoint)
                });

            var roleMsg = new OpenAI.Chat.SystemChatMessage(
                "You are a podcast production assistant. "
                + "Given a transcript, generate a concise episode title, "
                + "an engaging episode description (2-3 sentences), "
                + "and 5-8 relevant tags.");

            var userMsg = new OpenAI.Chat.UserChatMessage(
                "Here is the transcript:\n\n" + transcript + "\n\n"
                + "Generate the following in JSON format:\n"
                + "- title\n- description\n- tags (array of strings)");

            var opts = new OpenAI.Chat.ChatCompletionOptions
            {
                ResponseFormat = OpenAI.Chat.ChatResponseFormat.CreateJsonObjectFormat()
            };

            var reply = await chatApi.CompleteChatAsync(
                [roleMsg, userMsg], opts);

            var rawJson = reply.Value.Content[0].Text;
            var episode = JsonSerializer.Deserialize<NimEpisodeResult>(rawJson,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

            if (episode is null)
            {
                Console.WriteLine("⚠️ Could not parse the NIM response.");
                Console.WriteLine($"Raw response:\n{rawJson}");
                return;
            }

            Console.WriteLine($"  Title:       {episode.Title}");
            Console.WriteLine($"  Description: {episode.Description}");
            Console.WriteLine($"  Tags:        {string.Join(", ", episode.Tags ?? [])}");
            Console.WriteLine("\n✓ Podcast asset generation complete");
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
        public string model { get; set; } = "";
        public string? language { get; set; }
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

    /// <summary>
    /// Represents the JSON response from NIM for podcast episode metadata.
    /// </summary>
    class NimEpisodeResult
    {
        public string Title { get; set; } = "";
        public string Description { get; set; } = "";
        public string[]? Tags { get; set; }
    }
}
