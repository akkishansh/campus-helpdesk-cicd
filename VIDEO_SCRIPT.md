# Video presentation script

Replace bracketed personal details and only state results you have personally verified. The cues in square brackets are screen actions, not spoken words. Aim for about 5-7 minutes at a calm pace.

## 1. Introduction

“Good morning, ma’am. My name is [your name], and this is my Cloud Computing and DevOps project. I built Campus Care Helpdesk, a small campus support ticket application, and connected it to a CI/CD pipeline using GitHub, Jenkins, Docker, Docker Hub, AWS, and Minikube with Kubernetes. I’ll first show the app, then explain how a code change moves through the pipeline and gets deployed.”

[Show the title slide or the app home page. Keep the project name visible.]

## 2. Explain the application

“This is the Campus Care Helpdesk dashboard. The summary cards show how many requests are in the queue, how many are open, in progress, or resolved. I can search requests and use these tabs to filter by status. Each row shows the request, category, priority, current status, and requester.”

[Show the dashboard. Point to the summary cards, search box, and status filters.]

“I’ll create a request now. I enter a short title, choose a category and priority, add my name and details, and submit it. The request appears in the queue, and the totals update.”

[Click **New request**. Fill the form with a harmless demo request such as “Library Wi-Fi connection” and submit. Show the new row and updated counts.]

“I can change the request status as the support team works on it. The queue also supports searching and filtering, so a user can quickly find a request. The application stores tickets in SQLite, and its health endpoint is used by the deployment checks.”

[Change the ticket to **In Progress**, show the status filter, and briefly search for the ticket.]

## 3. Show the source repository

“The project source and deployment files are kept together in GitHub. The Python app and its tests are here. The Dockerfile describes how to package the app. The Jenkinsfile defines the automated pipeline, and the Kubernetes folder contains the Deployment, Service, and persistent volume claim manifests.”

[Show the GitHub repository. Point out `app.py`, `tests/`, `Dockerfile`, `Jenkinsfile`, and the `k8s/` files.]

## 4. Explain the Jenkins pipeline

“Jenkins checks out the latest repository code. It runs the automated unit tests and a Python syntax check. If those pass, it builds the Docker image, tags it with the Jenkins build number, and pushes it to Docker Hub using a credential stored in Jenkins. The access token is not written into the source code.”

[Show the Jenkins job and a successful build’s stage view or console output. Point to checkout, tests, Docker build, and push.]

“The pipeline then applies the Kubernetes manifests to Minikube, waits for the rollout, and checks the running resources. It also sends a health request to the application from inside the cluster.”

[Show the deployment and verification stages in Jenkins.]

## 5. Show Docker Hub and Kubernetes

“This is the Docker Hub repository where Jenkins published the image. The build-number tag tells me which source version was built. Kubernetes uses that image in the application Deployment. The Service gives the app a stable address inside the cluster, and the persistent volume claim provides storage for the ticket database.”

[Show Docker Hub with the build-number tag, then show the terminal output for `kubectl get pods,deployments,services,pvc`.]

“For the browser demonstration, I access the app through an SSH tunnel to the EC2 host. The Minikube NodePort is not opened to the public internet.”

[Show the deployed app in the browser at the forwarded local address.]

## 6. Demonstrate the second deployment

“The assignment also asks us to prove that a source-code change flows through the pipeline. I changed [name the exact visible change], committed and pushed it to GitHub, and started the Jenkins pipeline again. Jenkins produced a new build-number image tag and deployed it to Minikube.”

[Show the changed GitHub line or commit, the second Jenkins build and new image tag, then refresh the deployed app to show the change.]

## 7. Close

“This project demonstrates the complete automated flow: GitHub source, Jenkins build and tests, Docker image creation and publishing, and Kubernetes deployment on Minikube. I verified the running application and demonstrated a second deployment after a source-code change. Thank you.”

[Finish on the updated running application or the successful second Jenkins build.]

## Before recording

- Replace your name and the exact changed feature in the script.
- Complete the AWS/Jenkins/Docker Hub setup and the second run before describing them as completed.
- Capture screenshots and use your real build numbers, image tags, and Kubernetes statuses.
- Do not show passwords, access tokens, private SSH keys, or Jenkins credential values in the recording.
