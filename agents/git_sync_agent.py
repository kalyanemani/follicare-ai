import os
import time
import subprocess
from typing import Dict, Any, Optional
from data.database import get_database

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REACT_APP_DIR = os.path.join(BASE_DIR, "react_app")

class GitReactSyncAgent:
    """
    Automated Git & React Sync Agent:
    Compiles dynamic UI state, stages the complete React 18 codebase under a dedicated
    git branch, commits changes, and pushes to remote Git repositories (e.g. https://github.com/kalyanemani/...).
    """
    DEFAULT_REMOTE_URL = "https://github.com/kalyanemani/follicare-ai.git"

    def __init__(self, default_branch: str = "react-ui-sync", default_remote_url: str = "https://github.com/kalyanemani/follicare-ai.git"):
        self.default_branch = default_branch
        self.default_remote_url = default_remote_url
        self.db = get_database()

    def run_git_cmd(self, args: list, cwd: str = BASE_DIR) -> Dict[str, Any]:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "returncode": res.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    def sync_and_push(
        self,
        branch_name: Optional[str] = None,
        commit_message: Optional[str] = None,
        remote_name: str = "origin",
        remote_url: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.sync_and_push_react_code(
            branch=branch_name,
            commit_message=commit_message,
            remote_name=remote_name,
            remote_url=remote_url or self.default_remote_url
        )

    def sync_and_push_react_code(
        self,
        branch: Optional[str] = None,
        commit_message: Optional[str] = None,
        remote_name: str = "origin",
        remote_url: Optional[str] = None
    ) -> Dict[str, Any]:

        start_time = time.time()
        target_branch = branch or self.default_branch
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        msg = commit_message or f"✨ React UI Auto-Sync: Updated complete React 18 codebase & dynamic tokens ({ts})"

        steps_log = []

        # 1. Ensure remote is configured if custom remote_url provided
        if remote_url:
            self.run_git_cmd(["remote", "set-url", remote_name, remote_url])
            steps_log.append(f"Configured remote '{remote_name}' to {remote_url}")

        # 2. Check current branch or switch to target branch
        cur_branch_res = self.run_git_cmd(["branch", "--show-current"])
        current_branch = cur_branch_res.get("stdout", "main")
        steps_log.append(f"Current active branch: {current_branch}")

        # 3. Create or checkout target sync branch
        branch_checkout = self.run_git_cmd(["checkout", "-B", target_branch])
        if branch_checkout["success"]:
            steps_log.append(f"Switched to sync branch '{target_branch}'")
        else:
            steps_log.append(f"Checkout warning: {branch_checkout['stderr']}")

        # 4. Stage React app files & UI artifacts
        stage_res = self.run_git_cmd(["add", "react_app/", "react_widget/", "static/", "agents/ui_agent.py", "mcp_server.py"])
        steps_log.append("Staged React application codebase (react_app/) & UI components")

        # 5. Commit
        commit_res = self.run_git_cmd(["commit", "-m", msg])
        committed = commit_res["success"] or "nothing to commit" in commit_res.get("stdout", "").lower()
        steps_log.append(f"Git commit status: {'Success' if committed else commit_res.get('stderr')}")

        # 6. Attempt push to remote
        push_success = False
        push_msg = ""
        push_res = self.run_git_cmd(["push", "-u", remote_name, target_branch])
        if push_res["success"]:
            push_success = True
            push_msg = f"Successfully pushed branch '{target_branch}' to {remote_name}."
            steps_log.append(push_msg)
        else:
            push_msg = f"Branch committed locally. Remote push info: {push_res['stderr'] or push_res['stdout']}"
            steps_log.append(push_msg)

        # 7. Switch back to previous branch if different
        if current_branch and current_branch != target_branch:
            self.run_git_cmd(["checkout", current_branch])
            steps_log.append(f"Returned to working branch '{current_branch}'")

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Log tool execution to SQLite
        self.db.log_tool_call({
            "session_id": "mcp_git_sync",
            "trace_id": f"git_{int(time.time()*1000)}",
            "tool_name": "git_push_react_code",
            "tool_type": "mcp",
            "arguments": {
                "branch": target_branch,
                "commit_message": msg,
                "remote": remote_name
            },
            "execution_status": "SUCCESS" if committed else "FAILURE",
            "latency_ms": duration_ms,
            "accuracy_score": 1.0,
            "path_detected": "MCP -> git_push_react_code -> Local/Remote Git",
            "loop_count": 0,
            "error_message": None if committed else commit_res.get("stderr")
        })

        return {
            "status": "success" if committed else "warning",
            "action": "GIT_PUSH_REACT_CODE",
            "branch": target_branch,
            "commit_message": msg,
            "committed": committed,
            "pushed_to_remote": push_success,
            "details": push_msg,
            "execution_steps": steps_log,
            "duration_ms": duration_ms
        }

_git_agent_instance = None

def get_git_react_sync_agent() -> GitReactSyncAgent:
    global _git_agent_instance
    if _git_agent_instance is None:
        _git_agent_instance = GitReactSyncAgent()
    return _git_agent_instance

def get_git_sync_agent() -> GitReactSyncAgent:
    return get_git_react_sync_agent()
