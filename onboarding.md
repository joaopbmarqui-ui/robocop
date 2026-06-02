# Enabling the Dispatch Command

Welcome to Dispatch! After completing the installation, you need to ensure the `dispatch` command is available in your terminal so you can launch jobs from any directory containing your SQL files.

The `install.sh` script automatically attempts to set this up for you by creating a shortcut (an alias) or placing the executable in a standard location (`~/.local/bin`).

> [!WARNING]
> When running the installer, make sure to execute it directly (e.g. `/ads_storage/dispatch/install.sh`) rather than using `source`. Sourcing the script can cause issues with directory resolution.

## Step 1: Refresh your terminal

The easiest way to enable the command is to start a new terminal session.

- **Option A:** Disconnect and SSH back into the Edge Node.
- **Option B:** Reload your current shell's configuration by running:
  ```bash
  source ~/.bashrc
  ```
  *(If you use zsh, run `source ~/.zshrc` instead).*

## Step 2: Verify the installation

Navigate to a folder with your SQL files and try running the command:

```bash
cd /path/to/your/sql/files
dispatch
```

If the Dispatch UI opens, you are fully set up!

---

## Troubleshooting

If you see `dispatch: command not found`, the installer might not have been able to update your shell configuration automatically.

### Option 1: Add the alias manually

You can manually add the alias to your profile by running these commands:

```bash
echo "alias dispatch='$HOME/.local/bin/dispatch'" >> ~/.bashrc
source ~/.bashrc
```

### Option 2: Add ~/.local/bin to your PATH

Alternatively, you can ensure that your user's local binary folder is part of your system's `PATH`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

*Note: If you use a shell other than bash (like zsh), replace `.bashrc` with your shell's profile file (e.g., `.zshrc`).*