"""
Level Structure Tools for Unreal MCP.

Create and open maps, stream sublevels, and author actors in a chosen sublevel with a label, outliner
folder, attach parent and FlowComponent identity tags. Also gameplay tag authoring, since new level
hierarchies need new tags.

Actors are addressed by label (as the outliner shows it) or object name. Labels repeat across sublevels,
so actor tools take an optional `level` (package path or bare map name) to pick one; an ambiguous
lookup is refused, not guessed. Opening a map is refused while any map has unsaved changes.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context, FastMCP

logger = logging.getLogger("UnrealMCP")


def _send(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    from unreal_mcp_server import get_unreal_connection

    try:
        unreal = get_unreal_connection()
        if not unreal:
            return {"success": False, "message": "Failed to connect to Unreal Engine"}
        response = unreal.send_command(command, params)
        if not response:
            return {"success": False, "message": "No response from Unreal Engine"}
        return response
    except Exception as e:
        logger.error("Error in %s: %s", command, e)
        return {"success": False, "message": "Error in %s: %s" % (command, e)}


def _without_none(params: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


def register_level_tools(mcp: FastMCP):
    """Register level structure, actor authoring and gameplay tag tools with the MCP server."""

    @mcp.tool()
    def get_level_info(ctx: Context) -> Dict[str, Any]:
        """
        Describe the open editor world: persistent level, current level, streaming sublevels (package,
        streaming class, loaded), maps with unsaved changes, and whether Play-In-Editor is running.
        """
        return _send("get_level_info", {})

    @mcp.tool()
    def create_level(ctx: Context, level_path: str) -> Dict[str, Any]:
        """
        Create and save an empty map without opening it. Fails if the asset exists.

        Args:
            level_path: e.g. "/Game/Hallucination/Campaign/Act2/Act2_Scene1/LVL_Act2_S1_Gameplay".
        """
        return _send("create_level", {"level_path": level_path})

    @mcp.tool()
    def open_level(ctx: Context, level_path: str) -> Dict[str, Any]:
        """
        Open a map in the editor, replacing the current one. Refused while any map has unsaved
        changes, so work is never discarded; save with save_levels (or ask the user) first.
        """
        return _send("open_level", {"level_path": level_path})

    @mcp.tool()
    def add_streaming_level(ctx: Context, level_path: str,
                            streaming_class: str = "AlwaysLoaded") -> Dict[str, Any]:
        """
        Add an existing map to the open world as a sublevel. The current level is left unchanged.

        Args:
            level_path: The sublevel's package path.
            streaming_class: "AlwaysLoaded" (the narrative acts' convention) or "Dynamic".
        """
        return _send("add_streaming_level", {"level_path": level_path,
                                             "streaming_class": streaming_class})

    @mcp.tool()
    def set_current_level(ctx: Context, level: str) -> Dict[str, Any]:
        """Make a loaded level current (where placed actors go). Package path or bare map name."""
        return _send("set_current_level", {"level": level})

    @mcp.tool()
    def save_levels(ctx: Context) -> Dict[str, Any]:
        """Save every level of the open world that has unsaved changes. Returns the saved packages."""
        return _send("save_levels", {})

    @mcp.tool()
    def list_level_actors(ctx: Context, level: str = "", class_filter: str = "", label_filter: str = "",
                          flow_only: bool = False, format: str = "tree", include_transform: bool = False,
                          max_actors: int = 500) -> Dict[str, Any]:
        """
        List actors per loaded level, with outliner labels, attach hierarchy, folders and FlowComponent
        identity tags. Much richer than get_actors_in_level.

        Args:
            level: Only levels whose package path or map name matches (substring).
            class_filter / label_filter: Substrings of the class name / label.
            flow_only: Only actors with a FlowComponent.
            format: "tree" (compact indented text per level: `Label [Class] flow{tags}`, roots show their
                folder) or "list" (one object per actor: label, name, class, level, folder, parent,
                flow_tags, root_flow).
            include_transform: Add location to "list" entries.
            max_actors: Stop after this many; "truncated" says whether it did.
        """
        return _send("list_level_actors", {
            "level": level, "class_filter": class_filter, "label_filter": label_filter,
            "flow_only": flow_only, "format": format, "include_transform": include_transform,
            "max_actors": max_actors})

    @mcp.tool()
    def spawn_level_actor(ctx: Context, label: str, level: str = "", actor_class: str = "Actor",
                          folder: Optional[str] = None, parent: Optional[str] = None,
                          parent_level: Optional[str] = None, location: Optional[List[float]] = None,
                          rotation: Optional[List[float]] = None, scale: Optional[List[float]] = None,
                          flow_identity_tags: Optional[List[str]] = None, root_flow: Optional[str] = None,
                          properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Spawn an actor into a chosen loaded level. Labels must be unique within the level.

        Args:
            label: Outliner label.
            level: Target level (package path or map name); defaults to the current level.
            actor_class: "Actor" (an empty group actor with a scene root, like Place Actors > Empty
                Actor), a native class name ("PlayerCameraTriggerBox"), or a full path
                ("/Game/.../BP_Act2_AudioController").
            folder: Outliner folder, e.g. "Act2_Scene1".
            parent: Label of the actor to attach to (keeping world transform). Looked up in the same
                level unless parent_level is given.
            location / rotation / scale: World transform, [x, y, z] / [pitch, yaw, roll] / [x, y, z].
            flow_identity_tags: Identity tags for the actor's FlowComponent; one is added as an instance
                component if the class has none. Tags must already exist (add_gameplay_tags).
            root_flow: Flow asset for the FlowComponent's RootFlow.
            properties: Actor properties, as for add_flow_node (text import, applied in order).

        Returns:
            The actor: label, name, class, level, folder, parent, flow_tags, location.
        """
        return _send("spawn_level_actor", _without_none({
            "label": label, "level": level, "class": actor_class, "folder": folder, "parent": parent,
            "parent_level": parent_level, "location": location, "rotation": rotation, "scale": scale,
            "flow_identity_tags": flow_identity_tags, "root_flow": root_flow, "properties": properties}))

    @mcp.tool()
    def set_level_actor(ctx: Context, actor: str, level: str = "", label: Optional[str] = None,
                        folder: Optional[str] = None, parent: Optional[str] = None,
                        parent_level: Optional[str] = None, location: Optional[List[float]] = None,
                        rotation: Optional[List[float]] = None, scale: Optional[List[float]] = None,
                        flow_identity_tags: Optional[List[str]] = None, root_flow: Optional[str] = None,
                        properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Edit an existing actor. Only the fields given change.

        Args:
            actor: Label or object name. "WorldSettings" is the given level's (default: persistent
                level's) world settings, whose FlowComponent holds the map's RootFlow.
            level: Level to look in, to disambiguate labels that repeat across sublevels.
            parent: Label to attach to; "" detaches.
            folder: Outliner folder; "" moves it to the root.
            flow_identity_tags: Replaces the FlowComponent's identity tags (adds a FlowComponent if
                missing).
            root_flow: Flow asset path for RootFlow; "" clears it.
            Other fields as for spawn_level_actor.
        """
        return _send("set_level_actor", _without_none({
            "actor": actor, "level": level, "label": label, "folder": folder, "parent": parent,
            "parent_level": parent_level, "location": location, "rotation": rotation, "scale": scale,
            "flow_identity_tags": flow_identity_tags, "root_flow": root_flow, "properties": properties}))

    @mcp.tool()
    def delete_level_actor(ctx: Context, actor: str, level: str = "") -> Dict[str, Any]:
        """Delete an actor by label or name (attached children are detached, not deleted)."""
        return _send("delete_level_actor", {"actor": actor, "level": level})

    @mcp.tool()
    def add_gameplay_tags(ctx: Context, tags: List[str], comment: str = "") -> Dict[str, Any]:
        """
        Add gameplay tags to Config/DefaultGameplayTags.ini, usable immediately without a restart.
        Tags that already exist are reported, not re-added.
        """
        return _send("add_gameplay_tags", {"tags": tags, "comment": comment})

    @mcp.tool()
    def remove_gameplay_tag(ctx: Context, tag: str) -> Dict[str, Any]:
        """
        Remove a gameplay tag from its ini. Refused if any asset still references it, or if it only
        exists implicitly as the parent of other tags. Explicit child tags are left in place.
        """
        return _send("remove_gameplay_tag", {"tag": tag})

    @mcp.tool()
    def list_gameplay_tags(ctx: Context, prefix: str = "") -> Dict[str, Any]:
        """List registered gameplay tags, optionally only those starting with a prefix ("Act2.")."""
        return _send("list_gameplay_tags", {"prefix": prefix})
