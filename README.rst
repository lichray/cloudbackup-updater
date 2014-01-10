Cloud Backup Agent auto-updater operates in 2 modes:

  1. Daemon mode (with the -d commend line option);
  2. One-shot update (without -d).

In each mode, the auto-updater can add the agent repository
if it's not there, install the agent if not installed, and
update the agent if a new version is released.
