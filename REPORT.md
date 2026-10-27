# CI/CD Pipeline Implementation and Deployment Report

**Course:** TYCSE - Cloud Computing and DevOps  
**Student:** [Add your name and roll number]  
**GitHub repository:** [Add the repository URL after publishing]  
**Date:** [Add submission date]

## 1. Project overview

Campus Care Helpdesk is a small web application for tracking campus support requests. A user can create a ticket, search and filter requests, view priority and status, and update a ticket through Open, In Progress, and Resolved. The Python application uses SQLite for ticket storage and provides a health endpoint for deployment checks.

**Project origin:** This app was created for this assignment because I did not have an earlier application project ready. The guide asks for an existing academic project, so I confirmed that this newly created project is acceptable with the course instructor before submission. [Update this statement to reflect the instructor's answer.]

## 2. Tools and architecture

- GitHub stores the application, tests, Dockerfile, Jenkinsfile, and Kubernetes manifests.
- Jenkins runs on an Ubuntu 24.04 EC2 instance and reads the Jenkinsfile from GitHub.
- Docker builds and pushes a versioned image to Docker Hub.
- Minikube runs a single-node Kubernetes cluster on the EC2 host.
- Kubernetes Deployment, Service, and PersistentVolumeClaim resources run and expose the application and store its SQLite data.

## 3. Pipeline stages

1. **Checkout:** Jenkins checks out the repository configured for the Pipeline job.
2. **Build and Test:** Python unit tests and syntax checks run before an image is built.
3. **Build Docker Image:** Jenkins builds the app image and tags it with the Jenkins build number and `latest`.
4. **Push Image:** Jenkins logs in to Docker Hub using its stored `dockerhub-creds` credential and pushes both tags.
5. **Deploy to Minikube:** Jenkins applies the persistent volume claim, Deployment, and Service, then waits for the Deployment rollout.
6. **Verify Deployment:** Jenkins lists the Kubernetes resources and makes an HTTP health request from inside the cluster.

## 4. Setup and demonstration results

**AWS region and instance:** [Fill in]  
**Jenkins URL:** [Fill in; omit credentials]  
**GitHub URL:** [Fill in]  
**Docker Hub image:** [Fill in]  
**First successful Jenkins build:** [Build number and date]  
**Second build after code change:** [Build number and changed feature/label]  
**Application access method:** [For example, local browser through SSH tunnel]  
**Pod/Deployment/Service status:** [Record actual output]

The Jenkins credential stores the Docker Hub access token; it is not included in the repository. The Docker Hub repository is public for Minikube image pulls. Jenkins is restricted to my IP address. I used an SSH tunnel for browser access rather than exposing the Minikube NodePort publicly.

## 5. Evidence to attach

1. GitHub repository showing source, `Jenkinsfile`, `Dockerfile`, and `k8s/` files.
2. Jenkins console showing passing tests, image push, rollout, and health verification.
3. Docker Hub repository showing the build-number image tag.
4. Kubernetes output showing the running pod, Deployment, Service, and persistent volume claim.
5. Browser showing the deployed application.
6. The changed source file and successful second pipeline run showing the new version.

## 6. Conclusion

The pipeline automates the path from a source-code change to a tested container image and a Kubernetes deployment. The second run demonstrates that a change pushed to GitHub can be built, published, and redeployed through Jenkins.
