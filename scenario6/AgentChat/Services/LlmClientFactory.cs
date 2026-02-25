using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using OpenAI;
using OpenAI.Chat;
using System.ClientModel;

namespace AgentChat.Services;

/// <summary>
/// Creates an OpenAI <see cref="ChatClient"/> configured to talk to a local
/// OpenAI-compatible endpoint (e.g. Ollama).
/// </summary>
public sealed class LlmClientFactory
{
    private readonly LlmOptions _options;
    private readonly ILogger<LlmClientFactory> _logger;

    public LlmClientFactory(IOptions<LlmOptions> options, ILogger<LlmClientFactory> logger)
    {
        _options = options.Value;
        _logger = logger;
    }

    /// <summary>
    /// Builds a <see cref="ChatClient"/> pointing at the configured LLM endpoint.
    /// </summary>
    public ChatClient CreateChatClient()
    {
        var endpoint = new Uri(_options.EndpointUrl);
        var credential = new ApiKeyCredential(_options.ApiKey);
        var clientOptions = new OpenAIClientOptions { Endpoint = endpoint };

        _logger.LogDebug(
            "Creating ChatClient – endpoint: {Endpoint}, model: {Model}",
            _options.EndpointUrl,
            _options.ModelName);

        return new ChatClient(_options.ModelName, credential, clientOptions);
    }
}
