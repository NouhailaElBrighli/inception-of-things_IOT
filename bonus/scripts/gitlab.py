import sys
import time
import os
import json
import subprocess

from utils import run, colpr


def create_gitlab_token():
    """Create a GitLab access token for Argo CD to use"""
    # Get GitLab root password
    res = run(
        'kubectl -n gitlab get secret gitlab-gitlab-initial-root-password -o jsonpath="{.data.password}" | base64 -d',
        capture_output=True,
    )
    GITLAB_PASSWORD = res.stdout.strip()

    # Create Personal Access Token via API
    colpr("y", "Creating GitLab access token for Argo CD...")

    # Wait for GitLab API to be ready
    colpr("y", "Waiting for GitLab API to be ready...")
    time.sleep(30)

    token_name = "argocd-access"
    token_cmd = f"""
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -d '{{"name":"{token_name}","scopes":["api","read_repository","write_repository"]}}' \
      --user "root:{GITLAB_PASSWORD}" \
      --insecure \
      http://gitlab.localhost:8081/api/v4/personal_access_tokens
    """

    token_result = subprocess.run(token_cmd, shell=True, capture_output=True, text=True)

    # Store token in Kubernetes secret
    if token_result.returncode == 0:
        try:
            token_data = json.loads(token_result.stdout)
            if "token" in token_data:
                token = token_data["token"]
                colpr("g", "GitLab access token created successfully")

                # Store in Kubernetes secret for Argo CD to use
                run(
                    f"kubectl create secret generic gitlab-creds -n argocd "
                    f"--from-literal=username=root "
                    f"--from-literal=password={token} "
                    f"--dry-run=client -o yaml | kubectl apply -f -"
                )

                return "root", token
        except json.JSONDecodeError:
            colpr("r", "Failed to parse GitLab API response")

    colpr("r", "Failed to create GitLab token, using root password as fallback")
    # Store root credentials as fallback
    run(
        f"kubectl create secret generic gitlab-creds -n argocd "
        f"--from-literal=username=root "
        f"--from-literal=password={GITLAB_PASSWORD} "
        f"--dry-run=client -o yaml | kubectl apply -f -"
    )

    return "root", GITLAB_PASSWORD


def gitlab():
    pwd = run("pwd", capture_output=True).stdout
    username, GITLAB_PASSWORD = create_gitlab_token()

    # Clone from GitHub and push to GitLab with credentials
    run(
        f"cd /tmp && rm -rf will_IOT && git clone 'https://github.com/NajmiAchraf/will_IOT.git' && "
        f"cd will_IOT && git remote set-url origin 'http://{username}:{GITLAB_PASSWORD}@gitlab.localhost:8081/{username}/will_IOT.git' && "
        f"git push -uf origin master",
        capture_output=False,
    )

    run(f"cd {pwd}", capture_output=False)
    time.sleep(5)


def main():
    answer = input("Do you want to clone the repo from github to gitlab of course if you already created a repos under 'will_IOT' name? (y/n): ")
    if answer.lower() == "y":
        gitlab()


if __name__ == "__main__":
    main()
