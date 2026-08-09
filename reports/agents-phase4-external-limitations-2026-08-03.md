# Remaining external-provider limitations

- No production Cognito identities, model-provider credentials, RDS instance, MCP server, ServiceNow, SharePoint, Azure, or notification service was used.
- Browser tests use the isolated signed E2E boundary and contract-realistic API fixtures; live provider outcomes are not claimed.
- The local ignored OpenAI credential must be rotated by an authorized operator.
- Production configuration must keep `E2E_AUTH_ENABLED` unset/false. Enabling it with `APP_ENV=production` fails application startup.
