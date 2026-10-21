"""
PIE Tools for Unreal MCP.

Drive a running Play-In-Editor session the way a player would and observe the result: start/stop PIE, run
console commands in the PIE world, inject Enhanced Input on a frame-exact timeline, snapshot input/camera
state, read back the log written since a marker, and take screenshots.

Each tool is a thin wrapper over the in-editor module `pie_driver` (UnrealMCP plugin, Content/Python), called
through run_python. For anything these don't cover, use run_python with `import pie_driver` directly.
pie_show_viewport and pie_capture_viewport are native bridge commands instead (they need Slate's tab
manager and screenshot API), so they also work where pie_driver is not installed.
Guide: Docs/Agents/PIEDriver.md in the game repo.
"""

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

from mcp.server.fastmcp import FastMCP, Context

from tools.flow_tools import _node_summary, _obj_path

logger = logging.getLogger("UnrealMCP")

RESULT_PREFIX = "PIE_DRIVER_RESULT "

Send = Callable[[str, Dict[str, Any]], Optional[Dict[str, Any]]]


def _connection_send() -> Optional[Send]:
    from unreal_mcp_server import get_unreal_connection

    unreal = get_unreal_connection()
    return unreal.send_command if unreal else None


def _call(expression: str, setup: str = "", send: Optional[Send] = None) -> Dict[str, Any]:
    """Evaluate `expression` in the editor with pie_driver imported as `d`, returning its JSON-able value."""
    code = "import pie_driver as d\n" + setup + "\nd.emit(" + expression + ")\n"
    try:
        send = send or _connection_send()
        response = send("run_python", {"code": code}) if send else None
    except Exception as e:
        return {"success": False, "message": f"pie_driver call failed: {e}"}
    if not response:
        return {"success": False, "message": "No response from Unreal Engine"}

    result = response.get("result", response)
    output = result.get("output", [])
    for line in output:
        text = line.strip()
        if text.startswith(RESULT_PREFIX):
            return {"success": True, "result": json.loads(text[len(RESULT_PREFIX):])}
    return {"success": False, "message": result.get("error") or "pie_driver returned nothing",
            "output": output}


