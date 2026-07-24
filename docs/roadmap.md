# Roadmap

## MVP

- FastAPI trace ingestion API
- PostgreSQL persistence
- Python SDK wrapper
- Demo agent
- React dashboard
- Run list page
- Run detail timeline
- Metrics summary
- Error list
- Backend tests

## Next Improvements

- Authentication for trace ingestion
- API keys per agent
- PostgreSQL migrations with Alembic
- Real LLM provider integration
- Streaming trace updates
- OpenTelemetry export support
- Trace search and filtering
- Cost model configuration
- Dockerized API and web services
- GitHub Actions CI
- Cloud deployment guide

## Production Considerations

A production version would need:

- Authentication and authorization
- Tenant isolation
- Rate limiting
- PII redaction
- Secret redaction
- Retention policies
- Background aggregation jobs
- Role-based dashboards
- Alerting integration
- Hosted database backups
