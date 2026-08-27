# Global User Preferences & Behavioral Rules

## 1. Notification Audio Chimes (macOS Native)
- **At Response Completion:** ALWAYS play the completion chime at the end of every turn/task:
  `afplay /System/Library/Sounds/Glass.aiff`
- **When Asking a Question / Needing User Input:** ALWAYS play the attention chime:
  `afplay /System/Library/Sounds/Ping.aiff`
- **When Starting:** Do NOT play chimes at the start of a response.

## 2. Command Execution & Permissions
- Proactively run standard, routine, and non-destructive bash commands without asking for permission (e.g., installs, file creations, test runs, process checks, git commands).
- Only prompt for confirmation on truly destructive commands (`rm -rf`, `sudo`, `dd`, system disk operations).

## 3. Brand Neutrality
- When generating scripts, user agents, app configurations, or workflow IDs for community/social APIs, never include trademark words (e.g. "reddit") in app names or User-Agents to prevent API heuristic rejections.
