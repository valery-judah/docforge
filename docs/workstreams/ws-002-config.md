For a Dockerized FastAPI app with many configuration parameters, I would think about it in **layers**, not just “where do I put `.env`”.

## 1. Keep one typed configuration boundary inside the app

Do not read `os.environ` everywhere. Create one `Settings` object and inject it where needed.

FastAPI’s own docs recommend Pydantic Settings for external settings such as database URLs, secret keys, email credentials, and other values that vary by environment. They also mention `.env` support, dependency overrides for tests, and `@lru_cache` for avoiding repeated settings loading. ([FastAPI][1]) Pydantic Settings can load from environment variables and secrets files, with typed fields and defaults. ([Pydantic][2])

Example:

```python
from functools import lru_cache
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
        secrets_dir="/run/secrets",  # useful for Docker/K8s mounted secrets
    )

    environment: str = "local"
    debug: bool = False

    database_url: PostgresDsn
    redis_url: RedisDsn | None = None

    log_level: str = "INFO"
    request_timeout_seconds: int = Field(default=30, ge=1, le=300)

    jwt_secret: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

This gives you one place for validation, defaults, names, documentation, and test overrides.

## 2. Classify configuration by type

A useful split:

| Type                       | Examples                                                       | Recommended storage                                            |
| -------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------- |
| Build-time config          | Python version, OS packages, baked-in static assets            | Dockerfile / image build args                                  |
| Runtime non-secret config  | log level, feature flags, hostnames, limits, queue names       | env vars, ConfigMap, Helm values, deployment manifest          |
| Runtime secrets            | DB password, API keys, JWT signing secret, private keys        | secret manager, Kubernetes Secret, Docker secret, mounted file |
| Large structured config    | routing rules, policy files, ML model metadata, JSON/YAML maps | mounted config file, object storage, volume, database          |
| Dynamic operational config | kill switches, feature rollout %, tenant overrides             | config service, database, feature-flag service                 |

The biggest mistake is treating all of these as the same thing.

## 3. Use environment variables for simple runtime config

The classic Twelve-Factor approach is to store deploy-specific config in environment variables rather than in code. The benefit is that the same image can be promoted across dev, staging, and production with different runtime configuration. ([Twelve-Factor App][3])

This works well for:

```text
APP_ENVIRONMENT=production
APP_LOG_LEVEL=INFO
APP_REQUEST_TIMEOUT_SECONDS=30
APP_DATABASE_URL=postgresql://...
```

But environment variables become painful when you have many nested, repeated, or structured settings. At that point, use env vars for simple scalar values and mounted files for structured config.

## 4. In Docker Compose: use `.env` for local/dev, secrets for sensitive values

For local development, `.env` plus `docker compose` is fine. Docker Compose supports environment variables and interpolation to make compose files reusable across environments. ([Docker Documentation][4])

For secrets, prefer Docker secrets instead of putting passwords directly in environment variables. Docker’s docs explicitly describe Compose secrets as a way to avoid exposing passwords and API keys via env vars. ([Docker Documentation][5])

Example shape:

```yaml
services:
  api:
    image: my-api:1.2.3
    environment:
      APP_ENVIRONMENT: production
      APP_LOG_LEVEL: INFO
      APP_DATABASE_URL: postgresql://app@db:5432/app
    secrets:
      - jwt_secret

secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

Then Pydantic can read `/run/secrets/jwt_secret`.

## 5. In Kubernetes: ConfigMaps for non-secrets, Secrets for secrets

In Kubernetes, the normal pattern is:

```text
ConfigMap  -> non-confidential config
Secret     -> passwords, tokens, keys
Deployment -> wires those into the container
```

Kubernetes ConfigMaps are intended for non-confidential key-value configuration and can be consumed as env vars, command-line args, or mounted files. They decouple environment-specific config from the container image. ([Kubernetes][6])

Kubernetes Secrets are intended for small sensitive values such as passwords, tokens, and keys. ([Kubernetes][7]) But Kubernetes also warns that Secrets are stored unencrypted in etcd by default unless encryption at rest is enabled, so you still need RBAC, encryption at rest, and careful access control. ([Kubernetes][7])

Typical deployment pattern:

```yaml
envFrom:
  - configMapRef:
      name: my-api-config
  - secretRef:
      name: my-api-secrets
```

For many config values, mounted config files can be cleaner than hundreds of env vars.

## 6. For cloud deployments: use managed secret/config services

In AWS, Azure, GCP, or similar platforms, a common mature pattern is:

```text
App image contains no environment-specific values.
Deployment system injects config.
Secrets live in a managed secret store.
Kubernetes/VM/task runtime mounts or exposes them to the app.
```

Examples of the pattern:

```text
AWS Secrets Manager / SSM Parameter Store
Google Secret Manager
Azure Key Vault
HashiCorp Vault
Doppler / 1Password / Akeyless / other secret stores
```

In Kubernetes, External Secrets Operator is often used to sync values from external secret systems such as AWS Secrets Manager, HashiCorp Vault, and Google Secret Manager into Kubernetes Secrets. ([External Secrets][8])

This is better than manually copying secrets into cluster YAML.

## 7. For isolated / air-gapped deployments

