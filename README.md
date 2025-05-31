# AVS Business Assistant Admin Panel

A comprehensive admin panel for managing AI voice assistant business operations, including user management, subscription billing, usage monitoring, and analytics.

## 🚀 Features

### Core Features
- **User Management System**: Registration, authentication, profile management
- **Subscription & Billing**: Multiple plans, payment processing, invoice generation
- **Usage Monitoring**: Real-time call tracking, analytics, usage limits
- **Admin Dashboard**: Comprehensive analytics and system monitoring
- **IPCC Integration**: AI voice assistant connection management

### Technical Features
- **Backend**: FastAPI with latest syntax and Pydantic v2
- **Frontend**: React with TypeScript and Material-UI
- **Database**: PostgreSQL for persistent data
- **Cache**: Redis for sessions and caching
- **Authentication**: JWT-based with role-based access control
- **Deployment**: Docker Compose for containerized deployment

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🛠️ Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd avs-admin-panel
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   docker-compose exec backend python -m app.initial_data
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🏗️ Architecture

```
avs-admin-panel/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality (auth, config)
│   │   ├── crud/           # Database operations
│   │   ├── db/             # Database configuration
│   │   ├── models/         # SQLAlchemy models
│   │   └── schemas/        # Pydantic schemas
│   ├── alembic/            # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── contexts/       # React contexts
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml      # Docker services configuration
└── .env                    # Environment variables
```

## 🔧 Development Setup

### Backend Development

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**
   ```bash
   # Start PostgreSQL and Redis with Docker
   docker-compose up -d postgres redis
   
   # Run migrations
   alembic upgrade head
   
   # Initialize data
   python -m app.initial_data
   ```

4. **Start development server**
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Development

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm start
   ```

## 📊 Database Schema

### Core Models

- **User**: User accounts with authentication
- **Plan**: Subscription plans with features and pricing
- **Subscription**: User subscriptions with billing information
- **Usage**: Call usage tracking and analytics

### Key Relationships

- User → Subscriptions (One-to-Many)
- Plan → Subscriptions (One-to-Many)
- User → Usage (One-to-Many)

## 🔐 Authentication & Authorization

### User Roles
- **Regular User**: Can manage own profile, view usage, manage subscriptions
- **Admin**: Full system access, user management, analytics

### Security Features
- JWT token-based authentication
- Password hashing with bcrypt
- Role-based access control
- Rate limiting
- CORS protection

## 📈 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login/access-token` - User login
- `POST /api/v1/auth/login/test-token` - Token validation

### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update profile
- `GET /api/v1/users/` - List users (Admin)
- `POST /api/v1/users/` - Create user (Admin)

### Plans
- `GET /api/v1/plans/` - List active plans
- `GET /api/v1/plans/with-stats` - Plans with statistics (Admin)
- `POST /api/v1/plans/` - Create plan (Admin)

### Subscriptions
- `GET /api/v1/subscriptions/me` - User subscriptions
- `POST /api/v1/subscriptions/` - Create subscription
- `POST /api/v1/subscriptions/{id}/cancel` - Cancel subscription

### Usage
- `GET /api/v1/usage/me` - User usage records
- `GET /api/v1/usage/analytics` - Usage analytics (Admin)
- `POST /api/v1/usage/` - Create usage record

### Dashboard
- `GET /api/v1/dashboard/user` - User dashboard
- `GET /api/v1/dashboard/admin` - Admin dashboard

### Billing
- `GET /api/v1/billing/invoices/me` - User invoices
- `POST /api/v1/billing/process-payment` - Process payment
- `GET /api/v1/billing/revenue/summary` - Revenue summary (Admin)

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=AVS Business Assistant Admin Panel
SECRET_KEY=your-secret-key

# Database
POSTGRES_SERVER=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=avs_admin

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password

# Payment (Stripe)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# IPCC Integration
IPCC_API_URL=https://your-ipcc-provider.com/api
IPCC_API_KEY=your-api-key
```

## 🚀 Deployment

### Production Deployment

1. **Update environment variables**
   ```bash
   # Set production values in .env
   SECRET_KEY=your-production-secret-key
   POSTGRES_PASSWORD=secure-password
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **Set up reverse proxy (Nginx)**
   ```bash
   # Configure SSL certificates
   # Set up domain routing
   ```

### Scaling Considerations

- Use managed PostgreSQL service (AWS RDS, Google Cloud SQL)
- Use Redis cluster for high availability
- Implement load balancing for multiple backend instances
- Use CDN for frontend assets

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📝 Default Credentials

**Admin User:**
- Email: admin@avs.com
- Password: admin123

**Default Plans:**
- Starter: $9.99/month (25 calls, 100 minutes)
- Basic: $29.99/month (100 calls, 500 minutes)
- Professional: $79.99/month (500 calls, 2000 minutes)
- Enterprise: $199.99/month (2000 calls, 10000 minutes)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact: support@avs.com

## 🔄 Updates

Check the CHANGELOG.md for recent updates and version history.
