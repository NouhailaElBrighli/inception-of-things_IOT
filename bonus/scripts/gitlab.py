import sys
import time

from utils import colpr, run


def gitlab():
    # clone from github
    run("git clone 'git@github.com:NajmiAchraf/will_IOT.git' tmp", capture_output=False)
    # enter the directory
    run("cd tmp")
    # change the remote to gitlab
    run(
        "git remote set-url origin 'http://gitlab.localhost:8081/root/will_IOT.git'",
        capture_output=False,
    )
    # push to gitlab
    run("git push -uf origin master", capture_output=False)
    # remove the directory
    run("cd ..", capture_output=False)
    run("rm -rf tmp", capture_output=False)

    time.sleep(5)


def create_or_update_app():
    if len(sys.argv) > 1 and sys.argv[1] == "called_from_setup":
        run("python3 scripts/create_app.py called_from_setup")
    else:
        run("python3 scripts/create_app.py")


def main():
    answer = input("Do you want to create and configure the app? (y/n): ")
    if answer.lower() == "y":
        gitlab()
        create_or_update_app()
