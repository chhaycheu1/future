# Ubuntu VM & CI/CD Setup Guide

I have prepared the necessary configuration files in the `deploy/` and `.github/` directories. Follow these steps to complete the setup.

## 1. Prepare your New Ubuntu VM

1.  **SSH into your VM** as `root` (or the default user provided by your cloud provider).
    ```bash
    ssh root@<YOUR_VM_IP>
    ```

2.  **Create the Setup Script**:
    Copy the content of `deploy/setup_vm.sh` from this project into a file on your server (or upload it).
    ```bash
    nano setup_vm.sh
    # Paste content...
    chmod +x setup_vm.sh
    ./setup_vm.sh
    ```
    *This script will update your system, install Python/Nginx, and create a user named `deployer`.*

## 2. Configure SSH Access for Deployment

1.  **Switch to the new user**:
    ```bash
    su - deployer
    ```

2.  **Generate an SSH Keypair** (for GitHub Actions to log in):
    ```bash
    ssh-keygen -t ed25519 -C "github-actions"
    # Press Enter for all prompts (no passphrase)
    ```

3.  **Authorize the Key**:
    Add the public key to `authorized_keys` to allow self-login (for testing) or just use it for GitHub.
    ```bash
    cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    ```

4.  **Copy the Private Key**:
    You will need the content of the private key for GitHub Secrets.
    ```bash
    cat ~/.ssh/id_ed25519
    ```
    *Copy this entire block (including BEGIN and END lines).*

## 3. GitHub Configuration

1.  **Deploy Keys (for pulling code)**:
    -   Run `cat ~/.ssh/id_ed25519.pub` on the VM.
    -   Go to your GitHub Repo -> **Settings** -> **Deploy keys**.
    -   Add a new key, Title: "Production VM", Key: [Paste Public Key].
    -   **Important**: Check "Allow write access" if you want to push from the server, but for pulling, read-only is fine (though the script does `git pull`).

2.  **Secrets (for connecting to VM)**:
    -   Go to **Settings** -> **Secrets and variables** -> **Actions**.
    -   Add the following Repository Secrets:
        -   `HOST`: Your VM's IP address.
        -   `USERNAME`: `deployer`
        -   `KEY`: [The Private Key you copied in Step 2.4]

## 4. Final Deployment Steps

1.  **Push your code** to the `main` branch on GitHub.
    -   This will trigger the `.github/workflows/deploy.yml` action.
    -   Check the **Actions** tab in GitHub to see the progress.

2.  **Verify**:
    -   After the action turns green, verify your bot is running:
        ```bash
        systemctl status tradingbot
        ```
    -   Access your web interface at `http://<YOUR_VM_IP>`.

## Troubleshooting
-   If the **GitHub Action fails** on SSH: Check that the `KEY` secret is correct and corresponds to the public key in `/home/deployer/.ssh/authorized_keys`.
-   If `git clone` fails: Ensure you added the *Deploy Key* to the GitHub repo.
