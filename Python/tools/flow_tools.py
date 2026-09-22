"""
Flow Graph Tools for Unreal MCP.

Reads and edits FlowGraph assets (UFlowAsset / UHALFlowAsset).

Reading (get_flow_asset) is composed from the generic `get_asset_properties` command: every node with
its class, pins, connections and node-specific settings, plus the editor graph's comments. The
composition lives in a module-level function so it can also be driven from a script via
`dump_flow_asset(send, path)`.

Editing goes through the plugin's flow commands, which use the Flow editor's own graph actions, so
connections are harvested exactly as for a hand edit and every change is undoable in the editor.
Nodes are addressed by GUID, object name ("FlowNode_Start_0"), or "Start".
"""

import logging
import re
from typing import Any, Callable, Dict, List, Optional

from mcp.server.fastmcp import Context, FastMCP

logger = logging.getLogger("UnrealMCP")

# Properties every UFlowNode carries that say nothing about a specific graph. Dropped from the
# per-node "settings" so the interesting ones stand out.
_NODE_BOILERPLATE = {
    "AllowedAssetClasses", "DeniedAssetClasses", "AllowedSignalModes", "SignalMode", "NodeGuid",
    "InputPins", "OutputPins", "Connections", "PinNameToBoundPropertyNameMap", "AutoInputDataPins",
    "AutoOutputDataPins", "ActivationState", "AddOns", "GraphNode", "bDisplayNodeTitleWithoutPrefix",
    "bNodeDeprecated", "ReplacedBy", "Category", "NodeDisplayStyle", "NodeStyle", "NodeColor",
    "DevNodeConfigText", "AllowedAssignedAssetClasses", "DeniedAssignedAssetClasses",
    "SavedAssetInstanceName", "bCanInstanceIdenticalAsset",
}

_OBJ_REF = re.compile(r"'([^']+)'")
_PIN_NAME = re.compile(r'PinName="([^"]*)"')
_CONN = re.compile(r'NodeGuid=([0-9A-F]+),PinName="([^"]*)"')


def _obj_path(value: str) -> str:
    """'/Script/Flow.FlowNode_SubGraph'/Game/X.X:FlowNode_SubGraph_3'' -> '/Game/X.X:FlowNode_SubGraph_3'."""
    m = _OBJ_REF.search(value or "")
    return m.group(1) if m else value


def _pin_names(pins: Any) -> List[str]:
    if not isinstance(pins, dict):
        return []
    out = []
    for e in pins.get("elements", []):
        m = _PIN_NAME.search(e)
        out.append(m.group(1) if m else e)
    return out


def _connections(conns: Any) -> Dict[str, Dict[str, str]]:
    out = {}
    if not isinstance(conns, dict):
        return out
    for e in conns.get("entries", []):
        m = _CONN.search(e.get("value", ""))
        if m:
            out[e["key"]] = {"node": m.group(1), "pin": m.group(2)}
    return out


def _compact(v: Any) -> Any:
    """Shrink the generic serializer's output: object refs become paths, empty containers vanish."""
    if isinstance(v, dict):
        if "path" in v and "class" in v and "name" in v:
            return v["path"]
        if "count" in v and "elements" in v:
            if v["count"] == 0:
                return None
            els = [_compact(x) for x in v["elements"]]
            if v["count"] > len(v["elements"]):
                els.append("... %d more (truncated)" % (v["count"] - len(v["elements"])))
            return els
        if "count" in v and "entries" in v:
            if v["count"] == 0:
                return None
            return {e["key"]: _compact(e["value"]) for e in v["entries"]}
        return {k: _compact(x) for k, x in v.items()}
    if v in ("(None)", "()", "", "False", "0", "0.000000"):
        return None
    return v


def _node_summary(node_props: Dict[str, Any]) -> Dict[str, Any]:
    props = node_props.get("properties", {})
    settings = {}
    for k, v in props.items():
        if k in _NODE_BOILERPLATE:
            continue
        cv = _compact(v)
        if cv is not None:
            settings[k] = cv
    return {
        "name": node_props.get("name"),
        "class": node_props.get("class"),
        "inputs": _pin_names(props.get("InputPins")),
        "outputs": _pin_names(props.get("OutputPins")),
        "connections": _connections(props.get("Connections")),
        "settings": settings,
    }


