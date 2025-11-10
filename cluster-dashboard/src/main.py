"""
Cluster Dashboard - A comprehensive Kubernetes cluster monitoring dashboard.

Displays cluster information including:
- Nodes (status, resources, region, cloud provider)
- Pods (by namespace, status, resource usage)
- Services and endpoints
- Ingress routes and domains
- Storage volumes
- Cloud provider metadata
"""

import os
import socket
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Application metadata
APP_NAME = "cluster-dashboard"
APP_VERSION = "1.0.0"

# Configuration
PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize FastAPI
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Kubernetes cluster monitoring dashboard",
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# Initialize Kubernetes client
try:
    # Try in-cluster config first (when running in K8s)
    config.load_incluster_config()
    IN_CLUSTER = True
except:
    try:
        # Fall back to kubeconfig (for local development)
        config.load_kube_config()
        IN_CLUSTER = False
    except:
        IN_CLUSTER = None

# Kubernetes API clients
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
networking_v1 = client.NetworkingV1Api()


def get_cluster_info() -> Dict[str, Any]:
    """Get basic cluster information."""
    try:
        version = client.VersionApi().get_code()
        return {
            "kubernetes_version": version.git_version,
            "platform": version.platform,
            "in_cluster": IN_CLUSTER,
        }
    except:
        return {
            "kubernetes_version": "Unknown",
            "platform": "Unknown",
            "in_cluster": IN_CLUSTER,
        }


def get_nodes() -> List[Dict[str, Any]]:
    """Get all nodes with their status and metadata."""
    try:
        nodes = v1.list_node()
        node_list = []

        for node in nodes.items:
            # Get node conditions
            ready_status = "Unknown"
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    ready_status = "Ready" if condition.status == "True" else "NotReady"

            # Extract cloud provider info from labels
            labels = node.metadata.labels or {}
            cloud_provider = labels.get("node.kubernetes.io/instance-type", "Unknown")
            region = labels.get("topology.kubernetes.io/region", "Unknown")
            zone = labels.get("topology.kubernetes.io/zone", "Unknown")

            # Get resource capacity
            capacity = node.status.capacity or {}
            allocatable = node.status.allocatable or {}

            node_info = {
                "name": node.metadata.name,
                "status": ready_status,
                "roles": ", ".join([k.split("/")[1] for k in labels.keys() if "node-role.kubernetes.io" in k]) or "worker",
                "age": (datetime.now(node.metadata.creation_timestamp.tzinfo) - node.metadata.creation_timestamp).days,
                "version": node.status.node_info.kubelet_version,
                "os": f"{node.status.node_info.os_image}",
                "kernel": node.status.node_info.kernel_version,
                "container_runtime": node.status.node_info.container_runtime_version,
                "cpu_capacity": capacity.get("cpu", "0"),
                "memory_capacity": capacity.get("memory", "0"),
                "cpu_allocatable": allocatable.get("cpu", "0"),
                "memory_allocatable": allocatable.get("memory", "0"),
                "pods_capacity": capacity.get("pods", "0"),
                "instance_type": cloud_provider,
                "region": region,
                "zone": zone,
                "addresses": [
                    {"type": addr.type, "address": addr.address}
                    for addr in node.status.addresses
                ],
            }
            node_list.append(node_info)

        return node_list
    except ApiException as e:
        print(f"Error fetching nodes: {e}")
        return []


def get_pods_by_namespace() -> Dict[str, List[Dict[str, Any]]]:
    """Get all pods grouped by namespace."""
    try:
        pods = v1.list_pod_for_all_namespaces()
        pods_by_ns = {}

        for pod in pods.items:
            ns = pod.metadata.namespace
            if ns not in pods_by_ns:
                pods_by_ns[ns] = []

            # Get pod status
            phase = pod.status.phase
            ready_containers = sum(1 for c in (pod.status.container_statuses or []) if c.ready)
            total_containers = len(pod.spec.containers)

            pod_info = {
                "name": pod.metadata.name,
                "status": phase,
                "ready": f"{ready_containers}/{total_containers}",
                "restarts": sum(c.restart_count for c in (pod.status.container_statuses or [])),
                "age": (datetime.now(pod.metadata.creation_timestamp.tzinfo) - pod.metadata.creation_timestamp).days,
                "node": pod.spec.node_name or "Pending",
                "ip": pod.status.pod_ip or "None",
            }
            pods_by_ns[ns].append(pod_info)

        return pods_by_ns
    except ApiException as e:
        print(f"Error fetching pods: {e}")
        return {}


