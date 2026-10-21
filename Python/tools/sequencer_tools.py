"""
Sequencer Tools for Unreal MCP.

This module provides tools for inspecting Level Sequences and copying tracks between them, plus a
generic asset save for edits that only mark a package dirty.
"""

import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP, Context

# Get logger
logger = logging.getLogger("UnrealMCP")


def _send(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    from unreal_mcp_server import get_unreal_connection

    try:
        unreal = get_unreal_connection()
        if not unreal:
            logger.error("Failed to connect to Unreal Engine")
            return {"success": False, "message": "Failed to connect to Unreal Engine"}

        response = unreal.send_command(command, params)
        if not response:
            logger.error("No response from Unreal Engine")
            return {"success": False, "message": "No response from Unreal Engine"}

        return response

    except Exception as e:
        error_msg = f"Error in {command}: {e}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}


def register_sequencer_tools(mcp: FastMCP):
    """Register sequencer tools with the MCP server."""

    @mcp.tool()
    def get_level_sequence_tracks(ctx: Context, sequence: str) -> Dict[str, Any]:
        """
        List a Level Sequence's root tracks and bindings, with every track's sections.

        Args:
            sequence: Full path ("/Game/Dir/LS_Name") or bare asset name. A bare name that matches
                      several assets is refused, so use the full path when copies exist.

        Returns:
            Dict with display rate, tick resolution, playback range, root_tracks, and bindings. Each
            binding has a "path" ("Actor/Component" display names) and its tracks. Each track has its
            class, display name and sections; each section has row, start/end in display frames and
            seconds, and any assets it references (e.g. the FMOD event it plays).
        """
        return _send("get_level_sequence_tracks", {"sequence": sequence})

    @mcp.tool()
    def copy_level_sequence_tracks(
        ctx: Context,
        source_sequence: str,
        target_sequence: str,
        track_class: str = "",
        track_name: str = "",
        binding: str = "",
        include_root_tracks: bool = True,
        allow_duplicates: bool = False,
        replace_existing: bool = False,
        dry_run: bool = False,
        save: bool = False
    ) -> Dict[str, Any]:
        """
        Copy matching tracks, with their sections, from one Level Sequence into another.

        Binding tracks go onto the target binding with the same "Actor/Component" path, falling back
        to a unique match on the last name in the path. Sections keep their absolute frame times, so
        check them if the target's timing differs from the source's. Undoable in the editor.

        Args:
            source_sequence: Sequence to copy from (full path or unique bare name).
            target_sequence: Sequence to copy into.
            track_class: Substring of the track class name to match, e.g. "FMOD". At least one of
                         track_class or track_name is required.
            track_name: Exact track display name to match.
            binding: Only copy from the source binding with this path or last name.
            include_root_tracks: Also copy matching root (master) tracks. Ignored when binding is set.
            allow_duplicates: Copy even when the target already has a track of the same class and name.
            replace_existing: Remove the target's track of the same class and name and put the source's
                              in its place — "take theirs" for tracks both sides have. Exclusive with
                              allow_duplicates.
            dry_run: Report what would be copied without changing anything.
            save: Save the target sequence after copying.

        Returns:
            Dict with "copied" and "skipped" track lists; skipped entries carry the reason.
        """
        return _send("copy_level_sequence_tracks", {
            "source_sequence": source_sequence,
            "target_sequence": target_sequence,
            "track_class": track_class,
            "track_name": track_name,
            "binding": binding,
            "include_root_tracks": include_root_tracks,
            "allow_duplicates": allow_duplicates,
            "replace_existing": replace_existing,
            "dry_run": dry_run,
            "save": save,
        })

    @mcp.tool()
    def save_asset(ctx: Context, asset_path: str) -> Dict[str, Any]:
        """
        Save an asset's package, e.g. after set_blueprint_property or a track copy.

        Args:
            asset_path: Package or object path, e.g. "/Game/Dir/BP_Name".

        Returns:
            Dict with the saved package path.
        """
        return _send("save_asset", {"asset_path": asset_path})

    @mcp.tool()
    def set_string_table_entry(ctx: Context, asset_path: str, key: str, source_string: str,
                               save: bool = True) -> Dict[str, Any]:
        """
        Add a String Table entry, or overwrite an existing entry's source string (Python can't).

        Args:
            asset_path: String Table path, e.g. "/Game/Hallucination/StringTables/ST_PauseMenu"
            key: Entry key, e.g. "SettingsLabel_MuteMusic"
            source_string: The (native culture) source text
            save: Save the String Table package afterwards

        Returns:
            Dict with the table id, key, and previous_source_string when the key already existed.
        """
        return _send("set_string_table_entry", {"asset_path": asset_path, "key": key,
                                                "source_string": source_string, "save": save})

    @mcp.tool()
    def delete_asset(ctx: Context, asset_path: str, force: bool = False) -> Dict[str, Any]:
        """
        Delete an asset. Refused, with the referencing packages listed, while anything still references
        it, unless force is set. Referencers come from the asset registry, which reflects saved state:
        save assets that dropped their reference before deleting.

        Args:
            asset_path: Content path, e.g. "/Game/UI/WBP_Old"
            force: Delete even though other packages reference it (they will have broken references)
        """
        return _send("delete_asset", {"asset_path": asset_path, "force": force})

    @mcp.tool()
    def run_python(ctx: Context, code: str = "", file: str = "") -> Dict[str, Any]:
        """
        Run Python in the editor (the `unreal` module) and get back its result and log output - unlike
        execute_console_command("py ..."), which reports success even when the script raises. Use it for
        editor work no dedicated tool covers, such as importing textures or editing class defaults.
        Pass exactly one of code (a script, multiple statements fine) or file (a .py path). Each call
        runs in a fresh namespace: nothing defined in one call is visible to the next.
        """
        params = {"code": code} if code else {"file": file}
        return _send("run_python", params)

    logger.info("Sequencer tools registered successfully")
