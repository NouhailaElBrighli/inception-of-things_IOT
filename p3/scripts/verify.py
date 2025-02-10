import os
import shutil
import subprocess
import sys
import time

from utils import *


def notify(title, message):
    # Use notify-send on Ubuntu
    subprocess.run(f'notify-send "{title}" "{message}"', shell=True)


def kill_portforward(process_pattern):
    run(f"pkill -f '{process_pattern}'", capture_output=False)


def port_forward(service, namespace, local_port, remote_port):
    cmd = (
        f"kubectl port-forward svc/{service} -n {namespace} {local_port}:{remote_port}"
    )
    return subprocess.Popen(
        cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def copy_to_clipboard(text):
    p = subprocess.Popen("xsel --clipboard --input", stdin=subprocess.PIPE, shell=True)
    p.communicate(input=text.encode())


def main():
    # If not started by another script, refresh Argo CD connection
    if len(sys.argv) < 2:
        kill_portforward("kubectl port-forward svc/argocd-server")
        port_forward("argocd-server", "argocd", 9090, 443)

    colpr("g", "======== Connect to Argo CD user-interface (UI) ========")
    answer = input("Do you want to be redirected to the argo-cd UI? (y/n): ")
    if answer.lower() == "y":
        res = run(
            'kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d',
            capture_output=True,
        )
        ARGOCD_PASSWORD = res.stdout.strip()
        colpr("y", "ARGO CD USERNAME: admin")
        colpr("y", f"ARGO CD PASSWORD: {ARGOCD_PASSWORD} (Pasted to clipboard)")
        copy_to_clipboard(ARGOCD_PASSWORD)
        colpr(
            "y",
            "Remember those credentials. Login here https://localhost:9090 for the Argo CD UI",
        )
        time.sleep(20)
        subprocess.run("xdg-open 'https://localhost:9090'", shell=True)

    colpr("g", "======== Verify automated synchronization ========")
    answer = input(
        "Do you want to push git repo changes to verify if running app synchronizes? (y/n): "
    )
    if answer.lower() != "y":
        sys.exit(0)

    run("gh auth login", capture_output=False)

    colpr(
        "y",
        "WAIT until will-app pods are ready before starting... (This can take up to 4 minutes)",
    )
    start = time.time()
    wait_proc = run(
        "kubectl wait pods -n dev --all --for condition=Ready --timeout=600s"
    )
    if wait_proc.returncode != 0:
        notify("App Error", "will-app pods creation timeout")
        colpr("r", "An error occurred. The creation of will-app pods timed out.")
        sys.exit(1)
    elapsed = int(time.time() - start)
    minutes = elapsed // 60
    seconds = elapsed % 60
    colpr(
        "y",
        f"{minutes} minutes and {seconds} seconds elapsed since waiting for will-app pods creation.",
    )

    run("kubectl config set-context --current --namespace=dev")
    kill_portforward("kubectl port-forward svc/will-app-service")

    # Port-forward will-app-service on port 8888
    port_forward("will-app-service", "dev", 8888, 8888)
    time.sleep(5)

    # Get current image version (assumes image version is at position 26 in the output)
    res = run(
        "kubectl describe deployments will-app-deployment | grep 'Image'",
        capture_output=True,
    )
    output = res.stdout.strip()
    try:
        imageVersion = int(output[25])
    except (IndexError, ValueError):
        colpr("r", "Could not parse image version from deployment description.")
        sys.exit(1)
    newImageVersion = 2 if imageVersion == 1 else 1

    colpr("c", f"Our current app uses version {imageVersion} of the following image")
    run("kubectl describe deployments will-app-deployment | grep 'Image'")
    colpr("c", "> curl http://localhost:8888")
    run("curl http://localhost:8888", capture_output=False)
    colpr(
        "c",
        f"\nNow we will change the git repository Argo-CD is connected to so that the image uses version {newImageVersion} instead of {imageVersion}",
    )
    run(
        "git clone 'git@github.com:NajmiAchraf/inception_of_things.git' tmp",
        capture_output=False,
    )
    time.sleep(2)
    os.chdir("tmp/p3")

    res = run("git push --dry-run", capture_output=True)
    if res.returncode == 128:
        colpr(
            "r",
            "You don't have the permissions to make changes in repo. You won't be able to verify synchronization.",
        )
        os.chdir("..")
        shutil.rmtree("tmp")
        sys.exit(1)

    with open("config/deployment.yaml", "r") as f:
        content = f.read()
    colpr("y", "Before changing deployment.yaml")
    colpr("c", "> cat config/deployment.yaml | grep 'image'")
    colpr("c", content)

    # Replace image version in deployment.yaml
    new_content = content.replace(
        f"wil42/playground:v{imageVersion}", f"wil42/playground:v{newImageVersion}"
    )
    with open("config/deployment.yaml", "w") as f:
        f.write(new_content)

    colpr("y", "After changing deployment.yaml")
    colpr("c", "> cat config/deployment.yaml | grep 'image'")
    colpr("c", new_content)

    run("git add config/deployment.yaml", capture_output=False)
    time.sleep(1)
    run(
        'git commit -m "App change image version for synchronization TEST"',
        capture_output=False,
    )
    time.sleep(1)
    run("git push origin master", capture_output=False)
    time.sleep(2)
    os.chdir("..")
    shutil.rmtree("tmp")

    colpr(
        "c",
        "WAIT until automated synchronization occurs (this can take up to 6 minutes)\nAvoid manual synchronization as it can lead to bugs during this demonstration.",
    )
    start_sync = time.time()
    wait_sync = run(
        f'kubectl wait deployment will-app-deployment --for=jsonpath="{{.spec.template.spec.containers[*].image}}"="wil42/playground:v{newImageVersion}" --timeout=600s'
    )
    if wait_sync.returncode != 0:
        notify("App Error", "Synchronization timeout")
        colpr("r", "An error occurred. Argo-CD takes abnormally long to synchronize.")
        sys.exit(1)
    elapsed_sync = int(time.time() - start_sync)
    minutes_sync = elapsed_sync // 60
    seconds_sync = elapsed_sync % 60
    colpr(
        "y",
        f"{minutes_sync} minutes and {seconds_sync} seconds elapsed since waiting for sync.",
    )

    colpr(
        "c",
        f"After automated synchronization the running app should mirror the git repo and use image version {newImageVersion}",
    )
    run(
        "kubectl describe deployments will-app-deployment | grep 'Image'",
        capture_output=False,
    )

    # Find an open port starting from 8889
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
        colpr("y", "Call failed retrying...")
        result_pf = run(
            f"ps aux | grep -v 'grep' | grep 'kubectl port-forward svc/will-app-service -n dev {openPort}'",
            capture_output=True,
        )
        if not result_pf.stdout.strip():
            time.sleep(5)
            port_forward("will-app-service", "dev", openPort, 8888)
        time.sleep(5)
        curl_proc = run(f"curl http://localhost:{openPort}", capture_output=False)

    notify("Verification finished", "Synchronization results are ready")


if __name__ == "__main__":
    main()
