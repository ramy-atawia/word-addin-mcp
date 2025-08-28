# CI/CD Pipeline Setup and Configuration

This document describes the complete CI/CD pipeline setup for the Word Add-in MCP project, including GitHub Actions workflows, deployment strategies, and monitoring.

## Overview

The CI/CD pipeline consists of several interconnected workflows that provide:

- **Continuous Integration**: Automated testing, code quality checks, and security scanning
- **Continuous Deployment**: Automated deployment to staging and production environments
- **Monitoring & Alerting**: Real-time system health monitoring and performance tracking
- **Dependency Management**: Automated dependency updates and security vulnerability scanning

## Workflow Structure

### 1. CI Pipeline (`ci.yml`)

**Triggers**: Push to main/develop branches, Pull Requests

**Jobs**:
- **Backend Testing**: Python tests with PostgreSQL and Redis services
- **Frontend Testing**: Node.js tests with coverage reporting
- **Code Quality**: Linting, formatting, and complexity checks
- **Security Scanning**: Vulnerability scanning with Safety and Bandit
- **Build & Package**: Docker image building for successful builds
- **Notifications**: Slack notifications for success/failure

**Key Features**:
- Matrix testing with multiple Python versions
- Service containers for PostgreSQL and Redis
- Coverage reporting to Codecov
- Automated Docker image building
- Slack integration for team notifications

### 2. Deployment Pipeline (`deploy.yml`)

**Triggers**: Push to main branch, Manual workflow dispatch

**Jobs**:
- **Staging Deployment**: Automated deployment to staging environment
- **Production Deployment**: Automated deployment to production environment
- **Rollback**: Automatic rollback on deployment failures
- **Release Management**: GitHub release creation for successful deployments

**Key Features**:
- Environment-specific deployment strategies
- Container registry integration (GitHub Container Registry)
- Automated rollback on failures
- GitHub release management
- Slack notifications for deployment status

### 3. Dependency Updates (`dependencies.yml`)

**Triggers**: Weekly schedule (Monday 9 AM UTC), Manual workflow dispatch

**Jobs**:
- **Python Updates**: Automated Python dependency updates
- **Node.js Updates**: Automated Node.js dependency updates
- **Security Scanning**: Comprehensive security vulnerability scanning
- **Automated PRs**: Creation of pull requests for dependency updates

**Key Features**:
- Scheduled weekly dependency updates
- Security vulnerability detection
- Automated pull request creation
- Comprehensive security reporting
- Integration with security tools (Safety, Bandit, npm audit)

### 4. Monitoring & Alerting (`monitoring.yml`)

**Triggers**: Every 5 minutes (scheduled), Manual workflow dispatch

**Jobs**:
- **Health Checks**: System health monitoring for staging and production
- **Performance Monitoring**: Response time and throughput testing
- **Error Rate Monitoring**: Error rate tracking and alerting
- **Alerting**: Critical issue notifications
- **Reporting**: Comprehensive monitoring reports

**Key Features**:
- Real-time health monitoring
- Performance benchmarking
- Error rate tracking
- Automated alerting
- Comprehensive reporting

## Configuration

### Environment Variables

The following environment variables need to be configured in GitHub Secrets:

```bash
# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Azure OpenAI (for testing)
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Database (for testing)
DATABASE_URL=postgresql://user:password@localhost:5432/db
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key
```

### GitHub Environments

Configure the following environments in GitHub:

#### Staging Environment
- **Name**: `staging`
- **Protection Rules**: 
  - Required reviewers: 1
  - Wait timer: 0 minutes
  - Deployment branches: `develop`

#### Production Environment
- **Name**: `production`
- **Protection Rules**:
  - Required reviewers: 2
  - Wait timer: 5 minutes
  - Deployment branches: `main`

## Local Development

### Running CI/CD Locally

Use Docker Compose to run the CI/CD environment locally:

