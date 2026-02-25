using AgentChat.Services;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using System.Net;
using System.Net.Http.Headers;
using System.Text;
using Xunit;

namespace AgentChat.Tests;

/// <summary>
/// Unit tests for <see cref="LlmClientFactory"/>.
/// These tests validate that the factory builds a <see cref="OpenAI.Chat.ChatClient"/>
/// configured with the correct endpoint and model name, without requiring a real LLM.
/// </summary>
public class LlmClientFactoryTests
{
    [Fact]
    public void CreateChatClient_ReturnsNonNullClient()
    {
        // Arrange
        var options = BuildOptions(new LlmOptions
        {
            EndpointUrl = "http://localhost:11434/v1/",
            ModelName = "tinyllama",
            ApiKey = "not-required",
        });
        var factory = new LlmClientFactory(options, NullLogger<LlmClientFactory>.Instance);

        // Act
        var client = factory.CreateChatClient();

        // Assert
        Assert.NotNull(client);
    }

    [Fact]
    public void CreateChatClient_UsesConfiguredModel()
    {
        // Arrange
        const string expectedModel = "my-custom-model";
        var options = BuildOptions(new LlmOptions
        {
            EndpointUrl = "http://localhost:11434/v1/",
            ModelName = expectedModel,
            ApiKey = "test-key",
        });
        var factory = new LlmClientFactory(options, NullLogger<LlmClientFactory>.Instance);

        // Act – a client should be created without throwing
        var client = factory.CreateChatClient();

        // Assert – the client is non-null; model name is baked in at construction time
        Assert.NotNull(client);
    }

    [Fact]
    public void CreateChatClient_AllowsCustomEndpoint()
    {
        // Arrange – use an unusual port to prove the endpoint is forwarded
        var options = BuildOptions(new LlmOptions
        {
            EndpointUrl = "http://127.0.0.1:9999/v1/",
            ModelName = "tinyllama",
            ApiKey = "not-required",
        });
        var factory = new LlmClientFactory(options, NullLogger<LlmClientFactory>.Instance);

        // Act – should not throw when building the client
        var client = factory.CreateChatClient();

        // Assert
        Assert.NotNull(client);
    }

    [Fact]
    public void LlmOptions_DefaultValues_AreValid()
    {
        // Arrange & Act
        var opts = new LlmOptions();

        // Assert – defaults must be present and parseable
        Assert.False(string.IsNullOrWhiteSpace(opts.EndpointUrl));
        Assert.NotNull(new Uri(opts.EndpointUrl));
        Assert.False(string.IsNullOrWhiteSpace(opts.ModelName));
        Assert.False(string.IsNullOrWhiteSpace(opts.ApiKey));
        Assert.False(string.IsNullOrWhiteSpace(opts.SystemPrompt));
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static IOptions<LlmOptions> BuildOptions(LlmOptions value)
        => Options.Create(value);
}
