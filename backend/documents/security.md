# Meridian Analytics — Security & Compliance

Meridian Analytics takes security seriously. We protect customer data with industry-standard encryption, rigorous compliance certifications, and a defense-in-depth security architecture.

## Certifications & Compliance

- **SOC 2 Type II**: Certified. Last audit completed Q4 2024 by Deloitte. Report available to Enterprise customers under NDA.
- **GDPR**: Fully compliant. Meridian acts as a data processor. We offer a signed Data Processing Agreement (DPA) to all customers.
- **CCPA**: Compliant. We support consumer data deletion requests via API and dashboard.
- **HIPAA**: Available on Enterprise plan with a signed Business Associate Agreement (BAA).
- **ISO 27001**: Certification in progress, expected Q2 2025.

## Encryption

- **At rest**: All data is encrypted using AES-256-GCM. Encryption keys are managed via AWS KMS with automatic rotation every 90 days.
- **In transit**: All connections use TLS 1.3. We enforce HSTS and support certificate pinning for mobile SDKs.
- **API keys**: Stored as bcrypt hashes. Raw keys are shown only once at creation time.

## Infrastructure Security

Meridian runs on AWS (us-east-1 and eu-west-1 regions) with the following security controls:

- **Network**: All services run in private VPCs. Public endpoints are fronted by AWS WAF and CloudFront.
- **Compute**: Kubernetes (EKS) with pod security policies, no root containers, read-only filesystems.
- **Access**: Engineer access requires SSO + hardware MFA. Production access is logged and auditable.
- **Monitoring**: 24/7 security monitoring via Datadog and CrowdStrike. Automated alerting for suspicious activity.

## Data Residency

- **US region**: Data stored in AWS us-east-1 (N. Virginia).
- **EU region**: Data stored in AWS eu-west-1 (Ireland). Available on Growth and Enterprise plans.
- Enterprise customers can request dedicated tenancy for additional isolation.

## Access Control

Meridian provides fine-grained access control for teams:

- **Roles**: Owner, Admin, Member, Viewer. Each role has different permissions for dashboards, API keys, and billing.
- **SSO**: SAML 2.0 and OIDC support (Enterprise plan). Integrates with Okta, Azure AD, Google Workspace, and OneLogin.
- **SCIM**: Automatic user provisioning and de-provisioning (Enterprise plan).
- **Audit logs**: All user actions (logins, dashboard changes, API key creation, data exports) are logged with timestamp, user, and IP address. Logs are retained for 2 years.

## Vulnerability Management

- **Penetration testing**: Annual third-party pen test by NCC Group. Remediation SLA: critical within 24 hours, high within 7 days.
- **Bug bounty**: We run a private bug bounty program via HackerOne. Contact security@meridian.io for access.
- **Dependency scanning**: Automated Snyk scans on every deploy. No known critical vulnerabilities in production dependencies.

## Incident Response

Meridian maintains a documented incident response plan:

1. **Detection**: Automated monitoring detects anomalies and triggers alerts.
2. **Triage**: On-call engineer assesses severity within 15 minutes.
3. **Communication**: Customers are notified via status page and email within 1 hour for Sev1 incidents.
4. **Resolution**: Target resolution times — Sev1: 4 hours, Sev2: 24 hours, Sev3: 72 hours.
5. **Post-mortem**: Published within 5 business days for all Sev1 and Sev2 incidents.

Status page: https://status.meridian.io

## Data Deletion

- Customers can delete their data at any time via the dashboard or API.
- Upon account cancellation, all data is purged within 30 days.
- We honor GDPR and CCPA deletion requests within 72 hours.
