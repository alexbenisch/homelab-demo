# Freelance Radar - Source Code

A Kubernetes-based job search application that integrates with the Adzuna API to find and store freelance job opportunities.

## Architecture

- **FastAPI Application**: REST API for job searching and management
- **PostgreSQL Database**: Persistent storage for job searches and results
- **Adzuna Integration**: Real-time job search via Adzuna API
- **GitOps Deployment**: Deployed via Flux CD to k3s cluster
- **URL**: https://freelance-radar.k8s-demo.de

## Features

- Search jobs using Adzuna API with filters (location, keywords, date range)
- Store search history and results in PostgreSQL
- View statistics on saved jobs and salary information
- RESTful API endpoints for job management
- Health checks and database connectivity monitoring

## Deployment

This application is deployed via GitOps using Flux CD. The Kubernetes manifests are in `apps/base/freelance-radar/`.

See the [deployment README](../base/freelance-radar/README.md) for full documentation.

## Building the Docker Image

```bash
cd apps/freelance-radar
docker build -t freelance-radar:latest .
```

For k3s, import the image:
```bash
docker save freelance-radar:latest | sudo k3s ctr images import -
```

For kind:
```bash
kind load docker-image freelance-radar:latest
```

## Triggering Deployment

After building and importing the image:

```bash
# Trigger Flux reconciliation
flux reconcile kustomization apps --with-source

# Verify deployment
kubectl get all -n freelance-radar
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8080/health
```

### Database Check
```bash
curl http://localhost:8080/db
```

### Search Jobs
```bash
curl -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": "python developer",
    "country": "us",
    "location": "San Francisco",
    "max_days_old": 7,
    "results_per_page": 20,
    "page": 1
  }'
```

### Get Recent Searches
```bash
curl http://localhost:8080/searches?limit=10
```

### Get Saved Jobs
```bash
curl http://localhost:8080/jobs?limit=20
```

### Get Statistics
```bash
curl http://localhost:8080/stats
```

## API Documentation

Once deployed, visit `http://localhost:8080/docs` for interactive Swagger documentation.

## Configuration

### Environment Variables

Configured via ConfigMap and Secrets in `k8s/freelance-radar/`:

- `DATABASE_HOST`: PostgreSQL hostname (default: postgres)
- `DATABASE_NAME`: Database name (default: radar)
- `POSTGRES_USER`: Database user (from secret)
- `POSTGRES_PASSWORD`: Database password (from secret)
- `ADZUNA_APP_ID`: Adzuna API App ID (from secret)
- `ADZUNA_API_KEY`: Adzuna API Key (from secret)

### Supported Countries

The Adzuna API supports searches in multiple countries. Common values:
- `us` - United States
- `gb` - United Kingdom
- `de` - Germany
- `au` - Australia
- `ca` - Canada

Full list: [Adzuna API Documentation](https://developer.adzuna.com/activedocs)

## Database Schema

### job_searches
- `id`: Serial primary key
- `search_query`: Search keywords
- `country`: Country code
- `location`: Optional location filter
- `result_count`: Total results from API
- `mean_salary`: Average salary from results
- `created_at`: Timestamp

### jobs
- `id`: Serial primary key
- `search_id`: Foreign key to job_searches
- `job_id`: Unique Adzuna job identifier
- `title`: Job title
- `description`: Job description (truncated to 500 chars)
- `company`: Company name
- `location`: Job location
- `salary_min`: Minimum salary
- `salary_max`: Maximum salary
- `contract_type`: permanent/contract
- `contract_time`: full_time/part_time
- `redirect_url`: Link to original job posting
- `created_date`: When job was posted
- `saved_at`: When saved to database

## Monitoring

### Check Pod Status
```bash
kubectl get pods -n freelance-radar
```

### View Logs
```bash
# Application logs
kubectl logs -f deployment/freelance-radar -n freelance-radar

# PostgreSQL logs
kubectl logs -f deployment/postgres -n freelance-radar
```

### Check Services
```bash
kubectl get svc -n freelance-radar
```

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod -l app=freelance-radar -n freelance-radar
```

### Database connection issues
```bash
# Test database from app pod
kubectl exec -it deployment/freelance-radar -n freelance-radar -- curl http://localhost:8000/db

# Connect to PostgreSQL directly
kubectl exec -it deployment/postgres -n freelance-radar -- psql -U radar -d radar
```

### Check API credentials
```bash
kubectl get secret adzuna-secret -n freelance-radar -o jsonpath='{.data.ADZUNA_APP_ID}' | base64 -d
```

## Development

### Local Development
```bash
cd apps/freelance-radar/app

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_HOST=localhost
export DATABASE_NAME=radar
export POSTGRES_USER=radar
export POSTGRES_PASSWORD=radar123
export ADZUNA_APP_ID=your_app_id
export ADZUNA_API_KEY=your_api_key

# Run locally
uvicorn main:app --reload
```

### Rebuild and Redeploy
```bash
# Rebuild image
docker build -t freelance-radar:latest apps/freelance-radar/

# For k3s
docker save freelance-radar:latest | sudo k3s ctr images import -

# Restart deployment
kubectl rollout restart deployment/freelance-radar -n freelance-radar
```

## Cleanup

```bash
kubectl delete namespace freelance-radar
```

## Next Steps

- Add Helm chart for easier deployment
- Implement init job for database schema management
- Add CI/CD pipeline with GitHub Actions
- Configure TLS/HTTPS via cert-manager
- Add monitoring with Prometheus/Grafana
- Implement caching for API responses
- Add user authentication
