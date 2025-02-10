import subprocess
import sys
import time

from utils import *


def main():
    # Protect against running without an active Kubernetes cluster
    result = run("kubectl cluster-info", capture_output=True)
    if result.returncode != 0:
        colpr(
            "r",
            "An error occurred. No Kubernetes cluster is running for Argo-CD to be launched.",
        )
        answer = input("Do you want us to first create the cluster? (y/n): ")
        if answer.lower() == "y":
            run("python3 setup.py")
        sys.exit(0)

    if len(sys.argv) < 2:
        colpr(
            "g",
            "======== Argo CD setup - Allow the creation of a CI/CD pipeline around kubernetes application ========",
        )

    colpr("y", "WAITING FOR ARGO-CD PODS TO RUN... (This can take up to 6 minutes)")
    if len(sys.argv) > 1 and sys.argv[1] == "called_from_setup":
        time.sleep(10)

    start_time = time.time()
    wait_proc = run(
        "kubectl wait pods -n argocd --all --for condition=Ready --timeout=600s"
    )
    if wait_proc.returncode != 0:
        colpr("r", "An error occurred. The creation of Argo-CD pods timed out.")
        colpr("r", "We will delete the k3d cluster...")
        run("python3 fclean.py")
        sys.exit(1)

    elapsed = elapsed_time(start_time)
    colpr("y", f"{elapsed} elapsed since waiting for Argo-CD pods creation.")

    # Kill any existing port-forward process
    run("pkill -f 'kubectl port-forward svc/argocd-server'")

    # Start the port-forward in the background and suppress output
    subprocess.Popen(
        "kubectl port-forward svc/argocd-server -n argocd 9090:443",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Retrieve the Argo-CD admin password
    res = run(
        'kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d',
        capture_output=True,
    )
    ARGOCD_PASSWORD = res.stdout.strip()

    # Log in to Argo-CD
    run(
        f"argocd login localhost:9090 --username admin --password {ARGOCD_PASSWORD} --insecure --grpc-web"
    )

    run("kubectl config set-context --current --namespace=argocd")

    # Create the Argo-CD app and check if an error code 20 is returned
    app_create = run(
        "argocd app create will --repo 'git@github.com:NajmiAchraf/inception_of_things.git' --path 'p3/config' --dest-namespace 'dev' --dest-server 'https://kubernetes.default.svc' --grpc-web"
    )
    if app_create.returncode == 20:
        colpr("r", "An error occurred when creating Argo-CD app 'will'.")
        colpr("r", "Probably because the Argo-CD app 'will' already exists.")
        answer = input("Do you want us to delete and recreate the app? (y/n): ")
        if answer.lower() == "y":
            colpr("y", "Deleting the app...")
            run("yes | argocd app delete will --grpc-web")
            colpr("y", "Now we will relaunch Argo-CD for you.")
            run("python3 launch.py")
            sys.exit(0)
        sys.exit(1)

    colpr("g", "View created app before sync and configuration")
    run("argocd app get will --grpc-web")
    time.sleep(5)

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

    # Run the verify script with passed argument, if any
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    run(f"./scripts/verify.sh 'called_from_launch' {arg}")
    sys.exit(0)


if __name__ == "__main__":
    main()
