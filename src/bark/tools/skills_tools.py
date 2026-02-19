"""Tools for reading and writing agent skills to S3 (or Minio)."""

import logging
from typing import Any

from bark.core.config import get_settings
from bark.core.tools import tool

logger = logging.getLogger(__name__)


def _get_s3_client() -> Any:
    try:
        import boto3
    except ImportError as exc:
        raise ImportError(
            "boto3 is required for S3 skills. Install it with: uv pip install boto3"
        ) from exc
    settings = get_settings()
    
    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        raise ValueError("S3 credentials not configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        
    return boto3.client(
        "s3",
        endpoint_url=settings.aws_endpoint_url_s3,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


@tool(
    name="list_s3_skills",
    description="List all available skills (runbooks) stored in the S3 bucket.",
)
async def list_s3_skills() -> str:
    """List objects in the S3 skills bucket."""
    settings = get_settings()
    try:
        s3 = _get_s3_client()
        bucket = settings.s3_skills_bucket
        
        # Ensure bucket exists (for local minio)
        try:
            s3.create_bucket(Bucket=bucket)
        except Exception:
            pass
            
        response = s3.list_objects_v2(Bucket=bucket)
        if "Contents" not in response:
            return "No skills found in the S3 bucket."
            
        skills = [obj["Key"] for obj in response["Contents"]]
        return "Available S3 Skills:\n" + "\n".join(f"- {s}" for s in skills)
    except Exception as e:
        logger.error(f"S3 Error: {e}")
        return f"❌ Failed to list skills: {e}"


@tool(
    name="read_s3_skill",
    description="Read the contents of a specific skill file from the S3 bucket.",
    parameters={
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "Name of the skill file (e.g., 'deploy_frontend.md')",
            }
        },
        "required": ["skill_name"],
    }
)
async def read_s3_skill(skill_name: str) -> str:
    """Read a skill from S3."""
    settings = get_settings()
    try:
        s3 = _get_s3_client()
        bucket = settings.s3_skills_bucket
        
        if not skill_name.endswith(".md"):
            skill_name += ".md"
            
        response = s3.get_object(Bucket=bucket, Key=skill_name)
        content = response["Body"].read().decode("utf-8")
        return f"--- Content of {skill_name} ---\n\n{content}"
    except Exception as e:
        return f"❌ Failed to read skill '{skill_name}': {e}"


@tool(
    name="write_s3_skill",
    description="Create or update a skill file in the S3 bucket.",
    parameters={
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "Name of the skill file (e.g., 'deploy_frontend.md')",
            },
            "content": {
                "type": "string",
                "description": "The markdown content of the skill.",
            }
        },
        "required": ["skill_name", "content"],
    }
)
async def write_s3_skill(skill_name: str, content: str) -> str:
    """Write a skill to S3."""
    settings = get_settings()
    try:
        s3 = _get_s3_client()
        bucket = settings.s3_skills_bucket
        
        if not skill_name.endswith(".md"):
            skill_name += ".md"
            
        # Ensure bucket exists
        try:
            s3.create_bucket(Bucket=bucket)
        except Exception:
            pass
            
        s3.put_object(
            Bucket=bucket,
            Key=skill_name,
            Body=content.encode("utf-8"),
            ContentType="text/markdown"
        )
        return f"✅ Successfully wrote skill to S3: {skill_name}"
    except Exception as e:
        return f"❌ Failed to write skill: {e}"
