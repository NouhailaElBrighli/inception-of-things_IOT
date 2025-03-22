import subprocess
import sys
import time

from utils import *


def show_state_k3d_cluster():
    """Show the state of the k3d kubernetes cluster."""
    colpr("g", "======== Show state of k3d cluster ========")
    run("k3d cluster list")


def show_state_kubernetes_cluster():
    """Show the state of the kubernetes cluster."""
    colpr("g", "======== Show state of kubernetes cluster ========")
    run("kubectl cluster-info")


def show_state_argocd():
    """Show the state of the argocd application."""
    colpr("g", "======== Show state of argocd application ========")
    res = run("argocd app list --grpc-web")
    if res.returncode != 0:
        """If launched without extra arguments, kill and restart the Argo-CD connection."""
        kill_portforward("kubectl port-forward svc/argocd-server")
        port_forward("argocd-server", "argocd", 9090, 443)
        time.sleep(3)
        res = run("argocd app list --grpc-web")
        if res.returncode != 0:
            colpr("r", "An error occurred. The creation of anajmi-app pods timed out.")
            sys.exit(1)


def main():
    show_state_k3d_cluster()
    show_state_kubernetes_cluster()
    show_state_argocd()


if __name__ == "__main__":
    main()
