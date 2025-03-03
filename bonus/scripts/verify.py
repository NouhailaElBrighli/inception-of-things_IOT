import os
import re
import shutil
import sys
import time

from utils import *


def refresh_argocd_connection():
    """If launched without extra arguments, kill and restart the Argo-CD connection."""
    if len(sys.argv) < 2:
        kill_portforward("kubectl port-forward svc/argocd-server")
        port_forward("argocd-server", "argocd", 9090, 443)


def wait_for_will_app_pods():
    """Wait for the 'will-app' pods to be ready and report elapsed time."""
    colpr(
        "y",
        "WAIT until will-app pods are ready before starting... (This can take up to 6 minutes)",
    )
    start = time.time()
    wait_proc = run(
        "kubectl wait pods -n dev --all --for condition=Ready --timeout=600s"
    )
    if wait_proc.returncode != 0:
        notify("App Error", "will-app pods creation timeout")
        colpr("r", "An error occurred. The creation of will-app pods timed out.")
        sys.exit(1)
    elapsed = elapsed_time(start)
    colpr("y", f"{elapsed} elapsed since waiting for will-app pods creation.")


def update_deployment_image():
    """Clone the repo, update deployment.yaml, commit and push changes."""
    # Port-forward will-app-service on port 8888 for testing
    run("kubectl config set-context --current --namespace=dev")
    kill_portforward("kubectl port-forward svc/will-app-service")
    port_forward("will-app-service", "dev", 8888, 8888)
    time.sleep(5)

    # Retrieve the current image version using regex matching.
    res = run(
        "kubectl describe deployments will-app-deployment | grep 'Image'",
        capture_output=True,
    )
    output = res.stdout.strip()
    match = re.search(r"wil42/playground:v(\d+)", output)
    if match:
        imageVersion = int(match.group(1))
    else:
        colpr("r", "Could not extract image version from deployment description.")
        sys.exit(1)

    newImageVersion = 2 if imageVersion == 1 else 1

    colpr("c", f"Our current app uses version {imageVersion}")
    run("kubectl describe deployments will-app-deployment | grep 'Image'")

    colpr("c", "> curl http://localhost:8888")
    run("curl http://localhost:8888", capture_output=False)

    colpr(
        "c",
        f"\nChanging the git repo so the image uses version {newImageVersion} instead of {imageVersion}",
    )
    run(
        "git clone 'http://gitlab.localhost:8081/root/will_IOT.git' tmp",
        capture_output=False,
    )

    time.sleep(2)
    os.chdir("tmp")

    # Check for push permissions
    res = run("git push --dry-run", capture_output=True)
    if res.returncode == 128:
        colpr(
            "r",
            "You don't have permissions to make changes in the repo. Unable to verify synchronization.",
        )
        os.chdir("..")
        shutil.rmtree("tmp")
        sys.exit(1)

    with open("config/deployment.yaml", "r") as f:
        content = f.read()
    colpr("y", "Before updating deployment.yaml")
    colpr("c", "> cat config/deployment.yaml | grep 'image'")
    colpr("c", content)

    new_content = content.replace(
        f"wil42/playground:v{imageVersion}", f"wil42/playground:v{newImageVersion}"
    )
    with open("config/deployment.yaml", "w") as f:
        f.write(new_content)

    colpr("y", "After updating deployment.yaml")
    colpr("c", "> cat config/deployment.yaml | grep 'image'")
    colpr("c", new_content)

    run("git add config/deployment.yaml", capture_output=False)
    time.sleep(1)
    run(
        'git commit -m "App change image version for synchronization TEST"',
        capture_output=False,
    )
    time.sleep(1)
    run("git branch -M main", capture_output=False)
    run("git push -uf origin main", capture_output=False)
    time.sleep(2)
    os.chdir("..")
    shutil.rmtree("tmp")
    return newImageVersion


def wait_for_sync(newImageVersion):
    """Wait until the Argo-CD automated synchronization takes effect."""
    colpr("c", "WAIT until automated synchronization occurs (can take up to 6 minutes)")
    start_sync = time.time()
    cmd = f'kubectl wait deployment will-app-deployment --for=jsonpath="{{.spec.template.spec.containers[*].image}}"="wil42/playground:v{newImageVersion}" --timeout=600s'
    wait_sync = run(cmd)
    if wait_sync.returncode != 0:
        notify("App Error", "Synchronization timeout")
        colpr("r", "Argo-CD synchronization took abnormally long.")
        sys.exit(1)
    elapsed_sync = elapsed_time(start_sync)
    colpr("y", f"{elapsed_sync} elapsed since waiting for synchronization.")
    colpr("c", f"After sync the running app should use image version {newImageVersion}")
    run(
        "kubectl describe deployments will-app-deployment | grep 'Image'",
        capture_output=False,
    )
    return


def test_app_with_curl():
    """Find an open port to test the updated app using curl."""
    openPort = 8889
    while True:
        result = run(f"lsof -i :{openPort}", capture_output=True)
        if not result.stdout.strip():
            break
        openPort += 1
    colpr("c", f"> curl http://localhost:{openPort}")
    time.sleep(5)
    port_forward("will-app-service", "dev", openPort, 8888)
    time.sleep(10)
    curl_proc = run(f"curl http://localhost:{openPort}", capture_output=False)
    while curl_proc.returncode != 0:
        colpr("y", "Call failed, retrying...")
        result_pf = run(
            f"ps aux | grep -v 'grep' | grep 'kubectl port-forward svc/will-app-service -n dev {openPort}'",
            capture_output=True,
        )
        if not result_pf.stdout.strip():
            time.sleep(5)
            port_forward("will-app-service", "dev", openPort, 8888)
        time.sleep(5)
        curl_proc = run(f"curl http://localhost:{openPort}", capture_output=False)


def main():
    refresh_argocd_connection()

    answer = input("Do you want to verify automated synchronization? (y/n): ")
    if answer.lower() == "y":
        colpr("g", "======== Verify automated synchronization ========")
        wait_for_will_app_pods()
        newVersion = update_deployment_image()
        wait_for_sync(newVersion)
        test_app_with_curl()
        notify("Verification finished", "Synchronization results are ready")


if __name__ == "__main__":
    main()
