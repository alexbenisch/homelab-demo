# Homelab Demo - TODO List

## Phase 1: Monitoring Stack

- [ ] Set up monitoring stack (Prometheus + Grafana)
- [ ] Configure Prometheus to scrape WordPress and MySQL metrics
- [ ] Create Grafana dashboards for WordPress and WooCommerce
- [ ] Set up alerting rules for resource usage and pod health
- [ ] Configure log aggregation (Loki or similar)

## Phase 2: Load Testing

- [ ] Set up load testing tools (k6, Apache Bench, or Locust)
- [ ] Create load test scenarios for WordPress homepage
- [ ] Create load test scenarios for WooCommerce shop pages
- [ ] Run baseline performance tests and document results

## Phase 3: Optimization & Autoscaling

- [ ] Identify and address performance bottlenecks
- [ ] Configure HPA (Horizontal Pod Autoscaler) based on metrics
- [ ] Test autoscaling under load

## Recommended Tools

### Monitoring
- **kube-prometheus-stack** - Includes Prometheus, Grafana, and Alertmanager
- **MySQL exporter** - For database metrics
- **WordPress/Apache exporters** - For application metrics
- **Service monitors** - GitOps-managed scrape configs

### Load Testing
- **k6** - Modern, scriptable, great for CI/CD integration
- **Apache Bench (ab)** - Quick and simple for basic HTTP tests
- **Locust** - Python-based, good for complex user scenarios

## Notes

- All configurations should follow GitOps principles (declarative, version-controlled)
- Test in non-production environment first
- Document baseline metrics before optimization
- Set up alerts before load testing to catch issues early
