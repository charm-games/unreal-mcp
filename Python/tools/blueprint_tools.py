"""
Blueprint Tools for Unreal MCP.

This module provides tools for creating and manipulating Blueprint assets in Unreal Engine.
"""

import logging
from typing import Dict, List, Any
from mcp.server.fastmcp import FastMCP, Context

# Get logger
logger = logging.getLogger("UnrealMCP")

def register_blueprint_tools(mcp: FastMCP):
    """Register Blueprint tools with the MCP server."""
    
    @mcp.tool()
    def create_blueprint(
        ctx: Context,
        name: str,
        parent_class: str,
        path: str = ""
    ) -> Dict[str, Any]:
        """
        Create a new Blueprint class.

        Args:
            name: Asset name, e.g. "BP_Act2_AudioController".
            parent_class: A full class path ("/Script/Hallucination.HALActAudioController", or a
                "/Game/..." Blueprint to derive from), which fails loudly if not found, or a short
                engine class name ("Actor", "Pawn"), which falls back to Actor if not found.
            path: Content folder to create it in, e.g. "/Game/Hallucination/Campaign/Act2".
                Defaults to "/Game/Blueprints".
        """
        # Import inside function to avoid circular imports
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
                
            params = {"name": name, "parent_class": parent_class}
            if path:
                params["path"] = path
            response = unreal.send_command("create_blueprint", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Blueprint creation response: {response}")
            return response or {}
            
        except Exception as e:
            error_msg = f"Error creating blueprint: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @mcp.tool()
    def add_component_to_blueprint(
        ctx: Context,
        blueprint_name: str,
        component_type: str,
        component_name: str,
        location: List[float] = [],
        rotation: List[float] = [],
        scale: List[float] = [],
        parent_component: str = None,
        component_properties: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """
        Add a component to a Blueprint.

        Each call compiles the blueprint after adding the component.
        When adding multiple components, call this once per component.
        Property changes via set_component_property can be batched freely.

        Args:
            blueprint_name: Name of the target Blueprint
            component_type: Type of component to add (use component class name without U prefix)
            component_name: Name for the new component
            location: [X, Y, Z] coordinates for component's position
            rotation: [Pitch, Yaw, Roll] values for component's rotation
            scale: [X, Y, Z] values for component's scale
            parent_component: Name of the parent component to attach to (from get_blueprint_components)
            skip_compile: If True, skip blueprint compilation (use when batching multiple additions)
            component_properties: Additional properties to set on the component

        Returns:
            Information about the added component
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            # Ensure all parameters are properly formatted
            params = {
                "blueprint_name": blueprint_name,
                "component_type": component_type,
                "component_name": component_name,
                "location": location or [0.0, 0.0, 0.0],
                "rotation": rotation or [0.0, 0.0, 0.0],
                "scale": scale or [1.0, 1.0, 1.0]
            }
            
            # Add parent component if specified
            if parent_component:
                params["parent_component"] = parent_component

            # Add component_properties if provided
            if component_properties and len(component_properties) > 0:
                params["component_properties"] = component_properties
            
            # Validate location, rotation, and scale formats
            for param_name in ["location", "rotation", "scale"]:
                param_value = params[param_name]
                if not isinstance(param_value, list) or len(param_value) != 3:
                    logger.error(f"Invalid {param_name} format: {param_value}. Must be a list of 3 float values.")
                    return {"success": False, "message": f"Invalid {param_name} format. Must be a list of 3 float values."}
                # Ensure all values are float
                params[param_name] = [float(val) for val in param_value]
            
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
                
            logger.info(f"Adding component to blueprint with params: {params}")
            response = unreal.send_command("add_component_to_blueprint", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Component addition response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error adding component to blueprint: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @mcp.tool()
    def set_static_mesh_properties(
        ctx: Context,
        blueprint_name: str,
        component_name: str,
        static_mesh: str = "/Engine/BasicShapes/Cube.Cube"
    ) -> Dict[str, Any]:
        """
        Set static mesh properties on a StaticMeshComponent.
        
        Args:
            blueprint_name: Name of the target Blueprint
            component_name: Name of the StaticMeshComponent
            static_mesh: Path to the static mesh asset (e.g., "/Engine/BasicShapes/Cube.Cube")
            
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
                "blueprint_name": blueprint_name,
                "component_name": component_name,
                "static_mesh": static_mesh
            }
            
            logger.info(f"Setting static mesh properties with params: {params}")
            response = unreal.send_command("set_static_mesh_properties", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Set static mesh properties response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error setting static mesh properties: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @mcp.tool()
    def set_component_property(
        ctx: Context,
        blueprint_name: str,
        component_name: str,
        property_name: str,
        property_value,
    ) -> Dict[str, Any]:
        """Set a property on a component in a Blueprint."""
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            params = {
                "blueprint_name": blueprint_name,
                "component_name": component_name,
                "property_name": property_name,
                "property_value": property_value
            }
            
            logger.info(f"Setting component property with params: {params}")
            response = unreal.send_command("set_component_property", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Set component property response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error setting component property: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @mcp.tool()
    def set_physics_properties(
        ctx: Context,
        blueprint_name: str,
        component_name: str,
        simulate_physics: bool = True,
        gravity_enabled: bool = True,
        mass: float = 1.0,
        linear_damping: float = 0.01,
        angular_damping: float = 0.0
    ) -> Dict[str, Any]:
        """Set physics properties on a component."""
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            params = {
                "blueprint_name": blueprint_name,
                "component_name": component_name,
                "simulate_physics": simulate_physics,
                "gravity_enabled": gravity_enabled,
                "mass": float(mass),
                "linear_damping": float(linear_damping),
                "angular_damping": float(angular_damping)
            }
            
            logger.info(f"Setting physics properties with params: {params}")
            response = unreal.send_command("set_physics_properties", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Set physics properties response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error setting physics properties: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @mcp.tool()
    def compile_blueprint(
        ctx: Context,
        blueprint_name: str
    ) -> Dict[str, Any]:
        """Compile a Blueprint."""
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            params = {
                "blueprint_name": blueprint_name
            }
            
            logger.info(f"Compiling blueprint: {blueprint_name}")
            response = unreal.send_command("compile_blueprint", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Compile blueprint response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error compiling blueprint: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def set_blueprint_property(
        ctx: Context,
        blueprint_name: str,
        property_name: str,
        property_value
    ) -> Dict[str, Any]:
        """
        Set a property on a Blueprint class default object.
        
        Args:
            blueprint_name: Name of the target Blueprint
            property_name: Name of the property to set
            property_value: Value to set the property to
            
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
                "blueprint_name": blueprint_name,
                "property_name": property_name,
                "property_value": property_value
            }
            
            logger.info(f"Setting blueprint property with params: {params}")
            response = unreal.send_command("set_blueprint_property", params)
            
            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}
            
            logger.info(f"Set blueprint property response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error setting blueprint property: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    # @mcp.tool() commented out, just use set_component_property instead
    def set_pawn_properties(
        ctx: Context,
        blueprint_name: str,
        auto_possess_player: str = "",
        use_controller_rotation_yaw: bool = None,
        use_controller_rotation_pitch: bool = None,
        use_controller_rotation_roll: bool = None,
        can_be_damaged: bool = None
    ) -> Dict[str, Any]:
        """
        Set common Pawn properties on a Blueprint.
        This is a utility function that sets multiple pawn-related properties at once.
        
        Args:
            blueprint_name: Name of the target Blueprint (must be a Pawn or Character)
            auto_possess_player: Auto possess player setting (None, "Disabled", "Player0", "Player1", etc.)
            use_controller_rotation_yaw: Whether the pawn should use the controller's yaw rotation
            use_controller_rotation_pitch: Whether the pawn should use the controller's pitch rotation
            use_controller_rotation_roll: Whether the pawn should use the controller's roll rotation
            can_be_damaged: Whether the pawn can be damaged
            
        Returns:
            Response indicating success or failure with detailed results for each property
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}
            
            # Define the properties to set
            properties = {}
            if auto_possess_player and auto_possess_player != "":
                properties["auto_possess_player"] = auto_possess_player
            
            # Only include boolean properties if they were explicitly set
            if use_controller_rotation_yaw is not None:
                properties["bUseControllerRotationYaw"] = use_controller_rotation_yaw
            if use_controller_rotation_pitch is not None:
                properties["bUseControllerRotationPitch"] = use_controller_rotation_pitch
            if use_controller_rotation_roll is not None:
                properties["bUseControllerRotationRoll"] = use_controller_rotation_roll
            if can_be_damaged is not None:
                properties["bCanBeDamaged"] = can_be_damaged
                
            if not properties:
                logger.warning("No properties specified to set")
                return {"success": True, "message": "No properties specified to set", "results": {}}
            
            # Set each property using the generic set_blueprint_property function
            results = {}
            overall_success = True
            
            for prop_name, prop_value in properties.items():
                params = {
                    "blueprint_name": blueprint_name,
                    "property_name": prop_name,
                    "property_value": prop_value
                }
                
                logger.info(f"Setting pawn property {prop_name} to {prop_value}")
                response = unreal.send_command("set_blueprint_property", params)
                
                if not response:
                    logger.error(f"No response from Unreal Engine for property {prop_name}")
                    results[prop_name] = {"success": False, "message": "No response from Unreal Engine"}
                    overall_success = False
                    continue
                
                results[prop_name] = response
                if not response.get("success", False):
                    overall_success = False
            
            return {
                "success": overall_success,
                "message": "Pawn properties set" if overall_success else "Some pawn properties failed to set",
                "results": results
            }
            
        except Exception as e:
            error_msg = f"Error setting pawn properties: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @mcp.tool()
    def get_blueprint_variables(
        ctx: Context,
        blueprint_name: str
    ) -> Dict[str, Any]:
        """
        Get all variables defined in a Blueprint.

        Args:
            blueprint_name: Name or path of the Blueprint (e.g., "/Game/Hallucination/Puzzles/BPC_PressAndHoldInteraction")

        Returns:
            Dict containing:
            - blueprint: Name of the blueprint
            - count: Number of variables
            - variables: Array of variable info objects with:
              - name: Variable name
              - type: Human-readable type name
              - category: Variable category
              - pin_category: Raw pin category
              - pin_subcategory_object: Path to subcategory object if applicable
              - is_exposed: Whether exposed to editor
              - is_read_only: Whether read-only
              - is_instance_editable: Whether editable per instance
              - default_value: Default value if set
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name
            }

            logger.info(f"Getting blueprint variables for: {blueprint_name}")
            response = unreal.send_command("get_blueprint_variables", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Get blueprint variables response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error getting blueprint variables: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def reparent_blueprint(
        ctx: Context,
        blueprint_name: str,
        new_parent_class: str
    ) -> Dict[str, Any]:
        """
        Reparent a Blueprint to a new parent class.

        WARNING: This operation can cause data loss if the new parent class
        doesn't have matching properties. Variables and functions that don't
        exist in the new parent will be removed.

        Args:
            blueprint_name: Name or path of the Blueprint (e.g., "/Game/Hallucination/Puzzles/BPC_PressAndHoldInteraction")
            new_parent_class: The new parent class. Can be:
                - Full path: "/Script/Hallucination.HALPuzzleInteractionBehaviorComponent"
                - Class name: "HALPuzzleInteractionBehaviorComponent"
                - Class name with prefix: "UHALPuzzleInteractionBehaviorComponent"

        Returns:
            Dict containing:
            - blueprint: Name of the blueprint
            - old_parent: Previous parent class name
            - new_parent: New parent class name
            - success: Whether the operation succeeded
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name,
                "new_parent_class": new_parent_class
            }

            logger.info(f"Reparenting blueprint {blueprint_name} to {new_parent_class}")
            response = unreal.send_command("reparent_blueprint", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Reparent blueprint response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error reparenting blueprint: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_blueprint_components(
        ctx: Context,
        blueprint_name: str
    ) -> Dict[str, Any]:
        """
        Get all components defined in a Blueprint.

        Args:
            blueprint_name: Name or path of the Blueprint (e.g., "/Game/Hallucination/Player/Interaction/BP_HAL_InteractionTarget")

        Returns:
            Dict containing:
            - blueprint: Name of the blueprint
            - parent_class: Parent class of the blueprint
            - count: Number of components
            - components: Array of component info objects with:
              - name: Component variable name
              - class: Component class name
              - class_path: Full path to component class
              - parent: Parent component name (if any)
              - location: [X, Y, Z] relative location (for scene components)
              - rotation: [Pitch, Yaw, Roll] relative rotation (for scene components)
              - scale: [X, Y, Z] relative scale (for scene components)
              - visible: Whether the component is visible (for scene components)
              - child_actor_class: Actor class name (for ChildActorComponents only)
              - child_actor_class_path: Full path to actor class (for ChildActorComponents only)
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name
            }

            logger.info(f"Getting blueprint components for: {blueprint_name}")
            response = unreal.send_command("get_blueprint_components", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Get blueprint components response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error getting blueprint components: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def set_component_parent(
        ctx: Context,
        blueprint_name: str,
        component_name: str,
        parent_name: str
    ) -> Dict[str, Any]:
        """
        Re-parent a component in a Blueprint's SCS tree.

        Moves a component to be a child of a different parent component.
        Works with parents in the same BP or inherited from parent BPs.

        Args:
            blueprint_name: Name or path of the Blueprint
            component_name: Name of the component to re-parent
            parent_name: Name of the new parent component

        Returns:
            Dict with success status
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name,
                "component_name": component_name,
                "parent_name": parent_name
            }

            logger.info(f"Setting component parent: {blueprint_name} -> {component_name} under {parent_name}")
            response = unreal.send_command("set_component_parent", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Set component parent response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error setting component parent: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_component_properties(
        ctx: Context,
        blueprint_name: str,
        component_name: str
    ) -> Dict[str, Any]:
        """
        Get all editable properties of a specific component in a Blueprint.

        Returns all UPROPERTY values that are EditAnywhere or BlueprintVisible.
        For ChildActorComponents, also includes the child actor template's properties
        under a "child_actor_template" sub-object.

        Args:
            blueprint_name: Name or path of the Blueprint
            component_name: Name of the component variable (from get_blueprint_components)

        Returns:
            Dict containing:
            - blueprint: Name of the blueprint
            - component: Component name
            - class: Component class name
            - properties: Object with property name/value pairs
              - For ChildActorComponents, includes "child_actor_template" with template properties
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name,
                "component_name": component_name
            }

            logger.info(f"Getting component properties: {blueprint_name} -> {component_name}")
            response = unreal.send_command("get_component_properties", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Get component properties response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error getting component properties: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_blueprint_event_graph(
        ctx: Context,
        blueprint_name: str,
        filter_node_types: List[str] = None,
        include_connections: bool = True,
        max_nodes: int = 0
    ) -> Dict[str, Any]:
        """
        Get all nodes in a Blueprint's event graph with optional filtering.

        WARNING: For complex Blueprints (>50 nodes), use check_blueprint_complexity first
        or use filtering parameters to reduce output size.

        Args:
            blueprint_name: Name or path of the Blueprint (e.g., "/Game/Hallucination/Player/Interaction/BP_HAL_InteractionTarget")
            filter_node_types: Optional list of node types to include. Supported types:
                - "Event" or "K2Node_Event" - Event nodes
                - "FunctionCall" or "K2Node_CallFunction" - Function call nodes
                - "VariableGet" or "K2Node_VariableGet" - Variable get nodes
                - "VariableSet" or "K2Node_VariableSet" - Variable set nodes
                - "Other" - All other node types
            include_connections: Whether to include pin connection information (default True).
                Set to False to reduce output size significantly.
            max_nodes: Maximum number of nodes to return (default 0 = unlimited).
                Useful for previewing large graphs.

        Returns:
            Dict containing:
            - blueprint: Name of the blueprint
            - graph_name: Name of the event graph
            - node_count: Number of nodes returned (after filtering)
            - total_nodes: Total number of nodes in the graph (before filtering)
            - filtered: Whether any filtering was applied
            - nodes: Array of node info objects with:
              - guid: Node GUID
              - class: Node class name
              - title: Node title
              - pos_x: X position in graph
              - pos_y: Y position in graph
              - node_type: Type of node (Event, FunctionCall, VariableGet, VariableSet, Other)
              - event_name: Event name (for Event nodes)
              - function_name: Function name (for FunctionCall nodes)
              - function_class: Class containing the function (for FunctionCall nodes)
              - variable_name: Variable name (for VariableGet/Set nodes)
              - pins: Array of pin info objects with:
                - name: Pin name
                - direction: Input or Output
                - type: Pin type
                - default_value: Default value (if any)
                - connections: Array of connected node/pin info (only if include_connections=True)

        Example usage:
            # Get only event nodes without connections (minimal output)
            get_blueprint_event_graph("BP_MyBlueprint",
                                     filter_node_types=["Event"],
                                     include_connections=False)

            # Get first 10 nodes for preview
            get_blueprint_event_graph("BP_MyBlueprint", max_nodes=10)
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name,
                "include_connections": include_connections
            }

            if filter_node_types:
                params["filter_node_types"] = filter_node_types

            if max_nodes > 0:
                params["max_nodes"] = max_nodes

            logger.info(f"Getting blueprint event graph for: {blueprint_name} with params: {params}")
            response = unreal.send_command("get_blueprint_event_graph", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Get blueprint event graph response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error getting blueprint event graph: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def check_blueprint_complexity(
        ctx: Context,
        blueprint_name: str
    ) -> Dict[str, Any]:
        """
        Check the complexity of a Blueprint before fetching full details.

        This tool provides a size estimate and recommendation for how to best
        retrieve Blueprint data without overwhelming the context window.

        Args:
            blueprint_name: Name or path of the Blueprint

        Returns:
            Dict containing:
            - status: Complexity level (small, medium, large, very_large)
            - node_count: Number of nodes in the event graph
            - connection_count: Number of pin connections
            - execution_path_count: Number of execution entry points (events)
            - estimated_tokens: Rough token count estimate
            - recommendation: Suggested approach (use_full_graph, use_summary_or_filter, etc.)
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name
            }

            logger.info(f"Checking blueprint complexity for: {blueprint_name}")
            response = unreal.send_command("check_blueprint_complexity", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Check blueprint complexity response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error checking blueprint complexity: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_blueprint_summary(
        ctx: Context,
        blueprint_name: str
    ) -> Dict[str, Any]:
        """
        Get a high-level summary of a Blueprint without detailed node information.

        This is much more compact than get_blueprint_event_graph and is ideal for
        understanding Blueprint structure before diving into details.

        Args:
            blueprint_name: Name or path of the Blueprint

        Returns:
            Dict containing:
            - blueprint: Name of the blueprint
            - parent_class: Parent class name
            - component_count: Number of components
            - variable_count: Number of variables
            - custom_events: Array of custom event names
            - custom_functions: Array of custom function names
            - blueprint_events: Array of standard Blueprint events (ReceiveBeginPlay, etc.)
            - input_actions: Array of input action event names
            - complexity: Object with total_nodes, execution_paths, estimated_loc
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name
            }

            logger.info(f"Getting blueprint summary for: {blueprint_name}")
            response = unreal.send_command("get_blueprint_summary", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Get blueprint summary response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error getting blueprint summary: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_blueprint_function(
        ctx: Context,
        blueprint_name: str,
        function_name: str
    ) -> Dict[str, Any]:
        """
        Get the implementation of a single function or event from a Blueprint.

        This returns only the nodes for the specified function/event, not the entire
        event graph. Much more efficient for analyzing specific functionality.

        Args:
            blueprint_name: Name or path of the Blueprint
            function_name: Name of the function or event to retrieve

        Returns:
            Dict containing:
            - blueprint: Name of the blueprint
            - function_name: Name of the function/event
            - type: "Function" or "Event"
            - nodes: Array of node objects (same format as get_blueprint_event_graph)
            - node_count: Number of nodes in this function
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name,
                "function_name": function_name
            }

            logger.info(f"Getting blueprint function {function_name} for: {blueprint_name}")
            response = unreal.send_command("get_blueprint_function", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Get blueprint function response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error getting blueprint function: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_blueprint_pseudocode(
        ctx: Context,
        blueprint_name: str
    ) -> Dict[str, Any]:
        """
        Convert a Blueprint's event graph to human-readable pseudocode.

        This is the most compact representation and is ideal for understanding
        Blueprint logic without getting overwhelmed by node connection details.

        Args:
            blueprint_name: Name or path of the Blueprint

        Returns:
            Dict containing:
            - blueprint: Name of the blueprint
            - pseudocode: Multi-line string with readable pseudocode
            - line_count: Number of lines in the pseudocode

        Example pseudocode output:
            Event ReceiveBeginPlay:
              - Set bIsActive = True
              - Call InitializeComponents
              - Branch on bShouldStart
                - Call StartBehavior

            Custom Event OnInteractionComplete:
              - Call EndBehavior
              - Set bIsActive = False
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name
            }

            logger.info(f"Getting blueprint pseudocode for: {blueprint_name}")
            response = unreal.send_command("get_blueprint_pseudocode", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Get blueprint pseudocode response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error getting blueprint pseudocode: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def get_blueprint_interfaces(
        ctx: Context,
        blueprint_name: str
    ) -> Dict[str, Any]:
        """
        Get all interfaces implemented by a Blueprint.

        Args:
            blueprint_name: Name or path of the Blueprint (e.g., "/Game/Hallucination/Puzzles/BP_MyBlueprint")

        Returns:
            Dict containing:
            - blueprint: Name of the blueprint
            - count: Number of interfaces
            - interfaces: Array of interface info objects with:
              - name: Interface class name
              - class_path: Full path to interface class
              - is_blueprint_interface: Whether this is a Blueprint interface (vs C++)
              - functions: Array of function info objects with:
                - name: Function name
                - is_event: Whether it's a BlueprintEvent
                - is_callable: Whether it's BlueprintCallable
                - parameters: Array of parameter info
                - return_type: Return type (if any)
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {"success": False, "message": "Failed to connect to Unreal Engine"}

            params = {
                "blueprint_name": blueprint_name
            }

            logger.info(f"Getting blueprint interfaces for: {blueprint_name}")
            response = unreal.send_command("get_blueprint_interfaces", params)

            if not response:
                logger.error("No response from Unreal Engine")
                return {"success": False, "message": "No response from Unreal Engine"}

            logger.info(f"Get blueprint interfaces response: {response}")
            return response

        except Exception as e:
            error_msg = f"Error getting blueprint interfaces: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    @mcp.tool()
    def find_blueprints_by_class(
        ctx: Context,
        class_name: str
    ) -> Dict[str, Any]:
        """
        Find all Blueprints that inherit from a given C++ class.

        Searches the Asset Registry for Blueprint assets whose
        generated class is a child of the specified class. Returns
        both direct and indirect descendants.

        Args:
            class_name: Name of the C++ class to search for.
                Can be:
                - Short name: "InteractableAssembly"
                - With prefix: "AInteractableAssembly"
                - Full path: "/Script/Hallucination.AInteractableAssembly"

        Returns:
            Dict containing:
            - class: Resolved class name
            - count: Number of matching Blueprints
            - blueprints: Array of objects with:
              - path: Full asset path
              - name: Asset name
              - parent_class: Direct parent class name
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.error("Failed to connect to Unreal Engine")
                return {
                    "success": False,
                    "message": "Failed to connect to Unreal Engine"
                }

            params = {
                "class_name": class_name
            }

            logger.info(
                f"Finding blueprints by class: {class_name}"
            )
            response = unreal.send_command(
                "find_blueprints_by_class", params
            )

            if not response:
                logger.error("No response from Unreal Engine")
                return {
                    "success": False,
                    "message": "No response from Unreal Engine"
                }

            logger.info(
                f"Find blueprints by class response: {response}"
            )
            return response

        except Exception as e:
            error_msg = (
                f"Error finding blueprints by class: {e}"
            )
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    logger.info("Blueprint tools registered successfully")