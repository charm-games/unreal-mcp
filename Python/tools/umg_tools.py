"""
UMG Tools for Unreal MCP.

This module provides tools for creating and manipulating UMG Widget Blueprints in Unreal Engine.
"""

import logging
from typing import Any, Dict, List, Optional
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

def register_umg_tools(mcp: FastMCP):
    """Register UMG tools with the MCP server."""

    @mcp.tool()
    def create_umg_widget_blueprint(
        ctx: Context,
        widget_name: str,
        parent_class: str = "UserWidget",
        path: str = "/Game/UI",
        root_widget_class: str = "CanvasPanel"
    ) -> Dict[str, Any]:
        """
        Create a new UMG Widget Blueprint.
        
        Args:
            widget_name: Name of the widget blueprint to create
            parent_class: Parent class. Abstract C++ bases need a path: "/Script/Hallucination.HALFooWidget"
            path: Content browser folder to create it in
            root_widget_class: Class of the root widget; "" for none (the first add_widget becomes root)
            
        Returns:
            Dict containing success status and widget path
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            params = {
                "widget_name": widget_name,
                "parent_class": parent_class,
                "path": path,
                "root_widget_class": root_widget_class
            }
            
            logger.info(f"Creating UMG Widget Blueprint with params: {params}")
            response = unreal.send_command("create_umg_widget_blueprint", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Create UMG Widget Blueprint response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error creating UMG Widget Blueprint: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def add_text_block_to_widget(
        ctx: Context,
        widget_name: str,
        text_block_name: str,
        text: str = "",
        position: List[float] = [0.0, 0.0],
        size: List[float] = [200.0, 50.0],
        font_size: int = 12,
        color: List[float] = [1.0, 1.0, 1.0, 1.0]
    ) -> Dict[str, Any]:
        """
        Add a Text Block widget to a UMG Widget Blueprint.
        
        Args:
            widget_name: Name of the target Widget Blueprint
            text_block_name: Name to give the new Text Block
            text: Initial text content
            position: [X, Y] position in the canvas panel
            size: [Width, Height] of the text block
            font_size: Font size in points
            color: [R, G, B, A] color values (0.0 to 1.0)
            
        Returns:
            Dict containing success status and text block properties
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            params = {
                "widget_name": widget_name,
                "text_block_name": text_block_name,
                "text": text,
                "position": position,
                "size": size,
                "font_size": font_size,
                "color": color
            }
            
            logger.info(f"Adding Text Block to widget with params: {params}")
            response = unreal.send_command("add_text_block_to_widget", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Add Text Block response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error adding Text Block to widget: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def add_button_to_widget(
        ctx: Context,
        widget_name: str,
        button_name: str,
        text: str = "",
        position: List[float] = [0.0, 0.0],
        size: List[float] = [200.0, 50.0],
        font_size: int = 12,
        color: List[float] = [1.0, 1.0, 1.0, 1.0],
        background_color: List[float] = [0.1, 0.1, 0.1, 1.0]
    ) -> Dict[str, Any]:
        """
        Add a Button widget to a UMG Widget Blueprint.
        
        Args:
            widget_name: Name of the target Widget Blueprint
            button_name: Name to give the new Button
            text: Text to display on the button
            position: [X, Y] position in the canvas panel
            size: [Width, Height] of the button
            font_size: Font size for button text
            color: [R, G, B, A] text color values (0.0 to 1.0)
            background_color: [R, G, B, A] button background color values (0.0 to 1.0)
            
        Returns:
            Dict containing success status and button properties
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            params = {
                "widget_name": widget_name,
                "button_name": button_name,
                "text": text,
                "position": position,
                "size": size,
                "font_size": font_size,
                "color": color,
                "background_color": background_color
            }
            
            logger.info(f"Adding Button to widget with params: {params}")
            response = unreal.send_command("add_button_to_widget", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Add Button response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error adding Button to widget: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def bind_widget_event(
        ctx: Context,
        widget_name: str,
        widget_component_name: str,
        event_name: str,
        function_name: str = ""
    ) -> Dict[str, Any]:
        """
        Bind an event on a widget component to a function.
        
        Args:
            widget_name: Name of the target Widget Blueprint
            widget_component_name: Name of the widget component (button, etc.)
            event_name: Name of the event to bind (OnClicked, etc.)
            function_name: Name of the function to create/bind to (defaults to f"{widget_component_name}_{event_name}")
            
        Returns:
            Dict containing success status and binding information
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            # If no function name provided, create one from component and event names
            if not function_name:
                function_name = f"{widget_component_name}_{event_name}"
            
            params = {
                "widget_name": widget_name,
                "widget_component_name": widget_component_name,
                "event_name": event_name,
                "function_name": function_name
            }
            
            logger.info(f"Binding widget event with params: {params}")
            response = unreal.send_command("bind_widget_event", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Bind widget event response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error binding widget event: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def add_widget_to_viewport(
        ctx: Context,
        widget_name: str,
        z_order: int = 0
    ) -> Dict[str, Any]:
        """
        Add a Widget Blueprint instance to the viewport.
        
        Args:
            widget_name: Name of the Widget Blueprint to add
            z_order: Z-order for the widget (higher numbers appear on top)
            
        Returns:
            Dict containing success status and widget instance information
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            params = {
                "widget_name": widget_name,
                "z_order": z_order
            }
            
            logger.info(f"Adding widget to viewport with params: {params}")
            response = unreal.send_command("add_widget_to_viewport", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Add widget to viewport response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error adding widget to viewport: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def set_text_block_binding(
        ctx: Context,
        widget_name: str,
        text_block_name: str,
        binding_property: str,
        binding_type: str = "Text"
    ) -> Dict[str, Any]:
        """
        Set up a property binding for a Text Block widget.
        
        Args:
            widget_name: Name of the target Widget Blueprint
            text_block_name: Name of the Text Block to bind
            binding_property: Name of the property to bind to
            binding_type: Type of binding (Text, Visibility, etc.)
            
        Returns:
            Dict containing success status and binding information
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            params = {
                "widget_name": widget_name,
                "text_block_name": text_block_name,
                "binding_property": binding_property,
                "binding_type": binding_type
            }
            
            logger.info(f"Setting text block binding with params: {params}")
            response = unreal.send_command("set_text_block_binding", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Set text block binding response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error setting text block binding: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}


    @mcp.tool()
    def get_widget_tree(ctx: Context, blueprint_name: str) -> Dict[str, Any]:
        """
        Get a Widget Blueprint's widget hierarchy, root first, in child order.

        Each entry has name, class (native name, or asset path for a Widget Blueprint), depth, parent,
        is_variable, and - only where they differ from defaults - "properties" (the widget's) and "slot"
        (its layout in the parent: anchors/offsets for a canvas, padding/size/alignment for a box), as
        Unreal text. slot_class tells you which slot properties exist.

        Args:
            blueprint_name: Full content path, e.g. "/Game/Hallucination/Player/WBP_HAL_HUD"
        """
        return _send("get_widget_tree", {"blueprint_name": blueprint_name})

    @mcp.tool()
    def add_widget(
        ctx: Context,
        blueprint_name: str,
        widget_class: str,
        widget_name: str,
        parent_name: str = "",
        index: int = -1,
        is_variable: Optional[bool] = None,
        properties: Optional[Dict[str, Any]] = None,
        slot_properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a widget to a Widget Blueprint's tree, then compile (compile_status is reported).

        Args:
            blueprint_name: Full content path of the Widget Blueprint to edit
            widget_class: Native class name ("HorizontalBox", "Image", "CommonActionWidget"), a
                "/Script/Module.Class" path, or a Widget Blueprint path ("/Game/UI/WBP_Foo") to nest one
            widget_name: Name for the new widget; must be unique in the tree. Name it after a C++
                BindWidget property to bind it.
            parent_name: Panel to add it to. Empty: into the root panel, or becomes the root if there is none.
            index: Child position in the parent; -1 appends
            is_variable: Expose the widget as a Blueprint variable
            properties: Widget properties, set like the Details panel. Keys may be dotted paths
                ("Brush.ImageSize"); values are Unreal text-format strings, numbers or bools.
                A nested Widget Blueprint's own properties (e.g. "PromptSlot") go here too.
            slot_properties: Layout properties of the slot in the parent, same format. Canvas:
                {"LayoutData": "(Offsets=(Left=-20,Top=-20,Right=0,Bottom=0),Anchors=(Minimum=(X=1,Y=1),
                Maximum=(X=1,Y=1)),Alignment=(X=1,Y=1))", "bAutoSize": true}. Box: {"Padding":
                "(Left=0,Top=4,Right=0,Bottom=0)", "HorizontalAlignment": "HAlign_Right"}.
        """
        params: Dict[str, Any] = {
            "blueprint_name": blueprint_name,
            "widget_class": widget_class,
            "widget_name": widget_name,
            "parent_name": parent_name,
            "index": index,
        }
        if is_variable is not None:
            params["is_variable"] = is_variable
        if properties:
            params["properties"] = properties
        if slot_properties:
            params["slot_properties"] = slot_properties
        return _send("add_widget", params)

    @mcp.tool()
    def set_widget_properties(
        ctx: Context,
        blueprint_name: str,
        widget_name: str,
        properties: Optional[Dict[str, Any]] = None,
        slot_properties: Optional[Dict[str, Any]] = None,
        is_variable: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Set properties on a widget in a Widget Blueprint and/or its slot, then compile.
        Same value format as add_widget. Use get_widget_tree to see current values.

        Args:
            blueprint_name: Full content path of the Widget Blueprint
            widget_name: Widget to edit
            properties: Widget properties (dotted paths allowed)
            slot_properties: Slot (layout) properties
            is_variable: Expose/hide the widget as a Blueprint variable
        """
        params: Dict[str, Any] = {"blueprint_name": blueprint_name, "widget_name": widget_name}
        if properties:
            params["properties"] = properties
        if slot_properties:
            params["slot_properties"] = slot_properties
        if is_variable is not None:
            params["is_variable"] = is_variable
        return _send("set_widget_properties", params)

    @mcp.tool()
    def remove_widgets(ctx: Context, blueprint_name: str, widget_names: List[str]) -> Dict[str, Any]:
        """
        Delete widgets (and their children) from a Widget Blueprint, as the designer's Delete does:
        property bindings and the graph's Get nodes for those widgets go too. Then compile.
        Nothing is removed if any name is missing.

        Args:
            blueprint_name: Full content path of the Widget Blueprint
            widget_names: Names of the widgets to delete
        """
        return _send("remove_widgets", {"blueprint_name": blueprint_name, "widget_names": widget_names})

    logger.info("UMG tools registered successfully") 