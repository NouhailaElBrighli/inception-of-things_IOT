import subprocess
import sys
import time

from utils import colpr, elapsed_time, run


def ensure_cluster_running():
    result = run("kubectl cluster-info", capture_output=True)
    if result.returncode != 0:
        colpr("r", "No Kubernetes cluster is running for Argo-CD.")
        answer = input("Do you want us to first create the cluster? (y/n): ")
        if answer.lower() == "y":
            run("python3 scripts/setup.py")
        sys.exit(0)


def wait_for_argocd_pods():
    colpr("y", "WAITING FOR ARGO-CD PODS TO RUN... (This can take up to 6 minutes)")
    if len(sys.argv) > 1 and sys.argv[1] == "called_from_setup":
        time.sleep(10)
    start_time = time.time()
    wait_proc = run(
        "kubectl wait pods -n argocd --all --for condition=Ready --timeout=600s"
    )
    if wait_proc.returncode != 0:
        colpr("r", "Argo-CD pods creation timed out.")
        colpr("r", "Deleting the k3d cluster...")
        run("python3 scripts/fclean.py")
        sys.exit(1)
    elapsed = elapsed_time(start_time)
    colpr("y", f"{elapsed} elapsed since waiting for Argo-CD pods creation.")


def start_argocd_port_forward():
    # Kill any existing port-forward process and start a new one in the background.
    colpr("g", "Start port-forward to Argo-CD server")
    run("pkill -f 'kubectl port-forward svc/argocd-server'")
    subprocess.Popen(
        "kubectl port-forward svc/argocd-server -n argocd 9090:443",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def login_argocd():
    # Retrieve the Argo-CD admin password and log in.
    colpr("g", "Login to Argo-CD")
    res = run(
        'kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d',
        capture_output=True,
    )
    ARGOCD_PASSWORD = res.stdout.strip()
    run(
        f"argocd login localhost:9090 --username admin --password {ARGOCD_PASSWORD} --insecure --grpc-web"
    )
    run("kubectl config set-context --current --namespace=argocd")


def create_or_update_app():
    # Create the Argo-CD app, or, if it exists, offer to delete and recreate it.
    colpr("g", "Create Argo-CD app 'will'")
    app_create = run(
        "argocd app create will --repo 'https://github.com/NajmiAchraf/will_IOT.git' "
        "--path 'config' --dest-namespace 'dev' --dest-server 'https://kubernetes.default.svc' --grpc-web"
    )
    if app_create.returncode == 20:
        colpr("r", "Error creating Argo-CD app 'will'. It may already exist.")
        answer = input("Do you want us to delete and recreate the app? (y/n): ")
        if answer.lower() == "y":
            colpr("y", "Deleting the app...")
            run("argocd app delete will --yes --grpc-web")
            colpr("y", "Relaunching Argo-CD for you.")
            run("python3 scripts/launch.py")
            sys.exit(0)
        sys.exit(1)
    colpr("g", "View created app before sync and configuration")
    run("argocd app get will --grpc-web")
    time.sleep(5)


def sync_and_configure_app():
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


def run_verify():
    # Pass any additional argument to verify
    run(f"python3 scripts/ui.py 'called_from_launch'")
    run(f"python3 scripts/verify.py 'called_from_launch'")
    sys.exit(0)


def main():
    if len(sys.argv) < 2:
        colpr(
            "g",
            "======== Argo CD setup - Create CI/CD pipeline for Kubernetes app ========",
        )

    ensure_cluster_running()
    wait_for_argocd_pods()
    start_argocd_port_forward()
    login_argocd()
    create_or_update_app()
    sync_and_configure_app()
    run_verify()


if __name__ == "__main__":
    main()
