from utils import *


def main():
    run("k3d cluster delete p3", capture_output=False)
    colpr("g", "Cluster p3 deleted.")


if __name__ == "__main__":
    main()
