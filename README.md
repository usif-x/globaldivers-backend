# Top Divers Backend API

A FastAPI-based backend service for Top Divers, providing RESTful APIs for dive center management, course booking, trip reservations, and payment processing.

## Features

- 🚀 **FastAPI** - High performance web framework
- 🔐 **JWT Authentication** - Secure user and admin authentication
- 🗄️ **PostgreSQL** - Relational database with SQLAlchemy ORM
- 🎯 **Redis** - Caching and rate limiting
- 📊 **Rate Limiting** - API rate limiting with SlowAPI
- 📝 **Automatic Documentation** - Interactive API docs at `/docs`
- 🐳 **Docker Support** - Containerized development and deployment
- 🧪 **Alembic Migrations** - Database schema migrations
- 💳 **Payment Integration** - EasyKash payment gateway integration

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)

### Using Docker (Recommended)

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd Topdivers-backend
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services**

   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Local Development

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

3. **Run database migrations**

   ```bash
   alembic upgrade head
   ```

4. **Start the development server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

Required environment variables (see `.env.example` for full list):

```bash
# Application
ENVIRONMENT=development
DEBUG=true
PORT=8000

# Database
DB_ENGINE=postgresql
DB_NAME=Top_divers
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=password
DB_REDIS_URI=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-must-be-at-least-32-characters
JWT_ALGORITHM=HS256

# Admin
ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=adminpassword123

# Payment
EASYKASH_PRIVATE_KEY=your_private_key
EASYKASH_SECRET_KEY=your_secret_key

# CORS
CORS_ORIGIN=http://localhost:3000
```

## Development

### Database Migrations

Create new migration:

```bash
alembic revision --autogenerate -m "migration_description"
```

Apply migrations:

```bash
alembic upgrade head
```

## Deployment

### Production Deployment

1. Set `ENVIRONMENT=production` in your environment variables
2. Ensure `DEBUG=false` for production
3. Use proper SSL certificates
4. Configure production database connection
5. Set strong JWT secret keys

### Docker Production

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Email: yousseifmuhammed@gmail.com

## API Documentation

Interactive API documentation is available at `/docs` when the application is running. The documentation includes:

- All available endpoints
- Request/response schemas
- Authentication requirements
- Try-it-out functionality

## Health Check

The application includes a health check endpoint at `/health` that returns:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000",
  "version": "1.0.0"
}
```
