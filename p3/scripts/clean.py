import time

from utils import colpr, run


def main():
    # Kill existing port-forward for argocd-server
    run("pkill -f 'kubectl port-forward svc/argocd-server'", capture_output=False)
    # # Refresh Argo-CD connection
    # run(
    #     "kubectl port-forward svc/argocd-server -n argocd 9090:443",
    #     capture_output=False,
    # )
    time.sleep(5)  # Wait to avoid race conditions
    # Delete the app (using yes to auto-confirm)
    run("yes | argocd app delete will --grpc-web", capture_output=False)
    run("pkill -f 'kubectl port-forward svc/argocd-server'", capture_output=False)
    colpr("g", "Clean completed.")


if __name__ == "__main__":
    main()
