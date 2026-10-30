#!/usr/bin/env bash
# Run on a fresh Ubuntu 24.04 EC2 instance as ubuntu (or another sudo-capable user).
set -euo pipefail

if [[ "$(. /etc/os-release && echo "$VERSION_ID")" != "24.04" ]]; then
  echo "This helper expects Ubuntu 24.04 LTS." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg fontconfig git openjdk-21-jre docker.io
sudo systemctl enable --now docker

# Jenkins official Debian package repository.
sudo install -d -m 0755 /etc/apt/keyrings
sudo curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key -o /etc/apt/keyrings/jenkins-keyring.asc
echo "deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list >/dev/null
sudo apt-get update
sudo apt-get install -y jenkins

ARCH=amd64
sudo curl -fsSL "https://storage.googleapis.com/minikube/releases/latest/minikube-linux-${ARCH}" -o /tmp/minikube
sudo install /tmp/minikube /usr/local/bin/minikube
sudo curl -fsSLo /usr/local/bin/kubectl "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/${ARCH}/kubectl"
sudo chmod +x /usr/local/bin/kubectl
sudo usermod -aG docker jenkins
sudo systemctl enable --now jenkins
sudo systemctl restart jenkins

# Run Minikube as the Jenkins service user so the pipeline uses the same kubeconfig.
sudo -u jenkins -H minikube start --driver=docker --cpus=2 --memory=3000 --force
sudo -u jenkins -H kubectl get nodes

echo
echo "Setup complete. Open Jenkins on port 8080 from your own IP only."
echo "Initial Jenkins password: sudo cat /var/lib/jenkins/secrets/initialAdminPassword"
echo "Create a Pipeline job pointed at your GitHub repository after the first push."
