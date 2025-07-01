import asyncio
import re
import tempfile
import shutil
import os
import stat
from urllib.parse import urlparse

def get_repo_name(git_url):
    pattern = re.compile(r"^((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?$")
    if not pattern.match(git_url):
        return None
    return os.path.splitext(os.path.basename(urlparse(git_url).path))[0]

async def run_command(cmd, cwd=None):
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()
    except Exception as e:
        return 1, '', str(e)

def handle_remove_readonly(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)

async def handle_repo(git_url):
    repo_name = get_repo_name(git_url)
    temp_dir = tempfile.mkdtemp(prefix="dockerbuild_", dir=os.getcwd())

    result = {"type": "handle", "repo": repo_name, "success": True, "error": {}}

    # Clone
    code, _, err = await run_command(["git", "clone", git_url, temp_dir])
    if code != 0:
        result["success"] = False
        result["error"] = {"stage": "clone", "code": code, "mess": err}
        shutil.rmtree(temp_dir, ignore_errors=False, onerror=handle_remove_readonly)
        return result

    # Build
    code, out, err = await run_command(["docker", "build", "-t", repo_name, "."], cwd=temp_dir)
    if code != 0:
        result["success"] = False
        result["error"] = {"stage": "build", "code": code, "mess": err}

    shutil.rmtree(temp_dir, ignore_errors=False, onerror=handle_remove_readonly)
    return result