def dump_flow_asset(send: Callable[[str, Dict[str, Any]], Optional[Dict[str, Any]]],
                    asset_path: str, include_graph: bool = True) -> Dict[str, Any]:
    """
    Read a flow asset through `send(command, params)`, which must speak the plugin's command protocol
    (the MCP server's UnrealConnection.send_command, or anything equivalent).
    """
    if "." not in asset_path.rsplit("/", 1)[-1]:
        asset_path = "%s.%s" % (asset_path, asset_path.rsplit("/", 1)[-1])

    def get_props(path: str, filt: Optional[List[str]] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"asset_path": path}
        if filt:
            params["property_filter"] = filt
        r = send("get_asset_properties", params) or {}
        return r.get("result", r)

    asset = get_props(asset_path)
    if "properties" not in asset:
        return {"success": False, "message": "Could not read %s: %s" % (asset_path, asset)}
    ap = asset["properties"]

    result: Dict[str, Any] = {
        "success": True,
        "path": asset_path,
        "class": asset.get("class"),
        "custom_inputs": _compact(ap.get("CustomInputs")),
        "custom_outputs": _compact(ap.get("CustomOutputs")),
        "nodes": {},
        "comments": [],
    }

    node_map = ap.get("Nodes", {})
    if isinstance(node_map, dict) and node_map.get("count", 0) > len(node_map.get("entries", [])):
        result["warning"] = "Node map truncated to %d of %d" % (len(node_map["entries"]), node_map["count"])
    for entry in node_map.get("entries", []) if isinstance(node_map, dict) else []:
        guid = entry["key"]
        result["nodes"][guid] = _node_summary(get_props(_obj_path(entry["value"])))

    if include_graph:
        graph = ap.get("FlowGraph")
        if isinstance(graph, dict) and "path" in graph:
            gnodes = get_props(graph["path"], ["Nodes"]).get("properties", {}).get("Nodes", {})
            for gv in gnodes.get("elements", []) if isinstance(gnodes, dict) else []:
                gp = get_props(_obj_path(gv), ["NodeComment", "NodePosX", "NodePosY", "NodeInstance",
                                               "NodeWidth", "NodeHeight"])
                p = gp.get("properties", {})
                comment = p.get("NodeComment", "")
                inst = p.get("NodeInstance")
                pos = [p.get("NodePosX"), p.get("NodePosY")]
                if isinstance(inst, dict):
                    # Attach the comment bubble and position to the runtime node it wraps.
                    for guid, n in result["nodes"].items():
                        if n["name"] == inst.get("name"):
                            n["pos"] = pos
                            if comment:
                                n["comment"] = comment
                            break
                elif comment:
                    # A free-standing comment box.
                    result["comments"].append({"text": comment, "pos": pos,
                                               "size": [p.get("NodeWidth"), p.get("NodeHeight")]})
    return result


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


