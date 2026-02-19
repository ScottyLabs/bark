"""Workspace tools for local file manipulation, executing commands, and scaffolding."""

import asyncio
import logging
import os
import shutil
from pathlib import Path

from bark.core.tools import tool

logger = logging.getLogger(__name__)

# Sandbox workspace to the current directory
_BASE_DIR = Path(os.getcwd()).resolve()


def _safe_path(path_str: str) -> Path:
    target = (_BASE_DIR / path_str).resolve()
    # Simple check to ensure we aren't escaping the base dir
    if not str(target).startswith(str(_BASE_DIR)):
        raise ValueError("Path escapes the workspace directory")
    return target


@tool(
    name="run_terminal_command",
    description="Execute a terminal command locally. Use this for building, testing, or running scripts. Note that long-running commands (like servers) will block until they timeout (300s).",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The command to run"},
            "working_dir": {"type": "string", "description": "Optional working directory"},
        },
        "required": ["command"]
    }
)
async def run_terminal_command(command: str, working_dir: str = "") -> str:
    cwd = _safe_path(working_dir) if working_dir else _BASE_DIR
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
        except asyncio.TimeoutError:
            proc.kill()
            return f"❌ Command timed out after 300s:\n{command}"
            
        output = stdout.decode("utf-8", errors="replace") if stdout else ""
        if proc.returncode != 0:
            return f"❌ Command failed with exit code {proc.returncode}:\n{output}"
        return output or "✅ Command executed successfully (no output)."
    except Exception as e:
        return f"❌ Error executing command: {e}"


@tool(
    name="edit_local_file",
    description="Create or overwrite a file locally in the workspace.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative file path"},
            "content": {"type": "string", "description": "File content"}
        },
        "required": ["path", "content"]
    }
)
async def edit_local_file(path: str, content: str) -> str:
    try:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"✅ Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"❌ Error: {e}"


@tool(
    name="read_local_file",
    description="Read a local file's content from the workspace.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative file path"}
        },
        "required": ["path"]
    }
)
async def read_local_file(path: str) -> str:
    try:
        p = _safe_path(path)
        if not p.exists():
            return f"❌ File not found: {path}"
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"❌ Error: {e}"


@tool(
    name="scaffold_project",
    description="Scaffold a new project using the scottystack template.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Directory name for the new project"}
        },
        "required": ["name"]
    }
)
async def scaffold_project(name: str) -> str:
    try:
        target_dir = _safe_path(name)
        if target_dir.exists():
            return f"❌ Directory {name} already exists."
        
        # Clone scottystack
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "https://github.com/scottylabs/scottystack", str(target_dir),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return f"❌ Failed to clone template: {stderr.decode()}"
        
        # Remove inner .git so we can initialize a new one later
        git_dir = target_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
            
        return f"✅ Successfully scaffolded project '{name}' using scottystack template."
    except Exception as e:
        return f"❌ Error scaffolding project: {e}"