def _send(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Send a native bridge command (one handled in C++ rather than by pie_driver)."""
    from unreal_mcp_server import get_unreal_connection

    try:
        unreal = get_unreal_connection()
        response = unreal.send_command(command, params) if unreal else None
    except Exception as e:
        return {"success": False, "message": f"{command} failed: {e}"}
    return response or {"success": False, "message": "No response from Unreal Engine"}


class _FlowGraph:
    """A flow asset's nodes, each read over the bridge only when needed. dump_flow_asset reads them all,
    which takes seconds per narrative graph; the node map already names each node's class, so this skips
    the rest."""

    _NODE_CLASS = re.compile(r"^'?/Script/[^.]+\.([^']+)'")

    def __init__(self, send: Send, asset_path: str):
        if "." not in asset_path.rsplit("/", 1)[-1]:
            asset_path = "%s.%s" % (asset_path, asset_path.rsplit("/", 1)[-1])
        params = {"asset_path": asset_path, "property_filter": ["Nodes"]}
        response = send("get_asset_properties", params) or {}
        response = response.get("result", response)
        node_map = (response.get("properties") or {}).get("Nodes")
        if not isinstance(node_map, dict) or "entries" not in node_map:
            raise RuntimeError(f"could not read {asset_path}: {response}")
        self.path = asset_path
        self._send = send
        self._refs = {e["key"]: e["value"] for e in node_map["entries"]}
        self._read: Dict[str, Dict[str, Any]] = {}

    def node(self, guid: str) -> Dict[str, Any]:
        if guid not in self._read:
            response = self._send("get_asset_properties", {"asset_path": _obj_path(self._refs[guid])}) or {}
            self._read[guid] = _node_summary(response.get("result", response))
        return self._read[guid]

    def of_class(self, node_class: str) -> List[Dict[str, Any]]:
        return [self.node(guid) for guid, ref in self._refs.items()
                if (m := self._NODE_CLASS.match(ref)) and m.group(1) == node_class]

    def only(self, node_class: str) -> Dict[str, Any]:
        found = self.of_class(node_class)
        if len(found) != 1:
            raise RuntimeError(f"expected one {node_class} in {self.path}, found {len(found)}")
        return found[0]

    def connected(self, node: Dict[str, Any], pin: str) -> Dict[str, Any]:
        link = (node.get("connections") or {}).get(pin)
        link = link[0] if isinstance(link, list) else link
        if not link or link["node"] not in self._refs:
            raise RuntimeError(f"{node['name']} in {self.path} has nothing connected to {pin}")
        return self.node(link["node"])


def scene_entry_sequences(send: Send, root_flow: str, act: int, scene: int) -> List[str]:
    """The level sequences a scene's first moment (its door entry) plays, read from the narrative flow
    graph: the root flow's Act Sequence leads to a Scene Sequence, whose pin for the scene leads to the
    scene's subgraph, whose Moment Sequence's first pin leads to the first moment's subgraph."""
    root = _FlowGraph(send, root_flow)
    scenes = root.connected(root.only("FlowNode_ActSequence"), f"Act_{act + 1}")
    scene_graph = _FlowGraph(send, root.connected(scenes, f"Sequence_{scene + 1}")["settings"]["Asset"])
    first_moment = scene_graph.connected(scene_graph.only("FlowNode_MomentSequence"), "Sequence_1")
    moment_graph = _FlowGraph(send, first_moment["settings"]["Asset"])
    return [n["settings"]["Sequence"] for n in moment_graph.of_class("FlowNode_PlayHALLevelSequence")
            if n["settings"].get("Sequence") not in (None, "None")]


def start_pie(send: Send, params: Dict[str, Any], act: Optional[int] = None, scene: Optional[int] = None,
              moment: Optional[int] = None) -> Dict[str, Any]:
    """pie_start's body, taking the bridge's send function (so it can also be driven from a script)."""
    narrative = [act, scene, moment]
    if any(v is not None for v in narrative) and any(v is None for v in narrative):
        return {"success": False, "message": "act, scene and moment go together"}

    locator = None
    if act is not None:
        try:
            # A first moment is the door entry, which puts the player in the room itself
            if moment > 0:
                root = _call("d.root_flow()", send=send)
                if not root.get("success") or not root["result"]:
                    raise RuntimeError("the level has no root narrative flow")
                sequences = scene_entry_sequences(send, root["result"], act, scene)
                found = _call(f"d.entry_locator({sequences!r})", send=send)
                if not found.get("success"):
                    raise RuntimeError(found.get("message"))
                locator = found["result"]
                if locator:
                    params = dict(params, location=locator["location"],
                                  rotation=[locator["rotation"]["pitch"], locator["rotation"]["yaw"], 0.0])
        except Exception as e:
            return {"success": False, "message": f"finding the scene's door-entry locator failed: {e}"}
        overridden = _call(f"d.override_narrative({act}, {scene}, {moment})", send=send)
        if not overridden.get("success"):
            return overridden

    response = send("start_pie", params) or {"success": False, "message": "No response from Unreal Engine"}
    if act is not None:
        if response.get("status") == "error" or response.get("success") is False:
            _call("d.restore_narrative()", send=send)
        else:
            response["narrative"] = narrative
            response["entry_locator"] = locator["name"] if locator else None
    return response


def register_pie_tools(mcp: FastMCP):
    """Register PIE tools with the MCP server."""

    @mcp.tool()
    def pie_start(ctx: Context, act: Optional[int] = None, scene: Optional[int] = None,
                  moment: Optional[int] = None, new_window: bool = False, width: int = 1920,
                  height: int = 1080, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """
        Start Play-In-Editor. Returns immediately; poll pie_state until it reports pie=True.

        act, scene, moment (0-based, all three or none) start the session at that narrative point. Without
        them it follows the user's PIE override (Project Settings > Hallucination Editor). The override is
        set in memory only and put back once the session has read it. A scene's first moment (moment=0) is
        its door entry cinematic; for any later moment the player spawns at the scene's door-entry locator,
        where that cinematic would have left them, so there is no cinematic to wait through. The result
        names the locator (null when the scene has no door entry, e.g. the first scene: the level's player
        start is used). pie_state's `narrative` confirms where the session started.

        new_window=True opens PIE in its own window at exactly width x height (the docked viewport's size depends
        on the editor layout), which render measurements (DumpGPU, ProfileGPU) need to be comparable. The window
        is centred on the primary display and limited to it, unless x, y place it elsewhere: use the agent
        virtual display (C:/repos/MattUtilScripts/AgentDisplay.ps1 -Start; -Status prints its desktop rect).
        """
        send = _connection_send()
        if not send:
            return {"success": False, "message": "No response from Unreal Engine"}
        params = {"new_window": new_window, "width": width, "height": height}
        if x is not None and y is not None:
            params.update(x=x, y=y)
        return start_pie(send, params, act, scene, moment)

    @mcp.tool()
    def pie_stop(ctx: Context) -> Dict[str, Any]:
        """Stop Play-In-Editor, releasing any injected input first."""
        return _call("True", setup="d.stop()")

    @mcp.tool()
    def pie_state(ctx: Context) -> Dict[str, Any]:
        """
        Snapshot what gates player look and move: interaction mode, Manipulating (blocks all look input while
        set), cinematic, input locks, fixed camera, ignore-look/move, view target, control rotation, camera and
        rig location. Returns pie=False when PIE isn't running.
        """
        return _call("d.state()")

    @mcp.tool()
    def pie_console(ctx: Context, command: str) -> Dict[str, Any]:
        """
        Run a console command in the PIE world: cvars (hal.DebugInteraction 1, hal.DebugLevelSequences 1),
        cheat-manager commands (HAL_SetNarrative, HAL_GetNarrative). execute_console_command targets the editor
        world instead. Output goes to the log; read it with pie_mark before and pie_log after.
        """
        return _call("True", setup=f"d.console({command!r})")

    @mcp.tool()
    def pie_input(ctx: Context, steps: List[List[Any]]) -> Dict[str, Any]:
        """
        Schedule Enhanced Input on exact frames, counted from the next tick. Replaces any pending timeline
        (actions already held stay held). Each step is [frame, kind, arg, value]:
          [0, "hold", "IA_Interact", true]          inject every frame until released
          [2, "hold", "IA_Puzzle_Drag", [0, -0.05]] Axis2D value per frame
          [22, "release", "IA_Puzzle_Drag"]
          [30, "tap", "IA_Back", true]               one frame
          [40, "snapshot", "after-release"]          record pie_state on that frame (also logged)
        Actions are bare names under /Game/Input or full asset paths. Mapping-level modifiers and chords
        (IMC sensitivity, the InteractDriven chord on puzzle drags) do NOT apply to injected input: pre-scale
        values and hold IA_Interact around drags yourself. Poll pie_input_status for completion.
        """
        return _call("True", setup=f"import json\nd.run_input(json.loads({json.dumps(steps)!r}))")

    @mcp.tool()
    def pie_input_status(ctx: Context) -> Dict[str, Any]:
        """Pending step count, currently held actions, and the executed steps (with any snapshots/errors)."""
        return _call("d.input_status()")

    @mcp.tool()
    def pie_stop_input(ctx: Context) -> Dict[str, Any]:
        """Cancel the pending input timeline and release every held action."""
        return _call("True", setup="d.stop_input()")

    @mcp.tool()
    def pie_mark(ctx: Context, tag: str) -> Dict[str, Any]:
        """Write a unique marker into the editor log and return it, to pass to pie_log later."""
        return _call(f"d.mark({tag!r})")

    @mcp.tool()
    def pie_log(ctx: Context, marker: str, contains: Optional[List[str]] = None,
                exclude: Optional[List[str]] = None, limit: int = 300) -> Dict[str, Any]:
        """
        Log lines written since a pie_mark marker. Keep only lines containing any of `contains` (e.g.
        ["[Interaction]", "[Behavior]"]) and drop lines containing any of `exclude` (e.g. per-frame
        "[Seq] PauseSequence" scrub noise). Returns the last `limit` lines.
        """
        return _call(f"d.log_since({marker!r}, {contains!r}, {exclude!r}, {int(limit)})")

    @mcp.tool()
    def pie_screenshot(ctx: Context, name: str) -> Dict[str, Any]:
        """
        Request a 1280x720 screenshot of the PIE viewport and return its file path. The file appears on a
        later frame (the first in a session can take about a minute); wait for it to exist, then Read it.
        Renders the scene only: game UI (UMG) is not in it - use pie_capture_viewport for that.
        """
        return _call(f"d.screenshot({name!r})")

    @mcp.tool()
    def pie_show_viewport(ctx: Context) -> Dict[str, Any]:
        """
        Bring the editor tab holding the PIE viewport to the front. While docked PIE sits behind another
        tab (say a Blueprint editor), Slate neither lays out nor draws its UI: widget geometry and desired
        sizes read as zero, and nothing on it can be captured. Values are readable from the next frame on
        (the next tool call). Returns switched: whether a tab had to move. The tab is not switched back.
        """
        return _send("show_pie_viewport", {})

    @mcp.tool()
    def pie_capture_viewport(ctx: Context, name: str) -> Dict[str, Any]:
        """
        Screenshot the PIE viewport as Slate draws it on screen - game UI included, at the viewport's
        on-screen size - to Saved/Screenshots/MCP/<name>.png. If the viewport is behind another tab, it is
        brought to the front first and left there.

        Returns at once with `path`; the file is written a few frames later. Wait for `path` to exist,
        then Read it. On failure `error_path` (a .error.txt) is written instead, within about 5 seconds.
        """
        return _send("capture_pie_viewport", {"name": name})

    @mcp.tool()
    def pie_actor_info(ctx: Context, actor: str) -> Dict[str, Any]:
        """
        For the one PIE actor whose label or name contains `actor`: its location, its interaction targets
        (active / targeted / depth) and its interaction behaviors (progress / input active).
        """
        return _call(f"{{'location': d.location_of({actor!r}), 'targets': d.targets({actor!r}), "
                     f"'behaviors': d.behaviors({actor!r})}}")

    @mcp.tool()
    def pie_get_properties(ctx: Context, actor: str, component: str = "",
                           properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Read properties (snake_case Python names, e.g. "max_interaction_progress") from a PIE actor, or from
        one of its components when `component` is given. Unlike get_actor_properties this reads the live PIE
        instance, not the editor-world one.
        """
        return _call(f"d.props({actor!r}, {component!r}, {list(properties or [])!r})")

    logger.info("PIE tools registered successfully")
