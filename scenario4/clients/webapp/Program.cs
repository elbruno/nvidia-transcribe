using TranscriptionWebApp2.Components;
using TranscriptionWebApp2.Services;

var builder = WebApplication.CreateBuilder(args);

// Add Aspire service defaults (OpenTelemetry, health checks, service discovery)
builder.AddServiceDefaults();

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

// Add HttpClient for API communication with service discovery
builder.Services.AddHttpClient("api", (serviceProvider, client) =>
{
    // Use Aspire service discovery to resolve the API endpoint
    client.BaseAddress = new Uri("http://apiserver");
})
.AddStandardResilienceHandler();

// Register TranscriptionApiService
builder.Services.AddScoped<TranscriptionApiService>();

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