```bash
# Start CI/CD services
docker-compose -f docker-compose.ci.yml up -d

# Run backend tests
docker-compose -f docker-compose.ci.yml exec ci-backend pytest tests/ -v

# Run frontend tests
docker-compose -f docker-compose.ci.yml exec ci-frontend npm test

# Run code quality checks
docker-compose -f docker-compose.ci.yml exec ci-code-quality bash

# Run security scans
docker-compose -f docker-compose.ci.yml exec ci-security bash
```

### Pre-commit Hooks

Install pre-commit hooks for local code quality checks:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

## Deployment Strategy

### Staging Deployment

1. **Trigger**: Push to `develop` branch or manual workflow dispatch
2. **Process**:
   - Build Docker images with `staging` tag
   - Deploy to staging environment
   - Run smoke tests
   - Send notification

### Production Deployment

1. **Trigger**: Push to `main` branch or manual workflow dispatch
2. **Process**:
   - Build Docker images with `latest` and commit SHA tags
   - Deploy to production environment
   - Run health checks
   - Create GitHub release
   - Send notification

### Rollback Strategy

1. **Automatic Rollback**: Triggered on deployment failure
2. **Manual Rollback**: Available through workflow dispatch
3. **Rollback Process**:
   - Revert to previous deployment
   - Verify rollback success
   - Send notification

## Monitoring and Alerting

### Health Checks

- **Frequency**: Every 5 minutes
- **Endpoints**: Backend health, Frontend availability
- **Metrics**: Response time, Status codes, Error rates

### Performance Monitoring

- **Frequency**: On-demand (workflow dispatch)
- **Metrics**: Response times, Throughput, Success rates
- **Tools**: Locust, Custom performance scripts

### Error Rate Monitoring

- **Frequency**: Every 5 minutes
- **Threshold**: Alert if error rate > 5%
- **Actions**: Slack notifications, Issue creation

## Security Features

### Vulnerability Scanning

- **Python**: Safety, Bandit, pip-audit
- **Node.js**: npm audit, Snyk
- **Frequency**: Weekly + on dependency updates

### Security Gates

- **Code Quality**: Linting, formatting, complexity checks
- **Security**: Vulnerability scanning, dependency analysis
- **Testing**: Unit tests, integration tests, security tests

## Troubleshooting

### Common Issues

1. **Dependency Cache Issues**
   ```bash
   # Clear GitHub Actions cache
   # Go to repository settings > Actions > Cache
   # Delete specific cache entries
   ```

2. **Service Health Check Failures**
   ```bash
   # Check service logs
   docker-compose -f docker-compose.ci.yml logs ci-postgres
   docker-compose -f docker-compose.ci.yml logs ci-redis
   ```

3. **Test Failures**
   ```bash
   # Run tests locally first
   cd backend && pytest tests/ -v
   cd frontend && npm test
   ```

### Debug Mode

Enable debug logging in GitHub Actions:

```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

## Best Practices

### Code Quality

- Write tests for all new features
- Maintain >80% test coverage
- Use pre-commit hooks locally
- Follow coding standards (Black, isort, flake8)

### Security

- Regular dependency updates
- Security vulnerability scanning
- Code review for security issues
- Environment variable management

### Deployment

- Test in staging first
- Use blue-green deployment when possible
- Monitor deployment metrics
- Have rollback procedures ready

### Monitoring

- Set appropriate alerting thresholds
- Regular performance testing
- Comprehensive error tracking
- Automated reporting

## Future Enhancements

### Planned Features

1. **Advanced Deployment Strategies**
   - Blue-green deployment
   - Canary deployments
   - Feature flags integration

2. **Enhanced Monitoring**
   - APM integration (New Relic, DataDog)
   - Custom metrics dashboard
   - Predictive alerting

3. **Security Improvements**
   - Container vulnerability scanning
   - Infrastructure as Code security
   - Compliance reporting

4. **Performance Optimization**
   - Build caching improvements
   - Parallel job execution
   - Resource optimization

## Support

For CI/CD pipeline issues:

1. Check GitHub Actions logs
2. Review workflow configuration
3. Test locally with Docker Compose
4. Consult this documentation
5. Create issue in repository

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Playwright Testing](https://playwright.dev/)
- [Security Tools](https://bandit.readthedocs.io/, https://pyup.io/safety/)
