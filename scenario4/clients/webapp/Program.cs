using TranscriptionWebApp2.Components;
using TranscriptionWebApp2.Services;

var builder = WebApplication.CreateBuilder(args);

// Add Aspire service defaults (OpenTelemetry, health checks, service discovery)
builder.AddServiceDefaults();

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

// HttpClient for the ASR transcription API (service discovery via Aspire)
builder.Services.AddHttpClient("api", (_, httpClient) =>
{
    httpClient.BaseAddress = new Uri("http://apiserver");
});

// HttpClient for the NVIDIA NIM LLM container (podcast asset generation)
// Endpoint is injected by AppHost via service discovery env var
builder.Services.AddHttpClient("nim", (sp, httpClient) =>
{
    var nimEndpoint = builder.Configuration["services__nim-llm__http__0"]
                     ?? "http://localhost:8001";
    httpClient.BaseAddress = new Uri(nimEndpoint);
});

// Application services
builder.Services.AddScoped<TranscriptionApiService>();
builder.Services.AddScoped<NimPodcastService>();

var app = builder.Build();

// Map Aspire default endpoints (health checks)
app.MapDefaultEndpoints();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseAntiforgery();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
