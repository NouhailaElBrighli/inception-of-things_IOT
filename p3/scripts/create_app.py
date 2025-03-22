import sys
import time

from utils import colpr, run


def create_or_update_app():
    # Create the Argo-CD app, or, if it exists, offer to delete and recreate it.
    colpr("g", "Create Argo-CD app 'anajmi'")
    app_create = run(
        "argocd app create anajmi --repo 'https://github.com/NajmiAchraf/anajmi_IOT.git' "
        "--path 'config' --dest-namespace 'dev' --dest-server 'https://kubernetes.default.svc' --grpc-web"
    )
    if app_create.returncode == 20:
        colpr("r", "Error creating Argo-CD app 'anajmi'. It may already exist.")
        answer = input("Do you want us to delete and recreate the app? (y/n): ")
        if answer.lower() == "y":
            colpr("y", "Deleting the app...")
            run("argocd app delete anajmi --yes --grpc-web")
            colpr("y", "Relaunching Argo-CD for you.")
            run("python3 scripts/launch.py")
            sys.exit(0)
        sys.exit(1)
    colpr("g", "View created app before sync and configuration")
    run("argocd app get anajmi --grpc-web")
    time.sleep(5)


def sync_and_configure_app():
    # Synchronize the app and set up automation policies
    colpr("g", "Sync the app and configure for automated synchronization")
    run("argocd app sync anajmi --grpc-web")
    time.sleep(5)
    colpr("y", "> set automated sync policy")
    run("argocd app set anajmi --sync-policy automated --grpc-web")
    time.sleep(5)
    colpr("y", "> set auto-prune policy")
    run("argocd app set anajmi --auto-prune --allow-empty --grpc-web")
    time.sleep(5)
    colpr("g", "View created app after sync and configuration")
    run("argocd app get anajmi --grpc-web")


def main():
    answer = input("Do you want to create and configure the app? (y/n): ")
    if answer.lower() == "y":
        create_or_update_app()
        sync_and_configure_app()


if __name__ == "__main__":
    main()
