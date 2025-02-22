.PHONY: all setup launch re_launch clean clean_launch verify re

# Install prerequisites, create a cluster, install Argo-CD and deploy app
all: setup

# Run complete setup (install prerequisites + create k3d cluster + configure kubernetes)
setup:
	@echo "Starting complete setup..."
	python3 scripts/setup.py

# Launch the Argo-CD app (assumes cluster and Argo-CD are running)
launch:
	@echo "Launching Argo-CD app..."
	python3 scripts/launch.py

# Remove only the Argo-CD app (keep k3d cluster)
clean:
	@echo "Deleting Argo-CD app..."
	python3 scripts/clean.py

# Remove the entire app (clean Argo-CD app and delete k3d cluster)
fclean: clean
	@echo "Deleting the Kubernetes cluster..."
	python3 scripts/fclean.py

# Verify the running app
verify:
	@echo "Verifying the Argo-CD app synchronization..."
	python3 scripts/verify.py

# Reload the Argo-CD app (clean then launch)
re_launch: clean launch

# Rebuild the app (clean then setup)
re: fclean all