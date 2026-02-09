using System.Text.Json;
using OpenAI.Chat;

namespace TranscriptionWebApp2.Services;

/// <summary>
/// Strongly-typed representation of the LLM-generated podcast metadata.
/// </summary>
public sealed record EpisodeMetadata
{
    public string Title { get; init; } = string.Empty;
    public string Description { get; init; } = string.Empty;
    public string[] Tags { get; init; } = [];
}

/// <summary>
/// Communicates with the NVIDIA NIM LLM container to produce
/// structured podcast episode metadata from raw transcription text.
/// The NIM container exposes an OpenAI-compatible chat completions API.
/// </summary>
public sealed class NimPodcastService
{
    private readonly IHttpClientFactory _clientFactory;
    private readonly ILogger<NimPodcastService> _log;

    private const string NimModelId = "nvidia/llama-3.2-nv-minitron-4b-instruct";

    private const string LlmRoleInstruction =
        "You are a podcast production assistant. "
        + "Given a transcript, generate a concise episode title, "
        + "an engaging episode description (2-3 sentences), "
        + "and 5-8 relevant tags.";

    private static readonly JsonSerializerOptions DeserializeOpts = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public NimPodcastService(IHttpClientFactory clientFactory, ILogger<NimPodcastService> log)
    {
        _clientFactory = clientFactory;
        _log = log;
    }

    /// <summary>
    /// Sends the transcript to the NIM container and returns parsed episode metadata.
    /// </summary>
    public async Task<EpisodeMetadata> CreateEpisodeMetadataAsync(
        string transcript,
        CancellationToken ct = default)
    {
        var nimHttp = _clientFactory.CreateClient("nim");

        var chatApi = new ChatClient(
            model: NimModelId,
            credential: new System.ClientModel.ApiKeyCredential("nim-local"),
            options: new OpenAI.OpenAIClientOptions { Endpoint = nimHttp.BaseAddress });

        _log.LogInformation("Requesting episode metadata from NIM – transcript length: {Len} chars", transcript.Length);

        var userPrompt =
            "Here is the transcript:\n\n" + transcript + "\n\n"
            + "Generate the following in JSON format:\n"
            + "- title\n- description\n- tags (array of strings)";

        ChatMessage[] conversation =
        [
            new SystemChatMessage(LlmRoleInstruction),
            new UserChatMessage(userPrompt)
        ];

        var completionOpts = new ChatCompletionOptions
        {
            ResponseFormat = ChatResponseFormat.CreateJsonObjectFormat()
        };

        var reply = await chatApi.CompleteChatAsync(conversation, completionOpts, ct);

        var rawJson = reply.Value.Content[0].Text;
        _log.LogInformation("NIM replied with {Len} chars of JSON", rawJson.Length);

        var metadata = JsonSerializer.Deserialize<EpisodeMetadata>(rawJson, DeserializeOpts);
        return metadata
            ?? throw new InvalidOperationException("NIM returned JSON that could not be mapped to EpisodeMetadata.");
    }
}