def register_flow_tools(mcp: FastMCP):
    """Register flow graph tools with the MCP server."""

    @mcp.tool()
    def get_flow_asset(ctx: Context, asset_path: str, include_graph: bool = True) -> Dict[str, Any]:
        """
        Read a FlowGraph asset (FlowAsset / HALFlowAsset) as a node map an agent can follow.

        Args:
            asset_path: Content path, e.g. "/Game/Hallucination/Preproduction/VerticalSlice/FG_VSAct".
            include_graph: Also read the editor graph for node positions and comment boxes.

        Returns:
            Dict with "nodes" keyed by node GUID. Each node has class, input/output pin names,
            "connections" (output pin -> {node GUID, input pin}), "settings" (the node's own
            properties with boilerplate stripped, e.g. a SubGraph's Asset or a SceneSequence's
            SceneConfigs), and when include_graph is set its "pos" and any "comment" bubble.
            "comments" lists free-standing comment boxes. "custom_inputs"/"custom_outputs" are the
            asset's own pins when it is used as a SubGraph.
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            return dump_flow_asset(unreal.send_command, asset_path, include_graph)
        except Exception as e:
            logger.error("Error reading flow asset: %s", e)
            return {"success": False, "message": "Error reading flow asset: %s" % e}

    @mcp.tool()
    def create_flow_asset(ctx: Context, asset_path: str, asset_class: str = "FlowAsset",
                          save: bool = True) -> Dict[str, Any]:
        """
        Create an empty Flow asset (editor graph plus its Start node). Fails if the asset exists.

        Args:
            asset_path: Package path, e.g. "/Game/Hallucination/Campaign/Act2/FG_Act2".
            asset_class: "FlowAsset", "HALFlowAsset" (act root graphs), or a full class path.
            save: Save the new asset to disk.

        Returns:
            path, class, and start_node (guid, name, pins).
        """
        return _send("create_flow_asset", {"asset_path": asset_path, "asset_class": asset_class,
                                           "save": save})

    @mcp.tool()
    def add_flow_node(ctx: Context, asset_path: str, node_class: str, position: Optional[List[float]] = None,
                      properties: Optional[Dict[str, Any]] = None, comment: str = "",
                      save: bool = True) -> Dict[str, Any]:
        """
        Add a node to a Flow graph.

        Args:
            asset_path: The Flow asset.
            node_class: Class name with or without the FlowNode_ prefix ("SubGraph", "FlowNode_Timer"),
                its display name ("Moment Complete"), or a full path for Blueprint nodes.
            position: [x, y] in graph space.
            properties: Node properties, applied in order like Details-panel edits (so pins rebuild).
                Values are Unreal text format strings, numbers or bools. Gameplay tag properties take a
                tag name; tag containers take a list of tag names. Examples:
                {"NumEntries": 4}, {"Asset": "/Game/X/FG_Y.FG_Y"},
                {"IdentityTags": ["AudioController"], "NotifyTags": ["Act2.S1.Cleanup"]},
                {"NumEntries": 3, "SceneConfigs": "((SceneHierarchyTag=(TagName=\"Act2.S1\")),...)"}.
            comment: Comment bubble shown on the node.
            save: Save the asset afterwards.

        Returns:
            The node: guid, name, class, position, inputs, outputs, connections.
        """
        return _send("add_flow_node", _without_none({
            "asset_path": asset_path, "node_class": node_class, "position": position,
            "properties": properties, "comment": comment or None, "save": save}))

    @mcp.tool()
    def set_flow_node_properties(ctx: Context, asset_path: str, node: str,
                                 properties: Optional[Dict[str, Any]] = None, comment: Optional[str] = None,
                                 save: bool = True) -> Dict[str, Any]:
        """
        Set properties (and optionally the comment bubble) on an existing Flow node.

        Args:
            asset_path: The Flow asset.
            node: Node GUID, object name, or "Start".
            properties: As for add_flow_node.
            comment: New comment bubble text; "" clears it. Omit to leave it.
            save: Save the asset afterwards.
        """
        return _send("set_flow_node_properties", _without_none({
            "asset_path": asset_path, "node": node, "properties": properties, "comment": comment,
            "save": save}))

    @mcp.tool()
    def connect_flow_pins(ctx: Context, asset_path: str, from_node: str, from_pin: str, to_node: str,
                          to_pin: str, save: bool = True) -> Dict[str, Any]:
        """
        Connect an output pin to an input pin. An exec output holds one link, so an existing link on
        from_pin is replaced.

        Args:
            asset_path: The Flow asset.
            from_node / to_node: Node GUID, object name, or "Start".
            from_pin / to_pin: Pin names as get_flow_asset lists them ("Out", "Sequence_1", "Start", "In").
        """
        return _send("connect_flow_pins", {"asset_path": asset_path, "from_node": from_node,
                                           "from_pin": from_pin, "to_node": to_node, "to_pin": to_pin,
                                           "save": save})

    @mcp.tool()
    def disconnect_flow_pin(ctx: Context, asset_path: str, node: str, pin: str,
                            save: bool = True) -> Dict[str, Any]:
        """Break every link on one pin of a Flow node."""
        return _send("disconnect_flow_pin", {"asset_path": asset_path, "node": node, "pin": pin,
                                             "save": save})

    @mcp.tool()
    def delete_flow_node(ctx: Context, asset_path: str, node: str, save: bool = True) -> Dict[str, Any]:
        """Delete a Flow node and its links. The Start node cannot be deleted."""
        return _send("delete_flow_node", {"asset_path": asset_path, "node": node, "save": save})

    @mcp.tool()
    def add_flow_comment(ctx: Context, asset_path: str, text: str, position: Optional[List[float]] = None,
                         size: Optional[List[float]] = None, save: bool = True) -> Dict[str, Any]:
        """Add a comment box to a Flow graph. position [x, y], size [width, height]."""
        return _send("add_flow_comment", _without_none({
            "asset_path": asset_path, "text": text, "position": position, "size": size, "save": save}))

    @mcp.tool()
    def build_flow_graph(ctx: Context, asset_path: str, nodes: Optional[List[Dict[str, Any]]] = None,
                         connections: Optional[List[List[str]]] = None, comments: Optional[List[Dict[str, Any]]] = None,
                         create_class: Optional[str] = None, save: bool = True) -> Dict[str, Any]:
        """
        Build (part of) a Flow graph in one call: add nodes, then connect them, then add comment boxes.
        Prefer this over many single-node calls when laying out a graph.

        Args:
            asset_path: The Flow asset.
            nodes: [{"id": "local alias", "class": ..., "position": [x, y], "properties": {...},
                     "comment": "..."}]. Ids are local to this call and used in connections.
            connections: [[from, from_pin, to, to_pin], ...]. from/to are ids from `nodes`, "Start",
                or an existing node's GUID or object name.
            comments: [{"text": ..., "position": [x, y], "size": [w, h]}].
            create_class: If set, create the asset first with this class ("FlowAsset" or
                "HALFlowAsset"). Fails if the asset already exists.
            save: Save once at the end.

        Returns:
            path, and nodes keyed by id (plus "Start"), each with guid, pins and connections.
            On failure, steps before the failing one are applied in memory but not saved.
        """
        return _send("build_flow_graph", _without_none({
            "asset_path": asset_path, "nodes": nodes, "connections": connections, "comments": comments,
            "create_class": create_class, "save": save}))

    @mcp.tool()
    def list_flow_node_classes(ctx: Context, filter: str = "") -> Dict[str, Any]:
        """
        List Flow node classes that can be added (name, display name, path), optionally filtered by a
        substring of the class or display name.
        """
        return _send("list_flow_node_classes", {"filter": filter})
