## About
The repository contains agents and tools for LLM to operate on Entra ID. 

## Agents
- `agent-entra-log-helper`: An agent that translates user questions about Entra ID logs into KQL queries, runs them against a Log Analytics workspace, and returns the results. It sources workspace details from `workspaces.json` and KQL templates from the `kb/` directory.

## How to use
### MCP 
Access to the Log Analytics workspace is done via Azure-Mcp, so you need to have it configured and running. You can use the provided `.mcp.ref.json` as a template, but make sure to fill in your own Azure credentials (client ID, tenant ID, client secret, subscription ID) before starting the MCP server.



## Thank you 
David Alonso for sharing a lot of knowlage about Entra ID Logs! in the repo: https://github.com/davidalonsod/Dalonso-Security-Repo