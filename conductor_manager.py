import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class ConductorManager:
    """
    Manages Conductor extension integration for Coderagy.
    Provides Spec-Driven Development (SDD) capabilities:
    - Status reporting from tracks and plans
    - Project context extraction for AI agents
    - Track creation and management
    - Project scaffolding/setup
    """

    def __init__(self, project_dir: str = "."):
        self.project_dir = os.path.abspath(project_dir)
        self.conductor_dir = os.path.join(self.project_dir, "conductor")
        self.index_file = os.path.join(self.conductor_dir, "index.md")
        self.tracks_file = os.path.join(self.conductor_dir, "tracks.md")
        self.product_file = os.path.join(self.conductor_dir, "product.md")
        self.tech_stack_file = os.path.join(self.conductor_dir, "tech-stack.md")
        self.workflow_file = os.path.join(self.conductor_dir, "workflow.md")
        self.tracks_dir = os.path.join(self.conductor_dir, "tracks")

    def is_initialized(self) -> bool:
        """Checks whether the Conductor environment is initialized."""
        return os.path.exists(self.conductor_dir) and os.path.exists(self.index_file)

    def list_tracks(self) -> List[Dict[str, Any]]:
        """Parses conductor/tracks.md and returns all registered tracks."""
        if not os.path.exists(self.tracks_file):
            return []

        tracks = []
        with open(self.tracks_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Match either new format '- [ ] **Track: Name**' or legacy format '## [ ] Track: Name'
        track_pattern = re.compile(
            r"^(?:-\s*\[([ x~])\]\s*\*\*Track:\s*([^*]+)\*\*|##\s*\[([ x~])\]\s*Track:\s*(.+))$",
            re.MULTILINE
        )
        link_pattern = re.compile(r"\*Link:\s*\[([^\]]+)\]\(([^)]+)\)\*")

        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            match = track_pattern.match(line)
            if match:
                status_char = match.group(1) or match.group(3)
                name = (match.group(2) or match.group(4)).strip()
                
                status_map = {"x": "completed", "~": "in_progress", " ": "pending"}
                status = status_map.get(status_char, "pending")

                # Look for link in subsequent lines
                link_path = None
                j = i + 1
                while j < len(lines) and j <= i + 3:
                    subline = lines[j].strip()
                    link_match = link_pattern.search(subline)
                    if link_match:
                        link_path = link_match.group(2).strip()
                        break
                    if subline.startswith("- [") or subline.startswith("## ["):
                        break
                    j += 1

                # Derive track_id from link_path or track name
                track_id = ""
                if link_path:
                    # Clean up link path (e.g. ./tracks/desktop_commander_20260906/ -> desktop_commander_20260906)
                    parts = [p for p in link_path.strip("/.").split("/") if p and p != "tracks"]
                    if parts:
                        track_id = parts[-1]
                if not track_id:
                    track_id = re.sub(r"[^a-zA-Z0-9_]+", "_", name.lower()).strip("_")

                tracks.append({
                    "id": track_id,
                    "name": name,
                    "status": status,
                    "status_char": status_char,
                    "link": link_path
                })
            i += 1

        return tracks

    def parse_track_plan(self, track_id: str, link: Optional[str] = None) -> Dict[str, Any]:
        """Reads and parses a track's plan.md file."""
        plan_path = None
        if link:
            # Resolve link relative to conductor directory
            rel_link = link.strip().lstrip("./")
            possible_path = os.path.join(self.conductor_dir, rel_link, "plan.md")
            if os.path.exists(possible_path):
                plan_path = possible_path
            else:
                possible_path = os.path.join(self.conductor_dir, rel_link)
                if os.path.exists(possible_path) and os.path.isfile(possible_path):
                    plan_path = possible_path

        if not plan_path or not os.path.exists(plan_path):
            plan_path = os.path.join(self.tracks_dir, track_id, "plan.md")

        if not os.path.exists(plan_path):
            return {
                "phases": [],
                "tasks": [],
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "pending_tasks": 0,
                "progress_percent": 0.0,
                "plan_exists": False
            }

        with open(plan_path, "r", encoding="utf-8") as f:
            content = f.read()

        phases = []
        tasks = []
        current_phase = None

        for line in content.splitlines():
            line_str = line.strip()
            # Phase header
            if line_str.startswith("## Phase") or line_str.startswith("## "):
                phase_title = line_str.lstrip("#").strip()
                current_phase = {"title": phase_title, "tasks": []}
                phases.append(current_phase)
            # Checkbox task
            task_match = re.match(r"^-\s*\[([ x~])\]\s*(?:Task:\s*)?(.+)$", line_str)
            if task_match:
                status_char = task_match.group(1)
                desc = task_match.group(2).strip()
                status_map = {"x": "completed", "~": "in_progress", " ": "pending"}
                task_item = {
                    "description": desc,
                    "status": status_map.get(status_char, "pending"),
                    "status_char": status_char,
                    "phase": current_phase["title"] if current_phase else "General"
                }
                tasks.append(task_item)
                if current_phase:
                    current_phase["tasks"].append(task_item)

        completed = sum(1 for t in tasks if t["status"] == "completed")
        in_progress = sum(1 for t in tasks if t["status"] == "in_progress")
        pending = sum(1 for t in tasks if t["status"] == "pending")
        total = len(tasks)
        pct = round((completed / total * 100), 1) if total > 0 else 0.0

        return {
            "phases": phases,
            "tasks": tasks,
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "pending_tasks": pending,
            "progress_percent": pct,
            "plan_exists": True
        }

    def get_status(self) -> Dict[str, Any]:
        """Provides a comprehensive status overview according to Conductor standards."""
        if not self.is_initialized():
            return {
                "initialized": False,
                "message": "Conductor is not initialized properly. I cannot find conductor/index.md.",
                "tracks": [],
                "total_tracks": 0,
                "completed_tracks": 0,
                "in_progress_tracks": 0,
                "pending_tracks": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "pending_tasks": 0,
                "progress_percent": 0.0,
                "project_status": "Uninitialized"
            }

        tracks_summary = []
        total_tasks = 0
        completed_tasks = 0
        in_progress_tasks = 0
        pending_tasks = 0
        total_phases = 0

        raw_tracks = self.list_tracks()
        active_track = None
        current_phase_desc = None
        current_task_desc = None
        next_action_desc = None

        for t in raw_tracks:
            plan_data = self.parse_track_plan(t["id"], t["link"])
            track_info = {
                **t,
                "plan": plan_data
            }
            tracks_summary.append(track_info)

            total_tasks += plan_data["total_tasks"]
            completed_tasks += plan_data["completed_tasks"]
            in_progress_tasks += plan_data["in_progress_tasks"]
            pending_tasks += plan_data["pending_tasks"]
            total_phases += len(plan_data["phases"])

            # Determine active track (first in_progress, or first pending if none in_progress)
            if not active_track and t["status"] == "in_progress":
                active_track = track_info
            elif not active_track and t["status"] == "pending":
                # Candidate if no track is explicitly in progress
                candidate_track = track_info

        if not active_track and raw_tracks:
            # Check for any pending track
            for t_info in tracks_summary:
                if t_info["status"] == "pending":
                    active_track = t_info
                    break

        if active_track and active_track.get("plan"):
            plan_tasks = active_track["plan"]["tasks"]
            # Find in-progress task
            for pt in plan_tasks:
                if pt["status"] == "in_progress" and not current_task_desc:
                    current_task_desc = pt["description"]
                    current_phase_desc = pt["phase"]
                elif pt["status"] == "pending" and not next_action_desc:
                    next_action_desc = pt["description"]
            # If no in-progress task found, current is the first pending
            if not current_task_desc and next_action_desc:
                current_task_desc = next_action_desc
                for pt in plan_tasks:
                    if pt["description"] == current_task_desc:
                        current_phase_desc = pt["phase"]
                        break

        total_tracks_count = len(raw_tracks)
        completed_tracks_count = sum(1 for t in raw_tracks if t["status"] == "completed")
        in_progress_tracks_count = sum(1 for t in raw_tracks if t["status"] == "in_progress")
        pending_tracks_count = sum(1 for t in raw_tracks if t["status"] == "pending")

        overall_pct = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else (
            100.0 if total_tracks_count > 0 and completed_tracks_count == total_tracks_count else 0.0
        )

        project_status = "Active"
        if in_progress_tracks_count > 0 or in_progress_tasks > 0:
            project_status = "In Progress"
        elif total_tracks_count > 0 and completed_tracks_count == total_tracks_count:
            project_status = "Completed"
        elif total_tracks_count == 0:
            project_status = "Ready for initial track"

        return {
            "initialized": True,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project_status": project_status,
            "active_track": active_track,
            "current_phase": current_phase_desc or "N/A",
            "current_task": current_task_desc or "N/A",
            "next_action": next_action_desc or "No pending tasks",
            "total_tracks": total_tracks_count,
            "completed_tracks": completed_tracks_count,
            "in_progress_tracks": in_progress_tracks_count,
            "pending_tracks": pending_tracks_count,
            "total_phases": total_phases,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "pending_tasks": pending_tasks,
            "progress_percent": overall_pct,
            "tracks": tracks_summary
        }

    def format_status_report(self) -> str:
        """Generates a human-readable Conductor status summary report."""
        status = self.get_status()
        if not status["initialized"]:
            return (
                "[!] Conductor is not initialized properly.\n"
                "I cannot find the `conductor/index.md` file.\n"
                "Run `conductor setup` to initialize the project."
            )

        report = []
        report.append("==================================================")
        report.append(f"  CONDUCTOR STATUS OVERVIEW")
        report.append(f"  Date: {status['current_time']}")
        report.append(f"  Status: {status['project_status']}")
        report.append(f"  Overall Progress: {status['completed_tasks']}/{status['total_tasks']} tasks ({status['progress_percent']}%)")
        report.append("==================================================")

        if status["active_track"]:
            at = status["active_track"]
            report.append(f"\n[Active Track]")
            report.append(f"  Name: {at['name']}")
            report.append(f"  Status: {at['status'].upper()}")
            report.append(f"  Current Phase: {status['current_phase']}")
            report.append(f"  Current Task:  {status['current_task']}")
            report.append(f"  Next Action:   {status['next_action']}")

        report.append("\n[Registered Tracks]")
        for t in status["tracks"]:
            badge = "[x]" if t["status"] == "completed" else ("[~]" if t["status"] == "in_progress" else "[ ]")
            plan = t["plan"]
            task_summary = f"{plan['completed_tasks']}/{plan['total_tasks']} tasks ({plan['progress_percent']}%)" if plan["total_tasks"] > 0 else "no tasks"
            report.append(f"  {badge} {t['name']} ({task_summary})")

        return "\n".join(report)

    def create_track(self, name: str, description: str = "", track_type: str = "feature") -> Dict[str, Any]:
        """Creates a new track directory, spec.md, plan.md, and registers it in tracks.md."""
        if not self.is_initialized():
            self.setup()

        date_str = datetime.now().strftime("%Y%m%d")
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")
        track_id = f"{slug}_{date_str}"
        track_path = os.path.join(self.tracks_dir, track_id)
        os.makedirs(track_path, exist_ok=True)

        # 1. index.md
        with open(os.path.join(track_path, "index.md"), "w", encoding="utf-8") as f:
            f.write(f"# Track: {name}\n\n## Overview\n{description or name}\n")

        # 2. metadata.json
        metadata = {
            "name": name,
            "type": track_type,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "planned"
        }
        with open(os.path.join(track_path, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # 3. spec.md
        with open(os.path.join(track_path, "spec.md"), "w", encoding="utf-8") as f:
            f.write(f"# Specification: {name}\n\n## Goal\n{description or name}\n\n## Acceptance Criteria\n- [ ] Initial criteria defined\n")

        # 4. plan.md
        plan_content = f"""# Implementation Plan: {name}

## Phase 1: Planning and Research
- [ ] Task: Clarify requirements and define technical design
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Implementation
- [ ] Task: Implement core functionality for {name}
- [ ] Task: Add tests and verify functionality
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)
"""
        with open(os.path.join(track_path, "plan.md"), "w", encoding="utf-8") as f:
            f.write(plan_content)

        # 5. Append to tracks.md
        rel_link = f"./tracks/{track_id}/"
        new_entry = f"\n- [ ] **Track: {name}**\n  *Link: [{rel_link}]({rel_link})*\n"
        with open(self.tracks_file, "a", encoding="utf-8") as f:
            f.write(new_entry)

        return {
            "track_id": track_id,
            "name": name,
            "path": track_path,
            "link": rel_link
        }

    def get_agent_context(self, max_chars: int = 4000) -> str:
        """
        Gathers product definition, tech-stack, workflow, and active track plan
        to provide a context injection block for AI agents.
        """
        if not self.is_initialized():
            return ""

        context_blocks = ["### Conductor Spec-Driven Development Context\n"]

        # 1. Product definition
        if os.path.exists(self.product_file):
            try:
                with open(self.product_file, "r", encoding="utf-8") as f:
                    context_blocks.append("#### Product Definition\n" + f.read()[:1000].strip())
            except Exception:
                pass

        # 2. Tech Stack
        if os.path.exists(self.tech_stack_file):
            try:
                with open(self.tech_stack_file, "r", encoding="utf-8") as f:
                    context_blocks.append("#### Tech Stack Constraints\n" + f.read()[:600].strip())
            except Exception:
                pass

        # 3. Active Track Details
        status = self.get_status()
        if status.get("active_track"):
            at = status["active_track"]
            context_blocks.append(f"#### Active Track: {at['name']} ({at['status']})")
            track_id = at["id"]
            spec_file = os.path.join(self.tracks_dir, track_id, "spec.md")
            plan_file = os.path.join(self.tracks_dir, track_id, "plan.md")
            if os.path.exists(spec_file):
                try:
                    with open(spec_file, "r", encoding="utf-8") as f:
                        context_blocks.append("##### Track Specification\n" + f.read()[:800].strip())
                except Exception:
                    pass
            if os.path.exists(plan_file):
                try:
                    with open(plan_file, "r", encoding="utf-8") as f:
                        context_blocks.append("##### Implementation Plan\n" + f.read()[:1000].strip())
                except Exception:
                    pass

        full_context = "\n\n".join(context_blocks)
        if len(full_context) > max_chars:
            return full_context[:max_chars] + "\n... [context truncated]"
        return full_context

    def setup(self, project_name: str = "Coderagy", description: str = "AI-assisted coding CLI tool", tech_stack: str = "Python, google-genai, MCP") -> bool:
        """Initializes Conductor folder structure and base context files."""
        os.makedirs(self.conductor_dir, exist_ok=True)
        os.makedirs(self.tracks_dir, exist_ok=True)
        os.makedirs(os.path.join(self.conductor_dir, "code_styleguides"), exist_ok=True)

        # index.md
        if not os.path.exists(self.index_file):
            with open(self.index_file, "w", encoding="utf-8") as f:
                f.write(f"# Project Context: {project_name}\n\n## Definition\n- [Product Definition](./product.md)\n- [Product Guidelines](./product-guidelines.md)\n- [Tech Stack](./tech-stack.md)\n\n## Workflow\n- [Workflow](./workflow.md)\n- [Tracks](./tracks.md)\n")

        # product.md
        if not os.path.exists(self.product_file):
            with open(self.product_file, "w", encoding="utf-8") as f:
                f.write(f"# Product Definition: {project_name}\n\n## Summary\n{description}\n")

        # tech-stack.md
        if not os.path.exists(self.tech_stack_file):
            with open(self.tech_stack_file, "w", encoding="utf-8") as f:
                f.write(f"# Tech Stack\n\n- Stack: {tech_stack}\n")

        # workflow.md
        if not os.path.exists(self.workflow_file):
            with open(self.workflow_file, "w", encoding="utf-8") as f:
                f.write("# Workflow Rules\n\n- Spec-Driven Development: Plan before coding.\n- Verification: Validate after each phase.\n")

        # tracks.md
        if not os.path.exists(self.tracks_file):
            with open(self.tracks_file, "w", encoding="utf-8") as f:
                f.write("# Project Tracks\n\nThis file tracks all major tracks for the project.\n\n---\n")

        return True
