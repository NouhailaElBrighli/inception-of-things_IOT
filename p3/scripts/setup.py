import sys

from utils import *


def InstallPrerequisites():
    colpr("g", "======== Install prerequisites ========")

    if not command_exists("docker"):
        colpr("y", "Docker not installed. Installing docker...")
        run("sudo apt-get update && sudo apt-get install -y docker.io")
    else:
        colpr("g", "Docker already installed.")

    if not command_exists("kubectl"):
        colpr("y", "kubectl not installed. Installing kubectl...")
        run(
            'curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"'
        )
        run("sudo mkdir -p /usr/local/bin")
        run("sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl")
        run("rm kubectl")
    else:
        colpr("g", "kubectl already installed.")

    if not command_exists("k3d"):
        colpr("y", "k3d not installed. Installing k3d...")
        run("bash scripts/k3d_install.sh")
    else:
        colpr("g", "k3d already installed.")

    if not command_exists("argocd"):
        colpr("y", "argocd not installed. Installing argocd...")
        run(
            "VERSION=$(curl -L -s https://raw.githubusercontent.com/argoproj/argo-cd/stable/VERSION) && "
            "curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/download/v$VERSION/argocd-linux-amd64 && "
            "sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd && "
            "rm argocd-linux-amd64"
        )
    else:
        colpr("g", "argocd already installed.")

    if not command_exists("gh"):
        colpr("y", "gh not installed. Installing gh...")
        run("sudo apt-get update && sudo apt-get install -y gh")
    else:
        colpr("g", "gh already installed.")

    if not command_exists("xsel"):
        colpr("y", "xsel not installed. Installing xsel...")
        run("sudo apt-get update && sudo apt-get install -y xsel")
    else:
        colpr("g", "xsel already installed.")


def InitializeK3DCluster():
    colpr(
        "g", "======== K3D setup - Create kubernetes cluster on local machine ========"
    )
    ret = run("k3d cluster create p3")
    if ret == 1:
        colpr("r", "An error occurred when creating the cluster.")
        colpr("r", "The cluster probably already exists.")
        answer = input("Do you want us to delete and restart the cluster? (y/n): ")
        if answer.lower() == "y":
            colpr("y", "Deleting the existing cluster...")
            run("k3d cluster delete p3")
            colpr("y", "Restarting the cluster...")
            run("python3 scripts/setup.py")
            sys.exit(0)
        sys.exit(1)

    run("kubectl cluster-info")


def ConfigureKubernetesForArgoCD():
    colpr("g", "======== Kubernetes namespaces setup ========")
    run("kubectl create namespace argocd")
    run("kubectl create namespace dev")
    run("kubectl get namespace")

    colpr(
        "g",
        "======== Argo CD setup - Allow the creation of a CI/CD pipeline around kubernetes application ========",
    )
    run(
        "kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
    )
    run("python3 scripts/launch.py 'called_from_setup'")
    sys.exit(0)


def main():
    InstallPrerequisites()
    InitializeK3DCluster()
    ConfigureKubernetesForArgoCD()


if __name__ == "__main__":
    main()
