"""TensorBoard Flight Plugin.

This module implements the TensorBoard plugin interface for the flight
visualization plugin.
"""

import io
import json
import os
import glob as glob_module
from pathlib import Path
from typing import Dict, Any, List
from werkzeug import wrappers
from werkzeug.exceptions import NotFound

from tensorboard.backend import http_util
from tensorboard.plugins import base_plugin

# Import ACMI export functionality
from tensorboard_flight.acmi import ACMIWriter
from tensorboard_flight.data.schema import (
    FlightDataPoint, FlightEpisode, Orientation, Telemetry, RLMetrics
)
import numpy as np


class FlightPlugin(base_plugin.TBPlugin):
    """TensorBoard plugin for flight trajectory visualization."""

    plugin_name = "flight"

    def __init__(self, context):
        """Initialize the plugin.

        Args:
            context: TensorBoard plugin context
        """
        self.context = context
        self.multiplexer = context.multiplexer

    def get_plugin_apps(self):
        """Return WSGI applications for the plugin's routes.

        Returns:
            Dict mapping route paths to WSGI applications
        """
        return {
            "/": self._serve_index,
            "/runs": self._serve_runs,
            "/episodes": self._serve_episodes,
            "/episode_data": self._serve_episode_data,
            "/export_acmi": self._serve_export_acmi,
            "/tags": self._serve_tags,
            "/index.html": self._serve_index,
            "/static/*": self._serve_static_file,
        }

    def is_active(self):
        """Check if plugin should be active.

        Returns:
            True if there is flight data to display
        """
        # Check if there are any runs - we'll check for flight data when accessed
        if not self.multiplexer:
            return False

        # Check if any run has flight plugin data by reading event files directly
        from tensorboard.backend.event_processing.event_file_loader import EventFileLoader

        for run in self.multiplexer.Runs():
            try:
                run_path = self.multiplexer.RunPaths().get(run)
                if not run_path:
                    continue

                # Find event files in run directory
                event_files = glob_module.glob(os.path.join(run_path, "events.out.tfevents.*"))
                for event_file in event_files:
                    loader = EventFileLoader(event_file)
                    for event in loader.Load():
                        if hasattr(event, 'summary') and event.summary.value:
                            for value in event.summary.value:
                                if hasattr(value, 'metadata') and hasattr(value.metadata, 'plugin_data'):
                                    if value.metadata.plugin_data.plugin_name == self.plugin_name:
                                        return True
            except Exception:
                continue

        return False

    def frontend_metadata(self):
        """Return metadata about the plugin frontend.

        Returns:
            Dictionary with frontend metadata
        """
        # Use ES module that directly manipulates DOM
        return base_plugin.FrontendMetadata(
            es_module_path="/static/plugin_loader.js",
            tab_name="Flight",
            disable_reload=False,
        )

    @wrappers.Request.application
    def _serve_runs(self, request):
        """Serve list of available runs.

        Args:
            request: Werkzeug request

        Returns:
            JSON response with list of runs
        """
        from tensorboard.backend.event_processing.event_file_loader import EventFileLoader

        runs = self.multiplexer.Runs()
        flight_runs = []

        print(f"[FlightPlugin] _serve_runs called, multiplexer runs: {runs}")

        for run in runs:
            try:
                run_path = self.multiplexer.RunPaths().get(run)
                print(f"[FlightPlugin] Processing run '{run}' at path: {run_path}")

                if not run_path:
                    continue

                # Find event files and collect flight tags
                flight_tags = set()
                event_files = glob_module.glob(os.path.join(run_path, "events.out.tfevents.*"))
                print(f"[FlightPlugin] Found {len(event_files)} event files")

                for event_file in event_files:
                    loader = EventFileLoader(event_file)
                    for event in loader.Load():
                        if hasattr(event, 'summary') and event.summary.value:
                            for value in event.summary.value:
                                if hasattr(value, 'metadata') and hasattr(value.metadata, 'plugin_data'):
                                    if value.metadata.plugin_data.plugin_name == self.plugin_name:
                                        flight_tags.add(value.tag)
                                        print(f"[FlightPlugin] Found flight tag: {value.tag}")

                if flight_tags:
                    flight_runs.append({
                        "run": run,
                        "tags": list(flight_tags),
                    })
                    print(f"[FlightPlugin] Added run with {len(flight_tags)} tags")
            except Exception as e:
                print(f"[FlightPlugin] Error processing run {run}: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"[FlightPlugin] Returning {len(flight_runs)} runs")
        return http_util.Respond(
            request,
            {"runs": flight_runs},
            "application/json",
        )

    @wrappers.Request.application
    def _serve_episodes(self, request):
        """Serve list of episodes for a run.

        Args:
            request: Werkzeug request with 'run' parameter

        Returns:
            JSON response with episode metadata
        """
        from tensorboard.backend.event_processing.event_file_loader import EventFileLoader

        run = request.args.get("run")
        if not run:
            return http_util.Respond(
                request,
                {"error": "Missing 'run' parameter"},
                "application/json",
                code=400,
            )

        print(f"[FlightPlugin] _serve_episodes called for run: {run}")

        try:
            run_path = self.multiplexer.RunPaths().get(run)
            if not run_path:
                print(f"[FlightPlugin] No path found for run: {run}")
                return http_util.Respond(
                    request,
                    {"episodes": []},
                    "application/json",
                )

            print(f"[FlightPlugin] Run path: {run_path}")

            # Collect episodes from all event files
            episodes = []
            event_files = glob_module.glob(os.path.join(run_path, "events.out.tfevents.*"))
            print(f"[FlightPlugin] Found {len(event_files)} event files")

            for event_file in event_files:
                loader = EventFileLoader(event_file)
                for event in loader.Load():
                    if hasattr(event, 'summary') and event.summary.value:
                        for value in event.summary.value:
                            if hasattr(value, 'metadata') and hasattr(value.metadata, 'plugin_data'):
                                if value.metadata.plugin_data.plugin_name == self.plugin_name:
                                    try:
                                        content = value.metadata.plugin_data.content
                                        episode_data = json.loads(content.decode('utf-8'))
                                        episodes.append({
                                            "episode_id": episode_data.get("episode_id"),
                                            "agent_id": episode_data.get("agent_id"),
                                            "episode_number": episode_data.get("episode_number"),
                                            "total_steps": episode_data.get("total_steps"),
                                            "total_reward": episode_data.get("total_reward"),
                                            "success": episode_data.get("success"),
                                            "duration": episode_data.get("duration"),
                                            "step": event.step,
                                            "wall_time": event.wall_time,
                                        })
                                        print(f"[FlightPlugin] Found episode: {episode_data.get('episode_id')}")
                                    except Exception as e:
                                        print(f"[FlightPlugin] Error parsing episode data: {e}")
                                        continue

            print(f"[FlightPlugin] Returning {len(episodes)} episodes")
            return http_util.Respond(
                request,
                {"episodes": episodes},
                "application/json",
            )
        except Exception as e:
            print(f"[FlightPlugin] Error in _serve_episodes: {e}")
            import traceback
            traceback.print_exc()
            return http_util.Respond(
                request,
                {"error": str(e), "episodes": []},
                "application/json",
                code=500,
            )

    @wrappers.Request.application
    def _serve_episode_data(self, request):
        """Serve full trajectory data for an episode.

        Args:
            request: Werkzeug request with 'run' and 'episode_id' parameters

        Returns:
            JSON response with episode trajectory
        """
        from tensorboard.backend.event_processing.event_file_loader import EventFileLoader

        run = request.args.get("run")
        episode_id = request.args.get("episode_id")

        if not run or not episode_id:
            return http_util.Respond(
                request,
                {"error": "Missing 'run' or 'episode_id' parameter"},
                "application/json",
                code=400,
            )

        print(f"[FlightPlugin] _serve_episode_data called for run: {run}, episode: {episode_id}")

        try:
            run_path = self.multiplexer.RunPaths().get(run)
            if not run_path:
                raise NotFound(f"Run not found: {run}")

            # Search for the episode in all event files
            event_files = glob_module.glob(os.path.join(run_path, "events.out.tfevents.*"))
            print(f"[FlightPlugin] Searching {len(event_files)} event files")

            for event_file in event_files:
                loader = EventFileLoader(event_file)
                for event in loader.Load():
                    if hasattr(event, 'summary') and event.summary.value:
                        for value in event.summary.value:
                            if hasattr(value, 'metadata') and hasattr(value.metadata, 'plugin_data'):
                                if value.metadata.plugin_data.plugin_name == self.plugin_name:
                                    try:
                                        content = value.metadata.plugin_data.content
                                        episode_data = json.loads(content.decode('utf-8'))
                                        if episode_data.get("episode_id") == episode_id:
                                            print(f"[FlightPlugin] Found episode {episode_id}")
                                            return http_util.Respond(
                                                request,
                                                episode_data,
                                                "application/json",
                                            )
                                    except Exception as e:
                                        print(f"[FlightPlugin] Error parsing episode: {e}")
                                        continue

            raise NotFound(f"Episode not found: {episode_id}")

        except KeyError:
            raise NotFound(f"Run not found: {run}")
        except Exception as e:
            print(f"[FlightPlugin] Error in _serve_episode_data: {e}")
            import traceback
            traceback.print_exc()
            return http_util.Respond(
                request,
                {"error": f"Error reading episode data: {str(e)}"},
                "application/json",
                code=500,
            )

    @wrappers.Request.application
    def _serve_export_acmi(self, request):
        """Export episode data as ACMI file for Tacview.

        Args:
            request: Werkzeug request with 'run' and 'episode_id' parameters

        Returns:
            ACMI file download response
        """
        from tensorboard.backend.event_processing.event_file_loader import EventFileLoader

        run = request.args.get("run")
        episode_id = request.args.get("episode_id")

        if not run or not episode_id:
            return http_util.Respond(
                request,
                {"error": "Missing 'run' or 'episode_id' parameter"},
                "application/json",
                code=400,
            )

        print(f"[FlightPlugin] _serve_export_acmi called for run: {run}, episode: {episode_id}")

        try:
            run_path = self.multiplexer.RunPaths().get(run)
            if not run_path:
                raise NotFound(f"Run not found: {run}")

            # Search for the episode in all event files
            event_files = glob_module.glob(os.path.join(run_path, "events.out.tfevents.*"))

            for event_file in event_files:
                loader = EventFileLoader(event_file)
                for event in loader.Load():
                    if hasattr(event, 'summary') and event.summary.value:
                        for value in event.summary.value:
                            if hasattr(value, 'metadata') and hasattr(value.metadata, 'plugin_data'):
                                if value.metadata.plugin_data.plugin_name == self.plugin_name:
                                    try:
                                        content = value.metadata.plugin_data.content
                                        episode_data = json.loads(content.decode('utf-8'))
                                        if episode_data.get("episode_id") == episode_id:
                                            # Convert JSON to FlightEpisode object
                                            episode = self._json_to_episode(episode_data)

                                            # Generate ACMI content
                                            acmi_content = self._generate_acmi_content(episode)

                                            # Return as downloadable file
                                            filename = f"{episode_id}.txt.acmi"
                                            response = wrappers.Response(
                                                acmi_content,
                                                mimetype="text/plain",
                                                headers={
                                                    "Content-Disposition": f'attachment; filename="{filename}"',
                                                    "Content-Type": "text/plain; charset=utf-8",
                                                }
                                            )
                                            return response
                                    except Exception as e:
                                        print(f"[FlightPlugin] Error converting episode: {e}")
                                        import traceback
                                        traceback.print_exc()
                                        continue

            raise NotFound(f"Episode not found: {episode_id}")

        except KeyError:
            raise NotFound(f"Run not found: {run}")
        except Exception as e:
            print(f"[FlightPlugin] Error in _serve_export_acmi: {e}")
            import traceback
            traceback.print_exc()
            return http_util.Respond(
                request,
                {"error": f"Error exporting ACMI: {str(e)}"},
                "application/json",
                code=500,
            )

    def _json_to_episode(self, data: dict) -> FlightEpisode:
        """Convert JSON episode data to FlightEpisode object.

        Args:
            data: Episode data dictionary from TensorBoard event

        Returns:
            FlightEpisode object
        """
        # Convert trajectory points
        trajectory = []
        for point_data in data.get("trajectory", []):
            orientation = Orientation(
                roll=point_data["orientation"]["roll"],
                pitch=point_data["orientation"]["pitch"],
                yaw=point_data["orientation"]["yaw"],
            )

            telemetry = Telemetry(
                airspeed=point_data["telemetry"].get("airspeed", 0.0),
                altitude=point_data["telemetry"].get("altitude", 0.0),
                g_force=point_data["telemetry"].get("g_force", 1.0),
                throttle=point_data["telemetry"].get("throttle", 0.0),
                aoa=point_data["telemetry"].get("aoa", 0.0),
                aos=point_data["telemetry"].get("aos", 0.0),
                heading=point_data["telemetry"].get("heading", 0.0),
                vertical_speed=point_data["telemetry"].get("vertical_speed", 0.0),
                turn_rate=point_data["telemetry"].get("turn_rate", 0.0),
                bank_angle=point_data["telemetry"].get("bank_angle", 0.0),
                aileron=point_data["telemetry"].get("aileron"),
                elevator=point_data["telemetry"].get("elevator"),
                rudder=point_data["telemetry"].get("rudder"),
            )

            rl_metrics = RLMetrics(
                reward=point_data["rl_metrics"].get("reward", 0.0),
                cumulative_reward=point_data["rl_metrics"].get("cumulative_reward", 0.0),
                action=point_data["rl_metrics"].get("action", [0.0, 0.0, 0.0, 0.5]),
                policy_logprob=point_data["rl_metrics"].get("policy_logprob"),
                value_estimate=point_data["rl_metrics"].get("value_estimate"),
                advantage=point_data["rl_metrics"].get("advantage"),
                entropy=point_data["rl_metrics"].get("entropy"),
                reward_components=point_data["rl_metrics"].get("reward_components"),
            )

            point = FlightDataPoint(
                timestamp=point_data["timestamp"],
                step=point_data["step"],
                position=np.array(point_data["position"]),
                orientation=orientation,
                velocity=np.array(point_data["velocity"]),
                angular_velocity=np.array(point_data.get("angular_velocity", [0.0, 0.0, 0.0])),
                telemetry=telemetry,
                rl_metrics=rl_metrics,
            )
            trajectory.append(point)

        # Create episode
        episode = FlightEpisode(
            episode_id=data["episode_id"],
            agent_id=data["agent_id"],
            episode_number=data["episode_number"],
            start_time=data.get("start_time", 0.0),
            duration=data.get("duration", 0.0),
            total_steps=data["total_steps"],
            total_reward=data["total_reward"],
            success=data.get("success", False),
            termination_reason=data.get("termination_reason", "unknown"),
            trajectory=trajectory,
            config=data.get("config"),
            tags=data.get("tags"),
        )

        return episode

    def _generate_acmi_content(self, episode: FlightEpisode) -> str:
        """Generate ACMI file content from FlightEpisode.

        Args:
            episode: FlightEpisode object

        Returns:
            ACMI file content as string
        """
        # Write to string buffer
        output = io.StringIO()

        writer = ACMIWriter(reference_point=(34.9054, -117.8839, 700.0))  # Edwards AFB default

        # Manually write to string buffer instead of file
        writer._write_header(output, episode)
        writer._write_trajectory(output, episode)
        writer._write_footer(output, episode)

        return output.getvalue()

    @wrappers.Request.application
    def _serve_tags(self, request):
        """Serve available tags for a run.

        Args:
            request: Werkzeug request with 'run' parameter

        Returns:
            JSON response with tags
        """
        run = request.args.get("run")
        if not run:
            return http_util.Respond(
                request,
                {"error": "Missing 'run' parameter"},
                "application/json",
                code=400,
            )

        run_data = self.multiplexer.PluginRunToTagToContent(run)
        tags = list(run_data.get(self.plugin_name, {}).keys())

        return http_util.Respond(
            request,
            {"tags": tags},
            "application/json",
        )

    @wrappers.Request.application
    def _serve_index(self, request):
        """Serve the main index.html file.

        Args:
            request: Werkzeug request

        Returns:
            HTML response
        """
        static_dir = Path(__file__).parent / "static"
        index_path = static_dir / "index.html"

        if not index_path.exists():
            raise NotFound("index.html not found")

        with open(index_path, "rb") as f:
            content = f.read()

        return http_util.Respond(
            request,
            content,
            "text/html",
        )

    @wrappers.Request.application
    def _serve_static_file(self, request):
        """Serve static files (JavaScript bundle, etc.).

        Args:
            request: Werkzeug request

        Returns:
            File response
        """
        # Get the path relative to /static/
        path = request.path
        if "/static/" in path:
            filename = path.split("/static/", 1)[1]
        else:
            raise NotFound()

        # Get the static directory
        static_dir = Path(__file__).parent / "static"
        filepath = static_dir / filename

        # Security: ensure the path is within static_dir
        try:
            filepath = filepath.resolve()
            static_dir = static_dir.resolve()
            if not str(filepath).startswith(str(static_dir)):
                raise NotFound()
        except Exception:
            raise NotFound()

        if not filepath.exists():
            raise NotFound()

        # Determine content type
        content_type = "application/octet-stream"
        if filename.endswith(".js"):
            content_type = "application/javascript"
        elif filename.endswith(".css"):
            content_type = "text/css"
        elif filename.endswith(".html"):
            content_type = "text/html"
        elif filename.endswith(".glb"):
            content_type = "model/gltf-binary"
        elif filename.endswith(".gltf"):
            content_type = "model/gltf+json"
        elif filename.endswith(".obj"):
            content_type = "text/plain"
        elif filename.endswith(".mtl"):
            content_type = "text/plain"

        # Read and serve file
        with open(filepath, "rb") as f:
            content = f.read()

        return http_util.Respond(
            request,
            content,
            content_type,
        )
