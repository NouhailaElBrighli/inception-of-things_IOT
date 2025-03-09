import sys
import time

from utils import *


def refresh_argocd_connection():
    """If launched without extra arguments, kill and restart the Argo-CD connection."""
    if len(sys.argv) < 2:
        kill_portforward("kubectl port-forward svc/argocd-server")
        port_forward("argocd-server", "argocd", 9090, 443)


def login_argocd():
    """Ensure we're logged in to Argo CD with admin privileges."""
    colpr("g", "Logging in to Argo-CD as admin")
    res = run(
        'kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d',
        capture_output=True,
    )
    ARGOCD_PASSWORD = res.stdout.strip()
    login_result = run(
        f"argocd login localhost:9090 --username admin --password {ARGOCD_PASSWORD} --insecure --grpc-web",
        capture_output=False,
    )
    if login_result.returncode != 0:
        colpr("r", "Failed to login to Argo CD. Trying without --grpc-web flag...")
        run(
            f"argocd login localhost:9090 --username admin --password {ARGOCD_PASSWORD} --insecure",
            capture_output=False,
        )

    # Ensure we're in the right namespace
    run("kubectl config set-context --current --namespace=argocd")


def create_or_update_app():
    # First ensure we're logged in
    login_argocd()

    # Create the Argo-CD app, or, if it exists, offer to delete and recreate it.
    colpr("g", "Create Argo-CD app 'will'")

    # Get stored GitLab credentials from Kubernetes secret
    gitlab_user = run(
        'kubectl get secret gitlab-creds -n argocd -o jsonpath="{.data.username}" | base64 -d',
        capture_output=True,
    ).stdout.strip()

    if not gitlab_user:
        colpr(
            "y",
            "No GitLab credentials found. Creating them from GitLab root password...",
        )
        root_pwd = run(
            'kubectl -n gitlab get secret gitlab-gitlab-initial-root-password -o jsonpath="{.data.password}" | base64 -d',
            capture_output=True,
        ).stdout.strip()

        # Create GitLab credentials secret
        run(
            f"kubectl create secret generic gitlab-creds -n argocd "
            f"--from-literal=username=root "
            f"--from-literal=password={root_pwd} "
            f"--dry-run=client -o yaml | kubectl apply -f -"
        )

        gitlab_user = "root"
        gitlab_pass = root_pwd
    else:
        gitlab_pass = run(
            'kubectl get secret gitlab-creds -n argocd -o jsonpath="{.data.password}" | base64 -d',
            capture_output=True,
        ).stdout.strip()

    # Register the repository with credentials
    repo_add = run(
        f"argocd repo add 'http://gitlab-webservice-default.gitlab.svc.cluster.local:8181/root/will_IOT.git' "
        f"--username {gitlab_user} --password {gitlab_pass} --insecure --grpc-web"
    )

    # Create the app (credentials are now stored in repo config)
    app_create = run(
        "argocd app create will "
        "--repo 'http://gitlab-webservice-default.gitlab.svc.cluster.local:8181/root/will_IOT.git' "
        "--path 'config' --dest-namespace 'dev' --dest-server 'https://kubernetes.default.svc' "
        "--grpc-web"
    )

    if app_create.returncode != 0:
        colpr("r", "Error creating app. Trying to delete existing app first...")
        run("argocd app delete will --yes --grpc-web")
        time.sleep(3)

        # Try creating again
        run(
            "argocd app create will "
            "--repo 'http://gitlab-webservice-default.gitlab.svc.cluster.local:8181/root/will_IOT.git' "
            "--path 'config' --dest-namespace 'dev' --dest-server 'https://kubernetes.default.svc' "
            "--grpc-web"
        )


def sync_and_configure_app():
    # Ensure we're logged in again before sync operations
    login_argocd()

    # Synchronize the app and set up automation policies
    colpr("g", "Sync the app and configure for automated synchronization")
    run("argocd app sync will --grpc-web")
    time.sleep(5)
    colpr("y", "> set automated sync policy")
    run("argocd app set will --sync-policy automated --grpc-web")
    time.sleep(5)
    colpr("y", "> set auto-prune policy")
    run("argocd app set will --auto-prune --allow-empty --grpc-web")
    time.sleep(5)
    colpr("g", "View created app after sync and configuration")
    run("argocd app get will --grpc-web")


def main():
    answer = input("Do you want to create and configure the app? (y/n): ")
    if answer.lower() == "y":
        create_or_update_app()
        sync_and_configure_app()


if __name__ == "__main__":
    main()
