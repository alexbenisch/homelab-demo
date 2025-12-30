# Freelance Radar

A job search and tracking application that integrates with the Adzuna API to find and store freelance opportunities. Built with FastAPI and PostgreSQL, deployed on Kubernetes.

## Overview

- **URL**: https://freelance-radar.k8s-demo.de
- **Built with**: FastAPI + PostgreSQL + Adzuna API integration
- **Image**: `freelance-radar:latest` (local build)
- **Database**: PostgreSQL 16 with persistent storage (5Gi)
- **Access**: Public (via Traefik ingress)

## Features

- **Job Search**: Search for jobs via Adzuna API with filters (location, keywords, date range, country)
- **Search History**: Track all job searches with metadata (result count, average salary)
- **Job Storage**: Persistent storage of job postings in PostgreSQL
- **Statistics**: View aggregated statistics on saved jobs and salary information
- **REST API**: Full RESTful API with auto-generated documentation
- **Health Checks**: Liveness and readiness probes for Kubernetes
- **SOPS-encrypted secrets**: API credentials and database credentials encrypted with SOPS

## API Endpoints

### Documentation
- `GET /docs` - Interactive Swagger API documentation
- `GET /redoc` - ReDoc API documentation

### Health & Status
- `GET /health` - Health check endpoint
- `GET /db` - Database connectivity check

### Job Search
- `POST /search` - Search for jobs and store results
  ```json
  {
    "keywords": "python developer",
    "country": "us",
    "location": "San Francisco",
    "max_days_old": 7,
    "results_per_page": 20,
    "page": 1
  }
  ```

### Data Retrieval
- `GET /searches?limit=10` - Get recent search history
- `GET /jobs?search_id={id}&limit=20` - Get saved jobs (optionally filtered by search_id)
- `GET /stats` - Get statistics (total searches, jobs, salary averages)

## Database Schema

### job_searches
Stores search history and metadata:
- `id` - Auto-incrementing primary key
- `search_query` - Search keywords
- `country` - Country code (us, gb, de, au, ca, etc.)
- `location` - Optional location filter
- `result_count` - Total results returned by API
- `mean_salary` - Average salary from results
- `created_at` - Search timestamp

### jobs
Stores individual job postings:
- `id` - Auto-incrementing primary key
- `search_id` - Foreign key to job_searches
- `job_id` - Unique Adzuna job identifier
- `title` - Job title
- `description` - Job description (truncated to 500 chars)
- `company` - Company name
- `location` - Job location
- `salary_min` - Minimum salary
- `salary_max` - Maximum salary
- `contract_type` - permanent/contract
- `contract_time` - full_time/part_time
- `redirect_url` - Link to original job posting
- `created_date` - When job was posted
- `saved_at` - When saved to database

## Building the Image

From the repository root:

```bash
cd apps/freelance-radar
docker build -t freelance-radar:latest .
```

For k3s, import the image:
```bash
docker save freelance-radar:latest | sudo k3s ctr images import -
```

## Deployment

The application is automatically deployed via Flux CD when changes are pushed to the repository.

### Manual Deployment

```bash
# Trigger Flux reconciliation
flux reconcile kustomization apps --with-source

# Verify deployment
kubectl get all -n freelance-radar
```

## Usage Examples

### Search for Python jobs in San Francisco
```bash
curl -X POST https://freelance-radar.k8s-demo.de/search \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": "python developer",
    "country": "us",
    "location": "San Francisco",
    "max_days_old": 7,
    "results_per_page": 20
  }'
```

### Get recent searches
```bash
curl https://freelance-radar.k8s-demo.de/searches?limit=5
```

### Get saved jobs
```bash
curl https://freelance-radar.k8s-demo.de/jobs?limit=20
```

### Get statistics
```bash
curl https://freelance-radar.k8s-demo.de/stats
```

## Configuration

### Environment Variables

Configured via ConfigMap and Secrets:

**ConfigMap (app-config)**:
- `DATABASE_HOST`: PostgreSQL hostname (default: postgres)
- `DATABASE_NAME`: Database name (default: radar)

**Secrets (postgres-secret)** - SOPS encrypted:
- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DB`: Database name

**Secrets (adzuna-secret)** - SOPS encrypted:
- `ADZUNA_APP_ID`: Adzuna API Application ID
- `ADZUNA_API_KEY`: Adzuna API Key

### Supported Countries

The Adzuna API supports searches in multiple countries:
- `us` - United States
- `gb` - United Kingdom
- `de` - Germany
- `au` - Australia
- `ca` - Canada
- `fr` - France
- `nl` - Netherlands
- `pl` - Poland

Full list: [Adzuna API Documentation](https://developer.adzuna.com/activedocs)

## Monitoring

### Check Pod Status
```bash
kubectl get pods -n freelance-radar
```

### View Application Logs
```bash
kubectl logs -f -n freelance-radar -l app=freelance-radar
```

### View PostgreSQL Logs
```bash
kubectl logs -f -n freelance-radar -l app=postgres
```

### Check Database
```bash
# Connect to PostgreSQL
kubectl exec -it -n freelance-radar deployment/postgres -- psql -U radar -d radar

# Check tables
\dt

# View recent searches
SELECT * FROM job_searches ORDER BY created_at DESC LIMIT 10;

# View saved jobs
SELECT title, company, location, salary_min, salary_max FROM jobs ORDER BY saved_at DESC LIMIT 10;
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod -n freelance-radar -l app=freelance-radar
kubectl logs -n freelance-radar -l app=freelance-radar
```

### Database connection issues
```bash
# Test database from app pod
kubectl exec -it -n freelance-radar deployment/freelance-radar -- curl http://localhost:8000/db

# Check database status
kubectl get pod -n freelance-radar -l app=postgres
```

### API not responding
```bash
# Check health endpoint
curl https://freelance-radar.k8s-demo.de/health

# Check ingress
kubectl get ingress -n freelance-radar
kubectl describe ingress -n freelance-radar
```

## Resources

### Application
- **CPU Request**: 100m
- **Memory Request**: 128Mi
- **CPU Limit**: 500m
- **Memory Limit**: 512Mi

### PostgreSQL
- **CPU Request**: 100m
- **Memory Request**: 256Mi
- **CPU Limit**: 500m
- **Memory Limit**: 512Mi
- **Storage**: 5Gi PVC (local-path)

## Future Enhancements

- Add user authentication and multi-user support
- Implement job alerts and notifications
- Add advanced filtering and search capabilities
- Create a web UI for easier job browsing
- Implement job application tracking
- Add export functionality (CSV, PDF)
- Integrate with additional job boards
- Add scheduled job search automation