def get_services() -> List[Dict[str, Any]]:
    """Get all services across all namespaces."""
    try:
        services = v1.list_service_for_all_namespaces()
        service_list = []

        for svc in services.items:
            # Get external IPs/endpoints
            external_ips = []
            if svc.status.load_balancer and svc.status.load_balancer.ingress:
                external_ips = [ing.ip or ing.hostname for ing in svc.status.load_balancer.ingress]

            service_info = {
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "external_ips": external_ips,
                "ports": [f"{p.port}/{p.protocol}" for p in (svc.spec.ports or [])],
                "age": (datetime.now(svc.metadata.creation_timestamp.tzinfo) - svc.metadata.creation_timestamp).days,
            }
            service_list.append(service_info)

        return service_list
    except ApiException as e:
        print(f"Error fetching services: {e}")
        return []


def get_ingresses() -> List[Dict[str, Any]]:
    """Get all ingress routes with domains."""
    try:
        ingresses = networking_v1.list_ingress_for_all_namespaces()
        ingress_list = []

        for ing in ingresses.items:
            # Extract hosts and paths
            rules = []
            for rule in (ing.spec.rules or []):
                host = rule.host or "*"
                paths = []
                if rule.http and rule.http.paths:
                    paths = [p.path for p in rule.http.paths]
                rules.append({"host": host, "paths": paths})

            # Get load balancer IPs
            addresses = []
            if ing.status.load_balancer and ing.status.load_balancer.ingress:
                addresses = [lb.ip or lb.hostname for lb in ing.status.load_balancer.ingress]

            ingress_info = {
                "name": ing.metadata.name,
                "namespace": ing.metadata.namespace,
                "class": ing.spec.ingress_class_name or "default",
                "rules": rules,
                "addresses": addresses,
                "age": (datetime.now(ing.metadata.creation_timestamp.tzinfo) - ing.metadata.creation_timestamp).days,
            }
            ingress_list.append(ingress_info)

        return ingress_list
    except ApiException as e:
        print(f"Error fetching ingresses: {e}")
        return []


def get_pvcs() -> List[Dict[str, Any]]:
    """Get all persistent volume claims."""
    try:
        pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
        pvc_list = []

        for pvc in pvcs.items:
            pvc_info = {
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase,
                "volume": pvc.spec.volume_name or "Pending",
                "capacity": pvc.status.capacity.get("storage", "Unknown") if pvc.status.capacity else "Pending",
                "access_modes": ", ".join(pvc.spec.access_modes or []),
                "storage_class": pvc.spec.storage_class_name or "default",
                "age": (datetime.now(pvc.metadata.creation_timestamp.tzinfo) - pvc.metadata.creation_timestamp).days,
            }
            pvc_list.append(pvc_info)

        return pvc_list
    except ApiException as e:
        print(f"Error fetching PVCs: {e}")
        return []


def get_namespaces() -> List[Dict[str, Any]]:
    """Get all namespaces."""
    try:
        namespaces = v1.list_namespace()
        ns_list = []

        for ns in namespaces.items:
            ns_info = {
                "name": ns.metadata.name,
                "status": ns.status.phase,
                "age": (datetime.now(ns.metadata.creation_timestamp.tzinfo) - ns.metadata.creation_timestamp).days,
            }
            ns_list.append(ns_info)

        return ns_list
    except ApiException as e:
        print(f"Error fetching namespaces: {e}")
        return []


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    cluster_info = get_cluster_info()
    nodes = get_nodes()
    pods_by_ns = get_pods_by_namespace()
    services = get_services()
    ingresses = get_ingresses()
    pvcs = get_pvcs()
    namespaces = get_namespaces()

    # Calculate statistics
    total_pods = sum(len(pods) for pods in pods_by_ns.values())
    running_pods = sum(1 for pods in pods_by_ns.values() for pod in pods if pod["status"] == "Running")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "cluster_info": cluster_info,
        "nodes": nodes,
        "pods_by_namespace": pods_by_ns,
        "services": services,
        "ingresses": ingresses,
        "pvcs": pvcs,
        "namespaces": namespaces,
        "stats": {
            "total_nodes": len(nodes),
            "total_namespaces": len(namespaces),
            "total_pods": total_pods,
            "running_pods": running_pods,
            "total_services": len(services),
            "total_ingresses": len(ingresses),
            "total_pvcs": len(pvcs),
        },
    })


@app.get("/api/cluster")
async def api_cluster():
    """API endpoint for cluster information."""
    return get_cluster_info()


@app.get("/api/nodes")
async def api_nodes():
    """API endpoint for node information."""
    return get_nodes()


@app.get("/api/pods")
async def api_pods():
    """API endpoint for pod information."""
    return get_pods_by_namespace()


@app.get("/api/services")
async def api_services():
    """API endpoint for services."""
    return get_services()


@app.get("/api/ingresses")
async def api_ingresses():
    """API endpoint for ingresses."""
    return get_ingresses()


@app.get("/api/pvcs")
async def api_pvcs():
    """API endpoint for PVCs."""
    return get_pvcs()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    print(f"Starting {APP_NAME} v{APP_VERSION}")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Port: {PORT}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        log_level=LOG_LEVEL,
        reload=ENVIRONMENT == "development",
    )
