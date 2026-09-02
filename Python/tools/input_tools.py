"""
Input & Asset Inspection Tools for Unreal MCP.

Provides runtime inspection of Enhanced Input state
(active mapping contexts, IMC mappings, bound actions)
and a generic UAsset property inspector.
"""

import logging
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP, Context

logger = logging.getLogger("UnrealMCP")


def register_input_tools(mcp: FastMCP):
    """Register input and asset inspection tools."""

    @mcp.tool()
    def get_active_input_contexts(
        ctx: Context,
    ) -> Dict[str, Any]:
        """
        Get all active input mapping contexts and their
        priorities. Requires PIE to be running.

        Returns:
            Dict containing 'contexts' array with name, path,
            priority, and mapping_count for each active IMC.
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {
                    "success": False,
                    "message": "Failed to connect to Unreal Engine",
                }

            response = unreal.send_command(
                "get_active_input_contexts", {}
            )
            if not response:
                return {
                    "success": False,
                    "message": "No response from Unreal Engine",
                }

            if "result" in response:
                return response["result"]
            return response

        except Exception as e:
            error_msg = f"Error getting active input contexts: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_imc_mappings(
        ctx: Context,
        asset_path: str,
    ) -> Dict[str, Any]:
        """
        Inspect an Input Mapping Context asset's action-to-key
        bindings.

        Args:
            asset_path: Full content path to the IMC asset
                (e.g. "/Game/Input/IMC_PuzzleDefault")

        Returns:
            Dict with 'name', 'path', 'mapping_count', and
            'mappings' array. Each mapping has action, key,
            triggers, and modifiers.
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {
                    "success": False,
                    "message": "Failed to connect to Unreal Engine",
                }

            response = unreal.send_command(
                "get_imc_mappings",
                {"asset_path": asset_path},
            )
            if not response:
                return {
                    "success": False,
                    "message": "No response from Unreal Engine",
                }

            if "result" in response:
                return response["result"]
            return response

        except Exception as e:
            error_msg = f"Error getting IMC mappings: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_input_action_bindings(
        ctx: Context,
    ) -> Dict[str, Any]:
        """
        Query what input actions are currently bound on the
        player's EnhancedInputComponent. Requires PIE.

        Returns:
            Dict with 'event_bindings' and 'value_bindings'
            arrays showing which actions are bound and their
            trigger events.
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {
                    "success": False,
                    "message": "Failed to connect to Unreal Engine",
                }

            response = unreal.send_command(
                "get_input_action_bindings", {}
            )
            if not response:
                return {
                    "success": False,
                    "message": "No response from Unreal Engine",
                }

            if "result" in response:
                return response["result"]
            return response

        except Exception as e:
            error_msg = (
                f"Error getting input action bindings: {e}"
            )
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_asset_properties(
        ctx: Context,
        asset_path: str,
        property_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Load any UAsset by path and serialize its UPROPERTY
        fields to JSON. Works on any asset type (IMC, DataAsset,
        Blueprint CDO, etc.).

        Args:
            asset_path: Full content path to the asset
                (e.g. "/Game/Input/IMC_PuzzleDefault")
            property_filter: Optional list of property names to
                include. If empty/None, returns all properties.

        Returns:
            Dict with 'name', 'path', 'class', and 'properties'
            containing the serialized UPROPERTY values. Arrays
            are capped at 50 elements. Object references show
            name, path, and class.
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {
                    "success": False,
                    "message": "Failed to connect to Unreal Engine",
                }

            params = {"asset_path": asset_path}
            if property_filter:
                params["property_filter"] = property_filter

            response = unreal.send_command(
                "get_asset_properties", params
            )
            if not response:
                return {
                    "success": False,
                    "message": "No response from Unreal Engine",
                }

            if "result" in response:
                return response["result"]
            return response

        except Exception as e:
            error_msg = f"Error getting asset properties: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_physics_asset_info(
        ctx: Context,
        asset_path: str,
    ) -> Dict[str, Any]:
        """
        Inspect a UPhysicsAsset to see its bodies (bones,
        physics type, geometry) and constraints (bone pairs,
        linear/angular limits).

        Args:
            asset_path: Full content path to the physics asset
                (e.g. "/Game/MyMesh_PhysicsAsset")

        Returns:
            Dict with body_count, constraint_count, bodies
            array, and constraints array.
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {
                    "success": False,
                    "message": "Failed to connect to Unreal Engine",
                }

            response = unreal.send_command(
                "get_physics_asset_info",
                {"asset_path": asset_path},
            )
            if not response:
                return {
                    "success": False,
                    "message": "No response from Unreal Engine",
                }

            if "result" in response:
                return response["result"]
            return response

        except Exception as e:
            error_msg = (
                f"Error getting physics asset info: {e}"
            )
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def copy_physics_bodies(
        ctx: Context,
        source_asset: str,
        target_asset: str,
        bone_names: List[str],
        clear_existing: bool = True,
    ) -> Dict[str, Any]:
        """
        Copy physics bodies and their constraints from one
        physics asset to another, filtered by bone name.

        Copies the full body setup (including convex hull
        geometry) for each matching bone, plus any constraints
        where both bones are in the list.

        Args:
            source_asset: Full content path to the source
                physics asset
            target_asset: Full content path to the target
                physics asset
            bone_names: List of bone names to copy
            clear_existing: If True (default), removes all
                existing bodies and constraints in the target
                before copying

        Returns:
            Dict with bodies_copied and constraints_copied
            counts.
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {
                    "success": False,
                    "message": (
                        "Failed to connect to Unreal Engine"
                    ),
                }

            response = unreal.send_command(
                "copy_physics_bodies",
                {
                    "source_asset": source_asset,
                    "target_asset": target_asset,
                    "bone_names": bone_names,
                    "clear_existing": clear_existing,
                },
            )
            if not response:
                return {
                    "success": False,
                    "message": (
                        "No response from Unreal Engine"
                    ),
                }

            if "result" in response:
                return response["result"]
            return response

        except Exception as e:
            error_msg = (
                f"Error copying physics bodies: {e}"
            )
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def remove_physics_body(
        ctx: Context,
        asset_path: str,
        bone_name: str,
    ) -> Dict[str, Any]:
        """
        Remove a physics body (and its constraints) from a
        physics asset by bone name.

        Args:
            asset_path: Full content path to the physics
                asset
            bone_name: Name of the bone whose body to remove

        Returns:
            Dict with bodies_removed and
            constraints_removed counts.
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {
                    "success": False,
                    "message": (
                        "Failed to connect to Unreal Engine"
                    ),
                }

            response = unreal.send_command(
                "remove_physics_body",
                {
                    "asset_path": asset_path,
                    "bone_name": bone_name,
                },
            )
            if not response:
                return {
                    "success": False,
                    "message": (
                        "No response from Unreal Engine"
                    ),
                }

            if "result" in response:
                return response["result"]
            return response

        except Exception as e:
            error_msg = (
                f"Error removing physics body: {e}"
            )
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    logger.info("Input & asset inspection tools registered")
