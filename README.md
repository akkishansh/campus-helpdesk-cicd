# Campus Care Helpdesk

A small campus support request tracker built for a CI/CD and Kubernetes demonstration. Students can submit a ticket, search/filter the queue, review its priority and requester, and move it through Open, In Progress, and Resolved. Tickets are stored in SQLite.

> **Academic project eligibility:** The assignment guide asks for an existing academic project. This repository was created for the assignment because no earlier application project was available. Confirm with your instructor that a newly created project is acceptable before describing it as an existing project.

## Run locally (Windows)

1. Install Python 3.10 or newer.
2. Open PowerShell in this repository folder.
3. Run `python app.py`.
4. Open <http://localhost:8000>.
5. Run the checks with `python -m unittest discover -s tests -v`.

The app uses only Python's standard library. Its SQLite database is created in `data/tickets.db` (or at the path in `DATABASE_PATH`).

## Pipeline overview

The Jenkinsfile runs checkout, unit tests and syntax checks, Docker image build, Docker Hub push, Kubernetes manifest apply, rollout wait, and a health request from inside the cluster. It publishes both a build-number tag and `latest`.

## Docker Hub and Jenkins configuration

1. Create a **public** Docker Hub repository named `campus-helpdesk` and a Docker Hub access token.
2. Push this repository to your GitHub account.
3. Create an Ubuntu 24.04 EC2 instance. For a small single-node Minikube demo, select an instance with at least 2 vCPU and 4 GiB memory. Keep SSH (22) and Jenkins (8080) inbound rules restricted to your own IP address. Do not expose the Kubernetes NodePort to the public internet.
4. Copy `scripts/bootstrap-ec2.sh` to the instance and run it. Jenkins and Minikube will run on that same host. The script uses the official Jenkins package repository and downloads Minikube/kubectl.
5. Open `http://<EC2-public-IP>:8080` from your allowed IP, unlock Jenkins with `/var/lib/jenkins/secrets/initialAdminPassword`, install suggested plugins, and create a Pipeline job using **Pipeline script from SCM** with your GitHub repository URL and branch.
6. In **Manage Jenkins → Credentials**, add a **Username with password** credential with ID `dockerhub-creds`; use your Docker Hub username and access token (not your Docker Hub account password).
7. Run the job. The image repository is generated as `docker.io/<credential-username>/campus-helpdesk`; keep the Docker Hub repository public so Minikube can pull it without an image pull secret.

The EC2 helper script is a setup aid, not evidence that an AWS machine has already been created. AWS billing depends on your selected instance, storage, region, and run time. Stop or terminate the instance when the assignment is finished; deleting the instance may not delete separately retained EBS volumes.

## Verify the deployed application

On the EC2 instance, check the deployment with `sudo -u jenkins -H kubectl get pods,deployments,services,pvc`. The Service uses NodePort 30080 inside the host/Minikube network. To view it in your own browser without opening that port publicly:

1. On the EC2 host, start `sudo -u jenkins -H kubectl port-forward --address 127.0.0.1 service/campus-helpdesk 8081:80` and leave that command running.
2. On your Windows computer, open a second PowerShell window and run `ssh -i <path-to-key.pem> -L 8081:127.0.0.1:8081 ubuntu@<EC2-public-IP>`.
3. Open <http://localhost:8081> in your browser. Replace the key path and public IP with your own values.

The Kubernetes manifests create a 1 GiB PersistentVolumeClaim for SQLite data. The Minikube storage provisioner must be enabled. The app is intended for a coursework demonstration, not production use.

## Show the source-change redeployment

Change a visible label in `static/index.html`, commit and push the change to GitHub, then run the Jenkins job again. The build number becomes the new immutable image tag. In Jenkins console output, confirm the new tag was pushed and the Deployment rollout completed; refresh the browser to show the changed label.

## Submission checklist

- GitHub repository URL (add after creating/pushing to your account)
- `Jenkinsfile`, `Dockerfile`, and `k8s/deployment.yaml`, `k8s/service.yaml`, `k8s/pvc.yaml`
- Screenshots: Jenkins successful run, Docker Hub tags, running pod/Deployment/Service/PVC, app in browser, and second run after the source change
- `REPORT.md`, describing the actual setup and results
- `VIDEO_SCRIPT.md`, with a matching screen cue for each spoken section

Do not claim a cloud deployment or second run until you have completed it and captured the evidence.