For isolated deployments, you usually cannot depend on a cloud secret manager at runtime. Common approaches are:

### A. Config bundle per environment

Ship a deployment package like:

```text
release/
  image.tar
  docker-compose.yml
  config/
    app.env
    app.yaml
  secrets/
    jwt_secret
    db_password
  checksums.txt
```

The customer/operator edits or provides the config before installation.

### B. Encrypted config in Git or artifact storage

Use encrypted files for secrets and decrypt during deployment. SOPS is a common tool here; it supports YAML, JSON, ENV, INI, and binary files and can encrypt with AWS KMS, GCP KMS, Azure Key Vault, age, or PGP. ([GitHub][9])

For isolated environments, `age` or PGP is often easier than cloud KMS.

### C. Local secret manager

For serious isolated deployments, run a local Vault or equivalent inside the isolated environment. The application still reads from mounted files or short-lived credentials, but the source of truth is local.

### D. Operator-provided secrets

In some enterprise/on-prem deployments, the app should not own secret generation at all. The installer asks for:

```text
DATABASE_URL
OIDC_CLIENT_SECRET
JWT_PRIVATE_KEY
SMTP_PASSWORD
```

and validates them before starting.

## 8. Use configuration-as-code for deployment values

For cloud/Kubernetes environments, avoid manually editing random `.env` files. Use one of:

```text
Helm values.yaml
Kustomize overlays
Terraform variables
Pulumi config
Ansible inventory/group_vars
GitOps repository
```

A good structure is:

```text
deploy/
  helm/
    values.yaml
    values-dev.yaml
    values-staging.yaml
    values-prod.yaml
```

But secrets should either be referenced from a secret manager or stored encrypted, not committed as plaintext.

## 9. Validate config at startup and fail fast

For many parameters, this is essential.

Good behavior:

```text
Application starts
Settings object loads
Types are validated
Required values are checked
Invalid combinations are rejected
App exits before accepting traffic
```

Bad behavior:

```text
App starts successfully
First real request fails because S3_BUCKET was missing
```

Examples of validation rules:

```python
from pydantic import model_validator


class Settings(BaseSettings):
    environment: str
    debug: bool = False
    sentry_dsn: str | None = None

    @model_validator(mode="after")
    def validate_prod(self):
        if self.environment == "production" and self.debug:
            raise ValueError("debug must be false in production")
        if self.environment == "production" and not self.sentry_dsn:
            raise ValueError("sentry_dsn is required in production")
        return self
```

## 10. Prefer config namespaces

With many parameters, naming matters.

Instead of:

```text
DB_HOST
DB_PORT
TIMEOUT
TOKEN
URL
```

Use:

```text
APP_DATABASE_HOST
APP_DATABASE_PORT
APP_HTTP_TIMEOUT_SECONDS
APP_AUTH_JWT_SECRET
APP_REDIS_URL
APP_OBSERVABILITY_LOG_LEVEL
```

This prevents collisions with platform-provided variables and makes the config self-documenting.

## 11. Make configuration observable, but never leak secrets

Expose a safe config summary at startup or in diagnostics:

```text
environment=production
log_level=INFO
database_host=db.internal
redis_enabled=true
feature_x_enabled=false
```

Never log:

```text
passwords
tokens
private keys
full DSNs with credentials
authorization headers
```

A good practice is to implement a redacted settings dump.

## 12. Practical recommendation for your case

For a FastAPI Docker app, I would use this default architecture:

```text
Application:
  Pydantic Settings as the only config interface

Local development:
  .env file
  docker compose override
  fake/dev secrets

Docker Compose isolated deployment:
  env_file for non-secrets
  Docker secrets or mounted files for secrets
  startup config validation

Kubernetes/cloud:
  ConfigMap for non-secrets
  Secret or External Secrets Operator for secrets
  Helm/Kustomize/Terraform for environment-specific values

Air-gapped/on-prem:
  versioned config bundle
  encrypted secrets with SOPS/age or local Vault
  installer/preflight validation
```

The core principle: **build one immutable Docker image, then inject environment-specific configuration at deployment time.** Your FastAPI code should know the schema and validation rules, but the deployment system should own the actual values.

[1]: https://fastapi.tiangolo.com/advanced/settings/ "Settings and Environment Variables - FastAPI"
[2]: https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/ "Settings Management | Pydantic Docs"
[3]: https://12factor.net/config?utm_source=chatgpt.com "Store config in the environment"
[4]: https://docs.docker.com/compose/how-tos/environment-variables/?utm_source=chatgpt.com "Environment variables in Compose"
[5]: https://docs.docker.com/compose/how-tos/use-secrets/?utm_source=chatgpt.com "Manage secrets securely in Docker Compose"
[6]: https://kubernetes.io/docs/concepts/configuration/configmap/ "ConfigMaps | Kubernetes"
[7]: https://kubernetes.io/docs/concepts/configuration/secret/ "Secrets | Kubernetes"
[8]: https://external-secrets.io/?utm_source=chatgpt.com "External Secrets Operator: Introduction"
[9]: https://github.com/getsops/sops?utm_source=chatgpt.com "getsops/sops: Simple and flexible tool for managing secrets"

