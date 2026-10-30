# CCA 2: CI/CD Pipeline Implementation and Deployment

**Student:** [Name and roll number]  
**Course:** [Course / section]  
**GitHub repository:** https://github.com/akkishansh/campus-helpdesk-cicd  
**Docker Hub image:** `akkishansh/campus-helpdesk`  
**Submission date:** [Date]

## 1. Project overview

TurfIt is a sports-ground discovery and booking demo. Players can browse and filter venues, check available time slots, create and look up bookings, and explore player features. A separate owner view supports venue listings, booking review, schedule blocks, and basic booking and revenue summaries. The app uses Python's standard library and SQLite. Payment choices are demonstration-only; no real payment is processed.

The repository and original Jenkins job retain the names `campus-helpdesk-cicd` and `campus-helpdesk`. The image and Kubernetes resource names were kept so the existing CI/CD setup could be reused while the application changed to TurfIt.

## 2. Tools and architecture

- **GitHub** stores the application and the pipeline/deployment files.
- **Jenkins** runs on the Ubuntu EC2 host and reads the `Jenkinsfile` from GitHub.
- **Docker** packages the application into a container image.
- **Docker Hub** stores the versioned image and the `latest` tag.
- **Minikube and Kubernetes** run on the EC2 host. Jenkins applies a Deployment, a NodePort Service, and a 1 GiB PersistentVolumeClaim.
- **AWS EC2** provides the machine for Jenkins and Minikube. This design uses Minikube on EC2; it is not Amazon EKS.

The image repository is public so Minikube can pull it without a registry pull secret. Jenkins stores the Docker Hub access token in a credential named `dockerhub-creds`. The token is not kept in the repository.

## 3. CI/CD pipeline stages

1. **Checkout:** Jenkins checks out the configured GitHub branch.
2. **Build and Test:** Python unit tests and syntax checks run before packaging.
3. **Build Docker Image:** Docker builds the app and tags it with the Jenkins build number and `latest`.
4. **Push Image:** Jenkins logs in using `dockerhub-creds` and pushes both tags to Docker Hub.
5. **Deploy to Minikube:** Jenkins applies the PersistentVolumeClaim, updates the Deployment to use the numbered image tag, applies the Service, and waits for the rollout.
6. **Verify Deployment:** Jenkins lists the Kubernetes resources and makes an HTTP request to `/health` from inside the cluster.

## 4. Implementation record

The Jenkins dashboard and Pipeline job were set up, the Docker Hub credential was added, and the user observed a `Finished: SUCCESS` run and the image in Docker Hub. Record the values from the run you use as final evidence below.

**AWS region:** ap-south-1 (Mumbai) [confirm in AWS console]  
**EC2 instance type:** [record from AWS console]  
**Jenkins job and build number:** [record final build number]  
**Build date:** [record date]  
**Docker Hub tag:** [for example, `<build-number>` and `latest`]  
**Kubernetes pod status:** [record actual status]  
**Application browser URL/access method:** [record actual method, such as SSH tunnel]

The previously confirmed successful build occurred before the latest local TurfIt edits. Those edits are still uncommitted in the working copy, so the prior success is not evidence that this exact current version was built or deployed. Before submitting, publish the intended final source and run Jenkins again; use that build's console output and tag as the final evidence. Do not describe the latest TurfIt version as deployed until that run succeeds.

## 5. Verification and evidence checklist

Capture these screenshots after the final source version has passed Jenkins:

1. **GitHub:** repository page showing the committed app and `Jenkinsfile`, `Dockerfile`, and `k8s/` directory.
2. **Jenkins:** successful final build and console output for tests, Docker image push, rollout, and health check.
3. **Docker Hub:** `akkishansh/campus-helpdesk` with the final numbered tag and `latest`.
4. **Kubernetes:** output from `kubectl get pods,deployments,services,pvc` showing ready resources.
5. **Application:** the deployed TurfIt page opened through the approved SSH tunnel or other private access method.
6. **Change/deploy proof:** GitHub commit for the final source and the matching Jenkins build/image tag.

Never include the Docker Hub token, Jenkins initial admin password, SSH private key, or other credentials in screenshots or the report. Keep AWS security group access limited to your own IP. Do not expose the Minikube NodePort publicly.

## 6. Final outcome

This project demonstrates an automated source-to-deployment path: GitHub provides the code, Jenkins runs checks and builds the container, Docker Hub stores the image, and Kubernetes on Minikube rolls out and health-checks the application. The final conclusion and build details should be completed only after the current TurfIt source has been pushed and the matching Jenkins run and Kubernetes status have been captured.
