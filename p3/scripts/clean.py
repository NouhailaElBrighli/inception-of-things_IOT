import time

from utils import *


def main():
    # Kill existing port-forward for argocd-server
    kill_portforward("kubectl port-forward svc/argocd-server")
    # Refresh Argo-CD connection
    port_forward("argocd-server", "argocd", 9090, 443)
    time.sleep(5)
    # Delete the app (using yes to auto-confirm)
    run("yes | argocd app delete anajmi --grpc-web", capture_output=False)
    run("pkill -f 'kubectl port-forward svc/argocd-server'", capture_output=False)
    colpr("g", "Clean completed.")


if __name__ == "__main__":
    main()
