FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY AgentChat/AgentChat.csproj AgentChat/
RUN dotnet restore AgentChat/AgentChat.csproj

COPY AgentChat/ AgentChat/
RUN dotnet publish AgentChat/AgentChat.csproj -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/runtime:10.0
WORKDIR /app
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "AgentChat.dll"]
