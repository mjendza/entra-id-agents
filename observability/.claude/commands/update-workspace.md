---
description: Discover Azure resource groups and Log Analytics workspaces via Azure-Mcp, then update workspaces.json.
argument-hint: <workspace key to update, e.g. "prod">
---

Update the `workspaces.json` file with real Azure subscription, resource group, and Log Analytics workspace ID values.

## Steps

1. **Read** `workspaces.json` to see existing workspace entries.

2. **List resource groups** using `mcp__Azure-Mcp__group_list` with the subscription ID from `.mcp.json` env `AZURE_SUBSCRIPTION_ID` (`7ff4a2b9-1e0f-4d66-99a3-59050b5558ff`).
   - Present the list to the user and ask which resource group to use.

3. **List Log Analytics workspaces** via the `mcp__Azure-Mcp__monitor` hierarchical router. There is no flat `log_analytics_workspaces_list` tool; the listing lives as a sub-command of `monitor`.
   - First call `mcp__Azure-Mcp__monitor` with `learn: true` and `intent: "Discover sub-command to list Log Analytics workspaces"` to find the exact sub-command and parameter names.
   - Then call it again with the discovered `command` and `parameters` (subscription + resource-group) to list workspaces in the chosen RG.
   - Present the list and ask which workspace to use. The needed value is the workspace's `customerId` (a GUID), not the Azure resource name.

4. **Update `workspaces.json`** — set the workspace key (use `$ARGUMENTS` if provided, otherwise `prod`) with:
   - `subscriptionId` — the subscription ID from `.mcp.json`
   - `resourceGroup` — the resource group selected in step 2
   - `workspaceId` — the Log Analytics workspace `customerId` (workspace ID / GUID) selected in step 3

5. **Show** the updated `workspaces.json` content to confirm.
