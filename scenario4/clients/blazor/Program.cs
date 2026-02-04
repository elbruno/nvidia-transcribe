using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using TranscriptionWebApp;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

// Configure HttpClient for API calls
// Support both Aspire service discovery and standalone mode
var apiUrl = builder.Configuration["services__apiserver__http__0"]
    ?? builder.Configuration["ApiUrl"]
    ?? "http://localhost:8000";

builder.Services.AddScoped(sp => new HttpClient
{
    BaseAddress = new Uri(apiUrl)
});

await builder.Build().RunAsync();
