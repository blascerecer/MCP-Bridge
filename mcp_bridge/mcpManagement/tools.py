import json
import os
from typing import Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from mcp_bridge.mcp_clients.McpClientManager import ClientManager
from mcp.types import ListToolsResult, CallToolResult
from loguru import logger

router = APIRouter(prefix="/tools")


@router.get("")
async def get_tools() -> dict[str, ListToolsResult]:
    """Get all tools from all MCP clients"""

    tools = {}

    for name, client in ClientManager.get_clients():
        tools[name] = await client.list_tools()

    return tools


@router.post("/{tool_name}/call")
async def call_tool(tool_name: str, arguments: dict[str, Any] = {}) -> CallToolResult:
    """Call a tool"""

    client = await ClientManager.get_client_from_tool(tool_name)
    if not client:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return await client.call_tool(tool_name, arguments)


class UpdateMCPServersRequest(BaseModel):
    serversToAdd: List[str] = []
    serversToRemove: List[str] = []


@router.post("/servers/update", status_code=200)
async def update_mcp_servers(request: UpdateMCPServersRequest) -> dict:
    """Update MCP servers by adding and removing specified servers"""
    try:
        # Path to the config file
        config_path = 'mcp_config.json'
        # Path to the install.json file containing server configurations
        install_json_path = 'mcp_config/install.json'
        
        logger.info(f"Opening config file at: {config_path}")
        # Read the current configuration
        with open(config_path, 'r') as f:
            config_content = f.read()
            logger.debug(f"Config content: {config_content[:100]}...")  # Log first 100 chars
            config = json.loads(config_content)
        
        # Read the install.json file containing server configurations
        logger.info(f"Opening install.json file at: {install_json_path}")
        try:
            with open(install_json_path, 'r') as f:
                install_configs = json.loads(f.read())
        except FileNotFoundError:
            logger.error(f"install.json file not found: {install_json_path}")
            raise HTTPException(
                status_code=500, 
                detail=f"install.json file not found: {install_json_path}"
            )
        except json.JSONDecodeError:
            logger.error("Invalid JSON in install.json file")
            raise HTTPException(
                status_code=500, 
                detail="Invalid JSON in install.json file"
            )
        
        # Keep track of changes made
        changes = {
            "added": [],
            "removed": []
        }
        
        # Remove servers if they exist in the config
        for server_id in request.serversToRemove:
            if server_id in config["mcpServers"]:
                del config["mcpServers"][server_id]
                changes["removed"].append(server_id)
                logger.info(f"Removed server: {server_id}")
        
        # Add new servers using configuration from install.json
        for server_id in request.serversToAdd:
            if server_id not in config["mcpServers"]:
                # Check if the server configuration exists in install.json
                if server_id in install_configs:
                    # Use the configuration from install.json
                    config["mcpServers"][server_id] = install_configs[server_id]
                    changes["added"].append(server_id)
                    logger.info(f"Added server: {server_id} with configuration from install.json")
                else:
                    logger.warning(f"Server {server_id} not found in install.json, skipping...")
                    continue
        
        # Write the updated configuration back to the file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Reload the ClientManager to apply changes
        reload_success = await ClientManager.reload_config_and_clients()
        
        if not reload_success:
            # If reloading failed, we should still return success for the config file update
            # but indicate the reload failed
            return {
                "success": True,
                "reload_success": False,
                "message": "Configuration updated successfully but failed to reload clients",
                "changes": changes
            }
        
        logger.info('MCP server configuration updated and reloaded successfully')
        return {
            "success": True,
            "reload_success": True,
            "message": "MCP server configuration updated and reloaded successfully",
            "changes": changes
        }
        
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise HTTPException(
            status_code=500, 
            detail=f"Configuration file not found: {config_path}"
        )
    except json.JSONDecodeError:
        logger.error("Invalid JSON in configuration file")
        raise HTTPException(
            status_code=500, 
            detail="Invalid JSON in configuration file"
        )
    except Exception as e:
        logger.error(f"Error updating MCP server configuration: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error updating MCP server configuration: {str(e)}"
        )
