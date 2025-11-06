#Deployment Docs
## Getting a Github Personal Access Token 
  - storing it in ~/.zshenv as GITHUB_TOKEN
  - better solution needed for future Deployment
## Adding the controlplane to my tailnet 
  - Because I want to connect to the controlplane with kubectl from my local machine
  I will add the VM to the tailnet and create a service, this way tailscale 
  advertises the k3s service on the IP in the tailnet. 
  This let's me access k3s via kubectl after adding the tailnet IP of the controlplane to the local k3s config on my machine.

## Installing Flux and creating Deployment
  - 
