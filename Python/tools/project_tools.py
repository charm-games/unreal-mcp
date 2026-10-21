"""
Project Tools for Unreal MCP.

This module provides tools for managing project-wide settings and configuration.
"""

import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP, Context

# Get logger
logger = logging.getLogger("UnrealMCP")

def register_project_tools(mcp: FastMCP):
    """Register project tools with the MCP server."""
    
    @mcp.tool()
    def create_input_mapping(
        ctx: Context,
        action_name: str,
        key: str,
        input_type: str = "Action"
    ) -> Dict[str, Any]:
        """
        Create an input mapping for the project.
        
        Args:
            action_name: Name of the input action
            key: Key to bind (SpaceBar, LeftMouseButton, etc.)
            input_type: Type of input mapping (Action or Axis)
            
        Returns:
            Response indicating success or failure
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            params = {
                "action_name": action_name,
                "key": key,
                "input_type": input_type
            }
            
            logger.info(f"Creating input mapping '{action_name}' with key '{key}'")
            response = unreal.send_command("create_input_mapping", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Input mapping creation response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error creating input mapping: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @mcp.tool()
    def set_project_settings(
        ctx: Context,
        settings_class: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Set values on a Project Settings / Editor Preferences page and save them, as editing them in
        those panels does: each property gets the edit notifications, then shared settings
        (DefaultConfig classes) are written to their Default*.ini and per-user ones to Saved/Config.

        Like Project Settings itself, the save rewrites the class's whole ini section: keys get
        reordered, keys for removed properties are dropped and defaults may be written out. For a
        clean diff, restore the file afterwards and add just the changed lines - the in-editor
        values are already set.

        Args:
            settings_class: The settings class: a native name ("HALSettings", "InputSettings") or a
                "/Script/Module.Class" path. Must be a config class.
            properties: Values to set, same format as add_widget / set_widget_properties: Unreal text
                strings, numbers or bools; dotted paths reach into structs. Arrays and structs take
                Unreal text, e.g. {"SandboxLevels": "((Level=\"/Game/Maps/L.L\",DisplayName=\"L\"))"}.
                An array value replaces the whole array.

        Returns:
            Dict with the resolved settings_class, the config_file written, and values: each set
            top-level property as Unreal text read back after saving.
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {"settings_class": settings_class, "properties": properties}
            response = unreal.send_command("set_project_settings", params)
            return response or {"success": False, "message": "No response from Unreal Engine"}

        except Exception as e:
            error_msg = f"Error setting project settings: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    logger.info("Project tools registered successfully")