# Security Best Practices Checklist

## Initial Setup Security

### Secrets Configuration
- [ ] GitHub Personal Access Token created with minimal required scopes
- [ ] Linear API Key created with read/write permissions only
- [ ] Both secrets added to GitHub repository secrets (not hardcoded)
- [ ] No secrets committed to version control (check `.gitignore`)
- [ ] Secret names follow naming convention (ends with `_TOKEN` or `_KEY`)

### Access Control
- [ ] Repository access limited to required team members
- [ ] Workflow permissions set to read/write only where needed
- [ ] Branch protection rules enabled for `main` branch
- [ ] Required reviews for pull requests enabled
- [ ] Signed commits encouraged (optional but recommended)

## Ongoing Security Practices

### Monthly Tasks
- [ ] Review workflow execution logs for anomalies
- [ ] Check secret usage patterns
- [ ] Verify no unauthorized workflow modifications
- [ ] Review artifact storage and retention
- [ ] Check API rate limit consumption

### Quarterly Tasks
- [ ] Rotate GitHub Personal Access Token (every 90 days)
- [ ] Rotate Linear API Key (every 90 days)
- [ ] Review and update workflow permissions
- [ ] Audit team access to repository
- [ ] Review third-party actions versions

### Incident Response Checklist
- [ ] Document incident response procedures
- [ ] Test secret revocation process
- [ ] Create backup secrets (stored securely offline)
- [ ] Document communication chain for security issues
- [ ] Regular security drills (quarterly)

## Workflow Security

### Before Each Workflow Run
- [ ] Verify secrets are properly configured
- [ ] Check workflow file hasn't been tampered with
- [ ] Review parameters for any suspicious inputs
- [ ] Ensure target repositories are expected/trusted

### During Execution
- [ ] Monitor workflow logs for unexpected errors
- [ ] Verify API calls are to expected endpoints only
- [ ] Check artifact contents don't contain sensitive data
- [ ] Validate output data before Linear updates

### After Execution
- [ ] Review execution logs for security events
- [ ] Verify artifacts are properly secured
- [ ] Confirm Linear updates were successful
- [ ] Check for any error messages indicating security issues

## Code Security

### Before Committing Code
- [ ] No hardcoded credentials anywhere in code
- [ ] All secrets accessed via environment variables
- [ ] Input validation for all user-provided parameters
- [ ] Output sanitization to prevent data leaks
- [ ] Error messages don't expose sensitive information

### Code Review Checklist
- [ ] Secret scanning enabled (CodeQL)
- [ ] Dependency vulnerability scanning active
- [ ] No use of `eval()` or similar dangerous functions
- [ ] All external inputs properly validated
- [ ] HTTPS enforced for all API calls

## API Security

### GitHub API
- [ ] Token has minimal required permissions
- [ ] Rate limiting implemented and monitored
- [ ] Timeouts configured for all requests
- [ ] SSL certificate validation enabled
- [ ] User-Agent header properly set

### Linear API
- [ ] API key stored securely in GitHub Secrets
- [ ] GraphQL queries validated before execution
- [ ] Input sanitization for all query variables
- [ ] Error handling doesn't expose API key
- [ ] Request/response logging excludes sensitive data

## Data Protection

### Data Classification
- [ ] Public data handled appropriately
- [ ] Internal data properly secured
- [ ] Confidential data encrypted at rest and in transit
- [ ] Sensitive fields filtered from logs

### Data Handling
- [ ] Temporary files created with secure permissions (700)
- [ ] Artifacts encrypted during storage
- [ ] Data retention policies configured
- [ ] Secure deletion of temporary data after processing

## Monitoring & Alerting

### Security Monitoring
- [ ] Failed authentication attempts tracked
- [ ] Unusual API usage patterns monitored
- [ ] Workflow failures investigated
- [ ] Secret access audited regularly

### Alert Configuration
- [ ] Alerts for workflow failures
- [ ] Notifications for security scan findings
- [ ] Alerts for unusual execution patterns
- [ ] Notifications for dependency vulnerabilities

## Compliance

### Documentation
- [ ] Security architecture documented
- [ ] Incident response procedures documented
- [ ] Access control policies documented
- [ ] Data handling procedures documented

### Audit Trail
- [ ] All workflow executions logged
- [ ] Secret access logged
- [ ] API calls logged (excluding sensitive data)
- [ ] Changes to workflows tracked in Git history

## Emergency Procedures

### Compromised GitHub Token
1. [ ] Immediately revoke token at https://github.com/settings/tokens
2. [ ] Generate new token with same permissions
3. [ ] Update `GITHUB_TOKEN` secret in repository
4. [ ] Review recent workflow runs for suspicious activity
5. [ ] Document incident and lessons learned

### Compromised Linear API Key
1. [ ] Immediately revoke key in Linear settings
2. [ ] Generate new API key
3. [ ] Update `LINEAR_API_KEY` secret in repository
4. [ ] Review Linear activity for unauthorized changes
5. [ ] Document incident and lessons learned

### Suspected Workflow Tampering
1. [ ] Disable all workflows immediately
2. [ ] Review Git history for unauthorized changes
3. [ ] Audit team access permissions
4. [ ] Investigate source of tampering
5. [ ] Restore workflows from known-good commit
6. [ ] Enable additional branch protection rules

## Security Tools

### Enabled Tools
- [ ] CodeQL for code scanning
- [ ] Dependabot for dependency updates
- [ ] Secret scanning
- [ ] Branch protection rules
- [ ] Required status checks

### Recommended Tools
- [ ] Git hooks for pre-commit secret detection
- [ ] IDE plugins for security linting
- [ ] Regular penetration testing
- [ ] Third-party security audit (annual)

## Training & Awareness

### Team Training
- [ ] Security best practices documentation shared
- [ ] Team trained on secret handling
- [ ] Incident response procedures reviewed
- [ ] Regular security awareness sessions

### External Resources
- [ ] GitHub Security Best Practices: https://docs.github.com/security
- [ ] OWASP Top 10: https://owasp.org/www-project-top-ten/
- [ ] Linear Security: https://linear.app/security

---

## Review Schedule

- **Daily**: Monitor workflow execution
- **Weekly**: Review security logs
- **Monthly**: Complete monthly tasks checklist
- **Quarterly**: Complete quarterly tasks and rotate secrets
- **Annually**: Third-party security audit

## Sign-Off

**Last Review Date**: ___________  
**Reviewed By**: ___________  
**Next Review Date**: ___________  
**Status**: [ ] Pass [ ] Fail [ ] Needs Attention

**Notes**:
___________________________________________________________
___________________________________________________________
___________________________________________________________

---

**Version**: 1.0  
**Last Updated**: 2025-10-04  
**Owner**: Stephen Thompson