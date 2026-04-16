# LangFuse Self-Hosted Setup Guide

This guide explains how to set up a self-hosted LangFuse instance for tracing your LLM applications.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start with Podman Compose](#quick-start-with-podman-compose)
- [Manual Setup](#manual-setup)
- [Configuration](#configuration)
- [Creating API Keys](#creating-api-keys)
- [Connecting Your Application](#connecting-your-application)
- [Troubleshooting](#troubleshooting)
- [Comparison with TraceLoop](#comparison-with-traceloop)

## Overview

LangFuse is an open-source LLM engineering platform that provides:
- **Trace Visualization**: See detailed traces of your LLM calls
- **Cost Tracking**: Monitor token usage and costs
- **Prompt Management**: Version and manage your prompts
- **Evaluation**: Score and evaluate LLM outputs
- **Self-Hosted**: Full control over your data

This project supports LangFuse as an alternative or complement to TraceLoop.

## Prerequisites

### For Podman Compose Setup (Recommended)
- **Podman** and **Podman Compose** installed
  ```bash
  # macOS (using Homebrew)
  brew install podman podman-compose
  
  # Initialize Podman machine (first time only)
  podman machine init
  podman machine start
  ```

### For Manual Setup
- **PostgreSQL 15+** database
- **Node.js 18+** (for running LangFuse)
- At least **2GB RAM** available
- **Port 3000** available for LangFuse UI

## Quick Start with Podman Compose

### 1. Start LangFuse Stack

The project includes a `compose.yml` file that sets up everything you need:

```bash
# Start LangFuse and PostgreSQL
podman-compose up -d

# Check status
podman-compose ps

# View logs
podman-compose logs -f langfuse
```

### 2. Access LangFuse UI

Once the containers are running:

1. Open your browser to: **http://localhost:3000**
2. You'll see the LangFuse welcome screen
3. Create your first account (this becomes the admin account)

### 3. Create Your First Project

1. After logging in, click **"Create Project"**
2. Give it a name (e.g., "OpenTelemetry Testing")
3. Click **"Create"**

### 4. Generate API Keys

1. In your project, go to **Settings** → **API Keys**
2. Click **"Create new API keys"**
3. Give it a name (e.g., "Development")
4. Copy the keys immediately (they won't be shown again):
   - **Public Key**: `pk-lf-...`
   - **Secret Key**: `sk-lf-...`

### 5. Configure Your Application

Add these to your `.env` file:

```bash
# Choose LangFuse as your tracing backend
TRACING_BACKEND=langfuse

# LangFuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=http://localhost:3000
```

### 6. Start Your Application

```bash
# Start the Flask application
uv run python run.py
```

### 7. Generate Some Traces

```bash
# Test the LLM endpoint
curl -X POST http://localhost:5000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!", "model": "gpt-3.5-turbo"}'
```

### 8. View Traces in LangFuse

1. Go back to **http://localhost:3000**
2. Navigate to **Traces** in the sidebar
3. You should see your traces appearing!

## Manual Setup

If you prefer not to use Podman Compose, you can set up LangFuse manually.

### 1. Set Up PostgreSQL

```bash
# Install PostgreSQL (macOS)
brew install postgresql@15

# Start PostgreSQL
brew services start postgresql@15

# Create database and user
psql postgres -c "CREATE DATABASE langfuse;"
psql postgres -c "CREATE USER langfuse WITH PASSWORD 'your_password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE langfuse TO langfuse;"
```

### 2. Install LangFuse

```bash
# Clone LangFuse repository
git clone https://github.com/langfuse/langfuse.git
cd langfuse

# Install dependencies
npm install

# Build the application
npm run build
```

### 3. Configure LangFuse

Create a `.env` file in the LangFuse directory:

```bash
# Database
DATABASE_URL=postgresql://langfuse:your_password@localhost:5432/langfuse

# Authentication
NEXTAUTH_SECRET=your-random-secret-min-32-chars
NEXTAUTH_URL=http://localhost:3000

# Encryption
SALT=your-random-salt

# Optional: Disable telemetry
TELEMETRY_ENABLED=0
```

### 4. Run Database Migrations

```bash
npm run db:migrate
```

### 5. Start LangFuse

```bash
npm run start
```

LangFuse will be available at **http://localhost:3000**.

## Configuration

### Environment Variables

The `compose.yml` file includes these key configuration options:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://langfuse:password@postgres:5432/langfuse` |
| `NEXTAUTH_SECRET` | Secret for NextAuth (min 32 chars) | `change_me_to_random_string_min_32_chars` |
| `NEXTAUTH_URL` | Public URL of LangFuse | `http://localhost:3000` |
| `SALT` | Salt for encryption | `change_me_to_random_string` |
| `TELEMETRY_ENABLED` | Send usage data to LangFuse team | `0` (disabled) |

### Security Recommendations

**⚠️ IMPORTANT**: Before deploying to production:

1. **Change all default passwords and secrets**:
   ```bash
   # Generate secure random strings
   openssl rand -base64 32  # For NEXTAUTH_SECRET
   openssl rand -base64 16  # For SALT
   ```

2. **Update PostgreSQL password** in both services

3. **Use HTTPS** for production deployments:
   ```bash
   NEXTAUTH_URL=https://langfuse.yourdomain.com
   ```

4. **Configure email** for password resets (optional):
   ```bash
   EMAIL_FROM_ADDRESS=noreply@yourdomain.com
   SMTP_CONNECTION_URL=smtp://username:password@smtp.example.com:587
   ```

### Persistent Data

The compose file creates a named volume `langfuse_db` for PostgreSQL data. This ensures your data persists across container restarts.

To backup your data:
```bash
# Backup database
podman exec langfuse-postgres pg_dump -U langfuse langfuse > langfuse_backup.sql

# Restore database
podman exec -i langfuse-postgres psql -U langfuse langfuse < langfuse_backup.sql
```

## Creating API Keys

### Via UI (Recommended)

1. Log in to LangFuse at **http://localhost:3000**
2. Select or create a project
3. Go to **Settings** → **API Keys**
4. Click **"Create new API keys"**
5. Name your key set (e.g., "Development", "Production")
6. **Copy both keys immediately** - they won't be shown again!

### Key Types

- **Public Key** (`pk-lf-...`): Safe to use in client-side code
- **Secret Key** (`sk-lf-...`): Keep secure, use only server-side

### Multiple Environments

Create separate key sets for different environments:
- **Development**: For local testing
- **Staging**: For pre-production testing
- **Production**: For production use

## Connecting Your Application

### Option 1: LangFuse Only

```bash
# .env
TRACING_BACKEND=langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

### Option 2: Both LangFuse and TraceLoop

```bash
# .env
TRACING_BACKEND=traceloop,langfuse

# TraceLoop Configuration
TRACELOOP_API_KEY=your_traceloop_key

# LangFuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

This sends traces to both platforms simultaneously!

## Troubleshooting

### LangFuse Container Won't Start

**Check logs**:
```bash
podman-compose logs langfuse
```

**Common issues**:
- Port 3000 already in use: Change port in `compose.yml`
- Database not ready: Wait for PostgreSQL health check to pass
- Missing environment variables: Check all required vars are set

### Can't Connect to PostgreSQL

```bash
# Check PostgreSQL is running
podman-compose ps postgres

# Check PostgreSQL logs
podman-compose logs postgres

# Test connection manually
podman exec -it langfuse-postgres psql -U langfuse -d langfuse
```

### Application Can't Connect to LangFuse

**Check connectivity**:
```bash
# Test LangFuse health endpoint
curl http://localhost:3000/api/public/health
```

**Verify configuration**:
- Ensure `LANGFUSE_HOST` matches where LangFuse is running
- Check API keys are correct (no extra spaces)
- Verify `TRACING_BACKEND` includes `langfuse`

### No Traces Appearing

1. **Check application logs** for errors
2. **Verify API keys** are correct
3. **Check LangFuse logs**:
   ```bash
   podman-compose logs -f langfuse
   ```
4. **Test with a simple trace**:
   ```bash
   curl -X POST http://localhost:5000/api/llm/complete \
     -H "Content-Type: application/json" \
     -d '{"prompt": "test", "model": "gpt-3.5-turbo"}'
   ```

### Reset Everything

If you need to start fresh:

```bash
# Stop and remove containers
podman-compose down

# Remove volumes (⚠️ deletes all data)
podman volume rm langfuse_db

# Start fresh
podman-compose up -d
```

## Comparison with TraceLoop

### LangFuse (Self-Hosted)

**Pros:**
- ✅ **Full data control** - Your data never leaves your infrastructure
- ✅ **No subscription costs** - Open source and free
- ✅ **Works offline** - No internet required
- ✅ **Customizable** - Modify to fit your needs
- ✅ **Privacy** - Ideal for sensitive data

**Cons:**
- ❌ **Setup required** - Need to deploy and maintain
- ❌ **Infrastructure costs** - Server/hosting costs
- ❌ **Maintenance** - Updates, backups, monitoring

### TraceLoop (Cloud)

**Pros:**
- ✅ **Zero setup** - Just add API key
- ✅ **Managed service** - No maintenance needed
- ✅ **Always available** - High availability
- ✅ **Quick start** - Running in minutes

**Cons:**
- ❌ **Subscription costs** - Monthly fees
- ❌ **Data sent to third-party** - Privacy concerns
- ❌ **Internet required** - Can't work offline
- ❌ **Less control** - Limited customization

### When to Use Each

**Use LangFuse if:**
- You need full control over your data
- You're working with sensitive information
- You want to avoid subscription costs
- You need offline capabilities
- You want to customize the platform

**Use TraceLoop if:**
- You want the fastest setup
- You prefer managed services
- You don't want to maintain infrastructure
- You're okay with cloud-hosted data
- You want guaranteed uptime

**Use Both if:**
- You're migrating between platforms
- You want redundancy
- You're evaluating which to use long-term
- You want different backends for dev/prod

## Next Steps

1. **Explore LangFuse Features**:
   - Prompt management
   - Cost tracking
   - Evaluation scores
   - User feedback

2. **Set Up Production Deployment**:
   - Use HTTPS
   - Configure proper secrets
   - Set up backups
   - Monitor performance

3. **Integrate with Your Workflow**:
   - Add custom metadata to traces
   - Set up alerts
   - Create dashboards
   - Export data for analysis

## Additional Resources

- [LangFuse Documentation](https://langfuse.com/docs)
- [LangFuse GitHub](https://github.com/langfuse/langfuse)
- [OpenTelemetry Integration](https://langfuse.com/docs/integrations/opentelemetry)
- [Self-Hosting Guide](https://langfuse.com/docs/deployment/self-host)
- [API Reference](https://langfuse.com/docs/api)

## Support

- **LangFuse Issues**: [GitHub Issues](https://github.com/langfuse/langfuse/issues)
- **LangFuse Discord**: [Join Community](https://discord.gg/7NXusRtqYU)
- **Project Issues**: See main README.md

---

**Ready to start tracing?** Follow the [Quick Start](#quick-start-with-podman-compose) guide above!