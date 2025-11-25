# Deployment Guide

This guide covers deploying AI-Scraper to various platforms.

## Prerequisites

- Docker and Docker Compose
- Domain name (for production)
- SSL certificate (for HTTPS)

## Environment Setup

1. Copy environment template:
```bash
cp backend/.env.example backend/.env
```

2. Update the `.env` file with your settings:
- `SECRET_KEY`: Generate a secure random key
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- Other settings as needed

## Development Deployment

```bash
# Start all services
docker-compose up --build

# Or start in detached mode
docker-compose up -d --build
```

## Production Deployment

### Option 1: Coolify (Recommended for self-hosting)

1. Create a new project in Coolify
2. Connect your Git repository
3. Add environment variables from `.env`
4. Deploy using Docker Compose

### Option 2: Render

1. Create a new Web Service
2. Connect your repository
3. Set build command: `docker-compose up --build`
4. Add environment variables

### Option 3: Railway

1. Create a new project
2. Connect repository
3. Add environment variables
4. Deploy

### Option 4: VPS Deployment

```bash
# Clone repository
git clone https://github.com/yourusername/ai-scraper.git
cd ai-scraper

# Setup environment
cp backend/.env.example backend/.env
# Edit backend/.env with your settings

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

## Database Setup

### PostgreSQL (Production)

The system will automatically create tables on first run. For production:

```bash
# Run migrations (if using Alembic)
docker-compose exec backend alembic upgrade head
```

### SQLite (Development)

SQLite is automatically configured for development and requires no setup.

## SSL/HTTPS Setup

### Using Let's Encrypt with Caddy

1. Install Caddy
2. Configure reverse proxy:

```
your-domain.com {
    reverse_proxy localhost:3000  # Frontend
    reverse_proxy localhost:8000/api/*  # Backend
}
```

### Using Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}
```

## Monitoring and Logging

### Health Checks

- Backend: `GET /api/health`
- Frontend: `GET /health` (nginx)
- Database: Connection test
- Redis: Connection test

### Log Management

Logs are written to:
- Backend: `backend/logs/app.log`
- Nginx: `/var/log/nginx/`
- PostgreSQL: Docker logs

### Monitoring

Consider setting up monitoring with:
- Prometheus + Grafana
- ELK Stack
- Cloud monitoring (AWS CloudWatch, Google Cloud Monitoring)

## Scaling

### Horizontal Scaling

1. **Frontend**: Can be served from CDN or multiple instances
2. **Backend**: Use multiple FastAPI instances behind load balancer
3. **Database**: Use connection pooling and read replicas
4. **Redis**: Use Redis Cluster for high availability

### Vertical Scaling

- Increase container resources
- Optimize database queries
- Add more scraper runner containers

## Backup Strategy

### Database Backups

```bash
# PostgreSQL backup
docker-compose exec db pg_dump -U ai_scraper ai_scraper > backup.sql

# SQLite backup
docker-compose exec backend cp /app/ai_scraper.db /app/backup_$(date +%Y%m%d_%H%M%S).db
```

### File Backups

```bash
# Backup generated scripts and outputs
tar -czf scripts_backup_$(date +%Y%m%d).tar.gz generated_scripts/ outputs/
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **Database**: Use strong passwords and network isolation
3. **API Keys**: Rotate regularly
4. **HTTPS**: Always use SSL in production
5. **Rate Limiting**: Implement proper rate limiting
6. **CORS**: Configure CORS properly for production
7. **Container Security**: Regularly update base images

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Verify database is running
   - Check network connectivity

2. **AI Generation Fails**
   - Verify OPENAI_API_KEY
   - Check API quota/billing
   - Check rate limits

3. **Frontend Not Loading**
   - Check nginx configuration
   - Verify build completed
   - Check CORS settings

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
docker-compose up
```

### Logs

```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

## Performance Optimization

1. **Database**: Add indexes for frequently queried fields
2. **Caching**: Implement Redis caching for frequently accessed data
3. **CDN**: Serve static assets from CDN
4. **Compression**: Enable gzip compression
5. **Database Connection Pooling**: Configure proper connection limits

## Maintenance

### Regular Tasks

1. **Database**: Regular backups and vacuum
2. **Logs**: Rotate and clean old logs
3. **Updates**: Keep Docker images updated
4. **Security**: Update dependencies regularly

### Update Procedure

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose up -d --build

# Run database migrations (if applicable)
docker-compose exec backend alembic upgrade head
```

## Support

For issues and questions:
- GitHub Issues: [Project Issues](https://github.com/yourusername/ai-scraper/issues)
- Documentation: [Project Wiki](https://github.com/yourusername/ai-scraper/wiki)
- Discord: [Community Server](https://discord.gg/yourserver)