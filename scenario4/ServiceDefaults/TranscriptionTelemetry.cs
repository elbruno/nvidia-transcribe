using Azure.Monitor.OpenTelemetry.AspNetCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using OpenTelemetry;
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;

namespace Microsoft.Extensions.Hosting
{
    /// <summary>
    /// Transcription service telemetry configuration for Azure monitoring.
    /// Enables Azure Monitor integration when connection string is available.
    /// </summary>
    public static class TranscriptionTelemetryExtensions
    {
        public static IHostApplicationBuilder ConfigureTranscriptionTelemetry(this IHostApplicationBuilder appBuilder)
        {
            var azureConnectionString = appBuilder.Configuration["NVIDIA_TRANSCRIBE_INSIGHTS_CONNECTION"] 
                ?? appBuilder.Configuration["APPINSIGHTS_CONN_STR"]
                ?? appBuilder.Configuration["APPLICATIONINSIGHTS_CONNECTION_STRING"];
            
            var hasAzureConfig = !string.IsNullOrWhiteSpace(azureConnectionString);
            
            // Configure OpenTelemetry logging
            appBuilder.Logging.AddOpenTelemetry(logOptions =>
            {
                logOptions.IncludeFormattedMessage = true;
                logOptions.IncludeScopes = true;
            });
            
            // Configure OpenTelemetry services
            appBuilder.Services.AddOpenTelemetry()
                .WithMetrics(metricOptions =>
                {
                    metricOptions
                        .AddAspNetCoreInstrumentation()
                        .AddHttpClientInstrumentation()
                        .AddRuntimeInstrumentation();
                })
                .WithTracing(traceOptions =>
                {
                    traceOptions
                        .AddSource(appBuilder.Environment.ApplicationName)
                        .AddAspNetCoreInstrumentation(instrumentation =>
                        {
                            // Skip health check endpoints from traces
                            instrumentation.Filter = ctx => 
                                !ctx.Request.Path.StartsWithSegments("/health") &&
                                !ctx.Request.Path.StartsWithSegments("/alive");
                        })
                        .AddHttpClientInstrumentation();
                });
            
            // Add Azure Monitor if connection string is configured
            if (hasAzureConfig)
            {
                appBuilder.Services.AddOpenTelemetry()
                    .UseAzureMonitor(options =>
                    {
                        options.ConnectionString = azureConnectionString;
                    });
                
                appBuilder.Logging.AddConsole();
                appBuilder.Logging.AddDebug();
                
                var logger = appBuilder.Services.BuildServiceProvider().GetRequiredService<ILogger<IHostApplicationBuilder>>();
                logger.LogInformation("✅ Transcription telemetry: Azure Monitor enabled");
            }
            else
            {
                // Use OTLP exporter if configured, otherwise local only
                var otlpEndpoint = appBuilder.Configuration["OTEL_EXPORTER_OTLP_ENDPOINT"];
                if (!string.IsNullOrWhiteSpace(otlpEndpoint))
                {
                    appBuilder.Services.AddOpenTelemetry().UseOtlpExporter();
                }
                
                var logger = appBuilder.Services.BuildServiceProvider().GetRequiredService<ILogger<IHostApplicationBuilder>>();
                logger.LogInformation("🔧 Transcription telemetry: Running in local mode");
            }
            
            return appBuilder;
        }
    }
}
