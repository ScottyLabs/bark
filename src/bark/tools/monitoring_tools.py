"""Monitoring tools for post-deployment verification and debugging."""

import asyncio
import logging
import os
import json

import httpx

from bark.core.tools import tool

logger = logging.getLogger(__name__)


@tool(
    name="check_github_actions",
    description="Check the latest GitHub Actions workflow runs for a repository to verify CI/CD success.",
    parameters={
        "type": "object",
        "properties": {
            "repo_full_name": {
                "type": "string",
                "description": "Full repository name, e.g., 'scottylabs/bark'"
            },
            "limit": {
                "type": "integer",
                "description": "Number of runs to fetch (default 5)"
            }
        },
        "required": ["repo_full_name"]
    }
)
async def check_github_actions(repo_full_name: str, limit: int = 5) -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return "❌ GITHUB_TOKEN environment variable is not set."

    url = f"https://api.github.com/repos/{repo_full_name}/actions/runs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Bark-Bot"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params={"per_page": limit})
        if resp.status_code != 200:
            return f"❌ Failed to fetch actions runs: HTTP {resp.status_code}\n{resp.text}"
            
        data = resp.json()
        runs = data.get("workflow_runs", [])
        if not runs:
            return f"No GitHub Actions runs found for `{repo_full_name}`."
            
        lines = [f"### Latest {len(runs)} GitHub Actions for {repo_full_name}"]
        for r in runs:
            status = r.get("status", "unknown")
            conclusion = r.get("conclusion", "in_progress")
            emoji = "✅" if conclusion == "success" else "❌" if conclusion == "failure" else "🔄"
            lines.append(f"{emoji} **{r.get('name')}** (Branch: `{r.get('head_branch', '')}`) - Status: {status}, Conclusion: {conclusion}")
            lines.append(f"   URL: {r.get('html_url')}")
            
        return "\n".join(lines)


@tool(
    name="read_posthog_events",
    description="Fetch recent events or errors from PostHog. Requires POSTHOG_API_KEY and POSTHOG_PROJECT_ID.",
    parameters={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Number of events to fetch (default 20)"
            }
        }
    }
)
async def read_posthog_events(limit: int = 20) -> str:
    api_key = os.environ.get("POSTHOG_API_KEY", "")
    project_id = os.environ.get("POSTHOG_PROJECT_ID", "")
    
    if not api_key or not project_id:
        return "❌ Missing PostHog configuration. Ensure POSTHOG_API_KEY and POSTHOG_PROJECT_ID are set in the environment."
        
    # Assuming US cloud. Could be eu.posthog.com for EU.
    url = f"https://app.posthog.com/api/projects/{project_id}/events/"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params={"limit": limit})
        if resp.status_code != 200:
            return f"❌ Failed to fetch PostHog events: HTTP {resp.status_code}\n{resp.text}"
            
        data = resp.json()
        events = data.get("results", [])
        if not events:
            return "No recent PostHog events found."
            
        lines = [f"### Latest {len(events)} PostHog Events"]
        for e in events:
            event_name = e.get("event", "unknown")
            timestamp = e.get("timestamp", "")
            person_id = e.get("person", {}).get("distinct_ids", ["unknown"])[0] if e.get("person") else e.get("distinct_id", "unknown")
            lines.append(f"- **{event_name}** at {timestamp} by user `{person_id}`")
            
        return "\n".join(lines)


@tool(
    name="read_railway_logs",
    description="Fetch deployment or service logs from Railway via the Railway CLI. Requires RAILWAY_API_TOKEN.",
    parameters={
        "type": "object",
        "properties": {
            "lines": {
                "type": "integer",
                "description": "Number of log lines to tail (default 100)"
            }
        }
    }
)
async def read_railway_logs(lines: int = 100) -> str:
    token = os.environ.get("RAILWAY_API_TOKEN", "")
    if not token:
        return "❌ RAILWAY_API_TOKEN environment variable is not set."
        
    try:
        # Run railway logs CLI command
        env = os.environ.copy()
        
        proc = await asyncio.create_subprocess_exec(
            "railway", "logs", "-n", str(lines),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env
        )
        
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            return "❌ `railway logs` command timed out."
            
        output = stdout.decode("utf-8", errors="replace")
        
        if proc.returncode != 0:
            if "not found" in output.lower():
                return "❌ The `railway` CLI is not installed or not in PATH. Please install it to use this tool."
            return f"❌ Failed to read Railway logs (exit code {proc.returncode}):\n{output}"
            
        return f"### Railway Logs (last {lines} lines)\n```\n{output}\n```"
        
    except FileNotFoundError:
        return "❌ The `railway` CLI is not installed on this system. Cannot read logs."
    except Exception as e:
        return f"❌ Error reading railway logs: {e}"
