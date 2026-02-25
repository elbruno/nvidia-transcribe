using AgentChat.Agent;
using AgentChat.Services;
using Microsoft.Agents.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

// ── Build configuration ──────────────────────────────────────────────────────
IConfiguration configuration = new ConfigurationBuilder()
    .SetBasePath(AppContext.BaseDirectory)
    .AddJsonFile("appsettings.json", optional: true, reloadOnChange: false)
    .AddEnvironmentVariables()
    // Allow short-form overrides: LLM_ENDPOINT_URL, MODEL_NAME, LLM_API_KEY
    .AddInMemoryCollection(MapShortEnvVars())
    .Build();

// ── Dependency injection ─────────────────────────────────────────────────────
ServiceCollection services = new();

services.AddLogging(logging =>
{
    logging.AddConsole();
    logging.SetMinimumLevel(
        Enum.TryParse<LogLevel>(
            configuration["Logging:LogLevel:Default"], out var lvl)
            ? lvl
            : LogLevel.Warning);
});

services
    .Configure<LlmOptions>(configuration.GetSection(LlmOptions.SectionName))
    .AddSingleton<LlmClientFactory>()
    .AddSingleton<LocalLlmAgent>();

using ServiceProvider sp = services.BuildServiceProvider();

// ── Startup banner ───────────────────────────────────────────────────────────
var llmOpts = configuration.GetSection(LlmOptions.SectionName).Get<LlmOptions>()
    ?? new LlmOptions();

Console.ForegroundColor = ConsoleColor.Cyan;
Console.WriteLine("╔══════════════════════════════════════════════════════╗");
Console.WriteLine("║   Scenario 6 – Microsoft Agent Framework Chat        ║");
Console.WriteLine("╚══════════════════════════════════════════════════════╝");
Console.ResetColor();
Console.WriteLine($"  Endpoint : {llmOpts.EndpointUrl}");
Console.WriteLine($"  Model    : {llmOpts.ModelName}");
Console.WriteLine();
Console.WriteLine("Type your message and press Enter. Type 'exit' to quit.");
Console.WriteLine();

// ── Agent + thread ────────────────────────────────────────────────────────────
LocalLlmAgent agent = sp.GetRequiredService<LocalLlmAgent>();
AgentSession session = await agent.CreateSessionAsync();

using CancellationTokenSource cts = new();
Console.CancelKeyPress += (_, e) => { e.Cancel = true; cts.Cancel(); };

// ── Chat loop ─────────────────────────────────────────────────────────────────
while (!cts.Token.IsCancellationRequested)
{
    Console.ForegroundColor = ConsoleColor.Green;
    Console.Write("You: ");
    Console.ResetColor();

    string? input = Console.ReadLine();

    if (input is null || input.Trim().Equals("exit", StringComparison.OrdinalIgnoreCase))
        break;

    if (string.IsNullOrWhiteSpace(input))
        continue;

    try
    {
        Console.ForegroundColor = ConsoleColor.Yellow;
        Console.Write("Assistant: ");
        Console.ResetColor();

        string reply = await agent.ChatAsync(input, session, cts.Token);
        Console.WriteLine(reply);
        Console.WriteLine();
    }
    catch (OperationCanceledException)
    {
        break;
    }
    catch (Exception ex)
    {
        Console.ForegroundColor = ConsoleColor.Red;
        Console.WriteLine($"[Error] {ex.Message}");
        Console.ResetColor();
        Console.WriteLine("Make sure the LLM container is running. See README.md for setup.");
        Console.WriteLine();
    }
}

Console.WriteLine("Goodbye!");

// ── Helpers ───────────────────────────────────────────────────────────────────

/// <summary>
/// Reads short-form environment variables (LLM_ENDPOINT_URL, MODEL_NAME,
/// LLM_API_KEY) and maps them to the options-pattern keys expected by the
/// configuration system.
/// </summary>
static IEnumerable<KeyValuePair<string, string?>> MapShortEnvVars()
{
    var map = new Dictionary<string, string>
    {
        ["LLM_ENDPOINT_URL"] = $"{LlmOptions.SectionName}:EndpointUrl",
        ["MODEL_NAME"]       = $"{LlmOptions.SectionName}:ModelName",
        ["LLM_API_KEY"]      = $"{LlmOptions.SectionName}:ApiKey",
    };

    foreach (var (envKey, configKey) in map)
    {
        string? value = Environment.GetEnvironmentVariable(envKey);
        if (!string.IsNullOrEmpty(value))
            yield return new KeyValuePair<string, string?>(configKey, value);
    }
}
