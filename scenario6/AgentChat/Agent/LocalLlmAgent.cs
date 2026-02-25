using AgentChat.Services;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.OpenAI;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using OpenAI.Chat;

namespace AgentChat.Agent;

/// <summary>
/// Wraps a Microsoft Agent Framework <see cref="AIAgent"/> backed by a local
/// OpenAI-compatible LLM endpoint.  Call <see cref="CreateSessionAsync"/> to get
/// an <see cref="AgentSession"/> that preserves conversation history across turns,
/// enabling multi-turn chat.
/// </summary>
public sealed class LocalLlmAgent
{
    private readonly AIAgent _agent;
    private readonly ILogger<LocalLlmAgent> _logger;

    public LocalLlmAgent(
        LlmClientFactory factory,
        IOptions<LlmOptions> options,
        ILogger<LocalLlmAgent> logger)
    {
        _logger = logger;
        var llmOptions = options.Value;

        // Build the OpenAI ChatClient and wrap it as an AIAgent using the
        // Microsoft.Agents.AI.OpenAI extension method .AsAIAgent().
        ChatClient chatClient = factory.CreateChatClient();
        _agent = chatClient.AsAIAgent(
            instructions: llmOptions.SystemPrompt,
            name: "LocalAssistant");

        _logger.LogInformation(
            "LocalLlmAgent created – model: {Model}, endpoint: {Endpoint}",
            llmOptions.ModelName,
            llmOptions.EndpointUrl);
    }

    /// <summary>
    /// Creates a new conversation session for multi-turn chat.
    /// Pass the returned <see cref="AgentSession"/> to every subsequent
    /// <see cref="ChatAsync"/> call to maintain context.
    /// </summary>
    public ValueTask<AgentSession> CreateSessionAsync(CancellationToken cancellationToken = default)
        => _agent.CreateSessionAsync(cancellationToken);

    /// <summary>
    /// Sends <paramref name="userMessage"/> to the agent and returns the reply.
    /// Pass the same <paramref name="session"/> across calls to preserve context.
    /// </summary>
    public async Task<string> ChatAsync(
        string userMessage,
        AgentSession session,
        CancellationToken cancellationToken = default)
    {
        _logger.LogDebug("User: {Message}", userMessage);

        var response = await _agent.RunAsync(userMessage, session, cancellationToken: cancellationToken);

        string reply = response.Text ?? string.Empty;
        _logger.LogDebug("Assistant: {Reply}", reply);
        return reply;
    }
}
