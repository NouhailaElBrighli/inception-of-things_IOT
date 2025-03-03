import subprocess
import sys
import time

from utils import *


def copy_to_clipboard(text):
    """Copy given text to the clipboard using xsel."""
    p = subprocess.Popen("xsel --clipboard --input", stdin=subprocess.PIPE, shell=True)
    p.communicate(input=text.encode())


def refresh_argocd_connection():
    """If launched without extra arguments, kill and restart the Argo-CD connection."""
    if len(sys.argv) < 2:
        kill_portforward("kubectl port-forward svc/argocd-server")
        port_forward("argocd-server", "argocd", 9090, 443)


def get_gitlab_password():
    """Prompt for GitLab password and copy it to clipboard."""
    colpr("g", "======== Connect to GitLab user-interface (UI) ========")
    time.sleep(20)
    res = run(
        'kubectl -n gitlab get secret gitlab-gitlab-initial-root-password -o jsonpath="{.data.password}" | base64 -d',
        capture_output=True,
    )
    GITLAB_PASSWORD = res.stdout.strip()
    colpr("y", f"GITLAB PASSWORD: {GITLAB_PASSWORD} (Pasted to clipboard)")
    copy_to_clipboard(GITLAB_PASSWORD)
    colpr(
        "y",
        "Remember that password. Login here https://localhost:30080 for the GitLab UI",
    )


def get_argocd_password():
    """Prompt for UI redirection, copy credentials to clipboard, and open browser."""
    colpr("g", "======== Connect to Argo CD user-interface (UI) ========")

    res = run(
        'kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d',
        capture_output=True,
    )
    ARGOCD_PASSWORD = res.stdout.strip()
    colpr("y", "ARGO CD USERNAME: admin")
    colpr("y", f"ARGO CD PASSWORD: {ARGOCD_PASSWORD} (Pasted to clipboard)")
    copy_to_clipboard(ARGOCD_PASSWORD)
    colpr(
        "y",
        "Remember those credentials. Login here https://localhost:9090 for the Argo CD UI",
    )


def connect_to_ui():
    """Prompt for UI redirection, copy credentials to clipboard, and open browser."""
    time.sleep(20)
    subprocess.run("xdg-open 'https://localhost:9090'", shell=True)


def main():
    refresh_argocd_connection()
    get_gitlab_password()
    get_argocd_password()
    answer = input("Do you want to be redirected to the argo-cd UI? (y/n): ")
    if answer.lower() == "y":
        connect_to_ui()


if __name__ == "__main__":
    main()
