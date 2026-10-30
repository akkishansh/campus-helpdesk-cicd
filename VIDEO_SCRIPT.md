# CCA 2 video presentation script

About 5–7 minutes. Replace bracketed notes with your actual details. The bracketed text is what to show; do not read it aloud. Record only after the final TurfIt version has passed Jenkins and is running in Kubernetes.

## 1. Introduction

“Good morning, ma’am. I’m [name], roll number [number]. My CCA 2 project is TurfIt, a sports-ground discovery and booking application. I used GitHub, Jenkins, Docker, Docker Hub, AWS EC2, and Kubernetes through Minikube to automate the build and deployment. I’ll show the app first, then explain the pipeline and how I verified the deployment.”

[Show the TurfIt home page. Keep the browser address and project title visible.]

## 2. Show the application

“TurfIt helps players find sports venues, check a venue’s details, and choose an available date and time. The booking flow collects player details and shows a demonstration checkout. This is a coursework demo, so payment is simulated and no real payment is taken.”

[Search for a venue or sport. Open a venue, show its amenities and available time slots, then show the booking and demo payment pages. Do not submit a real payment or display personal information.]

“Players can look up their bookings. The app also has a community area. In the owner view, a venue owner can review bookings, manage turf listings, block an unavailable time, and see booking and revenue summaries.”

[Show My Bookings and Community briefly. Switch to For Owners; show Dashboard, My Turfs, Bookings, Analytics, and Schedule. Use demo records only.]

## 3. Show the source repository

“The source code and deployment configuration are in this GitHub repository. The Jenkinsfile defines the pipeline. The Dockerfile explains how the app is packaged. The Kubernetes folder contains the Deployment, Service, and persistent storage claim.”

[Show the GitHub repository and point to `app.py`, `static/`, `tests/`, `Dockerfile`, `Jenkinsfile`, and `k8s/`.]

“The repository and deployment resources still use the name campus-helpdesk because I reused the working CI/CD setup while changing the application to TurfIt.”

## 4. Explain Jenkins

“When I run the Jenkins Pipeline job, Jenkins checks out the GitHub code. It runs the Python unit tests and syntax checks. If those pass, Docker builds an image and gives it a unique tag based on the build number, along with a latest tag.”

[Show the final successful Jenkins build. Point to Checkout, Build and Test, and Build Docker Image.]

“Jenkins then uses a stored credential to sign in to Docker Hub and push both image tags. The access token is stored in Jenkins credentials and is not written into the source code.”

[Show the Push Image stage. Keep the credential page and token out of view.]

## 5. Explain deployment and verification

“The pipeline applies the Kubernetes configuration to Minikube running on my EC2 machine. Kubernetes starts the new image, exposes it through a Service inside the cluster, and uses a persistent volume claim for the SQLite database. Jenkins waits for the rollout and sends a health request to the app from inside the cluster.”

[Show the Deploy to Minikube and Verify Deployment stages. Then show terminal output for `kubectl get pods,deployments,services,pvc`.]

“AWS EC2 hosts Jenkins and Minikube for this project. This is a Minikube deployment on EC2, not Amazon EKS. I open the app using [your actual private access method].”

[Show the deployed TurfIt page and the matching Docker Hub numbered image tag. Do not expose the NodePort publicly.]

## 6. Demonstrate the final source change

“To verify the end-to-end flow, I pushed the final TurfIt source to GitHub and ran the Jenkins job. This successful build [number] created image tag [tag], completed the Kubernetes rollout, and passed the in-cluster health check.”

[Show the GitHub commit, matching Jenkins build number, Docker Hub tag, and ready Kubernetes pod. These should all refer to the same final run.]

## 7. Conclusion

“This project demonstrates continuous integration and deployment: source code is stored in GitHub, Jenkins checks and packages it, Docker Hub stores the versioned image, and Kubernetes deploys and verifies the application. Thank you.”

[Finish on the deployed application or the successful Jenkins result.]

## Before recording

- Replace name, roll number, build number, image tag, and access method with your real values.
- First commit and push the intended final TurfIt source, then run Jenkins and confirm all stages succeed. A previous `Finished: SUCCESS` for the older source does not prove the latest local edits were deployed.
- Capture the evidence listed in `REPORT.md`.
- Hide passwords, access tokens, private keys, email addresses, and AWS account details.
- If the final Jenkins run or Kubernetes status is not successful, say what is still pending instead of claiming deployment succeeded.
