# Secrets & Access Control Setup

## Environment Variables (.env.qdrant)

1. Copy template:
   ```bash
   cp .env.example .env.qdrant
   ```

2. Edit `.env.qdrant` with your Qdrant credentials:
   ```
   QDRANT_CLOUD_URL=https://your-cluster.qdrant.io:6333
   QDRANT_API_KEY=your-api-key
   ```

3. **NEVER commit `.env.qdrant` to git** (in .gitignore)

## Qdrant API Key Best Practices

- **Scope**: Use minimal permissions (read-only for queries, read-write for indexing)
- **Rotation**: Rotate keys quarterly or on team changes
- **Logging**: Never log API keys; sanitize logs before sharing
- **CI/CD**: Store credentials as GitHub Secrets, not in code

## Setup for Production

### Local Development
```bash
# Create .env.qdrant with dev credentials
cp .env.example .env.qdrant
# Edit and save (not committed)
```

### CI/CD (GitHub Actions)
1. Add secrets in GitHub repo settings:
   - `QDRANT_CLOUD_URL`
   - `QDRANT_API_KEY`

2. Use in workflows:
   ```yaml
   env:
     QDRANT_CLOUD_URL: ${{ secrets.QDRANT_CLOUD_URL }}
     QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
   ```

### Production Server
1. Set environment variables at deployment time:
   ```bash
   export QDRANT_CLOUD_URL=...
   export QDRANT_API_KEY=...
   python start_server.py
   ```

2. Or use `.env.qdrant` with restricted file permissions:
   ```bash
   chmod 600 .env.qdrant
   ```

## Audit

Check for accidental secrets:
```bash
# Scan for API keys in code
grep -r "qdrant_api_key\|QDRANT_API_KEY" . --include="*.py" --include="*.md"

# View committed secrets (if any)
git log -p --all -S "QDRANT_API_KEY"
```

