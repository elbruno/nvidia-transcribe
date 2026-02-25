namespace AgentChat.Services;

/// <summary>
/// Configuration options for the local LLM endpoint.
/// Values can be set via appsettings.json or environment variables
/// (prefix: Llm__).
/// </summary>
public sealed class LlmOptions
{
    public const string SectionName = "Llm";

    /// <summary>Base URL of the OpenAI-compatible LLM endpoint.</summary>
    /// <remarks>Override with the <c>LLM_ENDPOINT_URL</c> environment variable.</remarks>
    public string EndpointUrl { get; set; } = "http://localhost:11434/v1/";

    /// <summary>Model name to use for chat completions.</summary>
    /// <remarks>Override with the <c>MODEL_NAME</c> environment variable.</remarks>
    public string ModelName { get; set; } = "tinyllama";

    /// <summary>API key sent to the endpoint (most local servers ignore this).</summary>
    /// <remarks>Override with the <c>LLM_API_KEY</c> environment variable.</remarks>
    public string ApiKey { get; set; } = "not-required";

    /// <summary>System prompt injected as the agent's persona/instructions.</summary>
    public string SystemPrompt { get; set; } = "You are a helpful AI assistant. Be concise and friendly.";
}
