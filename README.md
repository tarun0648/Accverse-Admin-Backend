# Accverse Admin Backend

**Live Website:** [https://accverse.com.au/](https://accverse.com.au/)

A Flask-based backend for the Accverse Admin Portal, providing secure JWT-authenticated APIs for managing users, tax forms, appointments, notifications, and more. This backend is designed for admin and client roles, with robust authentication, role-based access, and MySQL database integration.

## Features
- JWT-based authentication for admin and client users
- User, client, and appointment management
- Tax form upload, retrieval, and file management
- Notifications system (read, archive, unarchive, mark all read)
- Form payments and pricing configuration
- Booking configuration and service management
- Password reset via email for admins
- CORS support for frontend integration

## Tech Stack
- **Python 3**
- **Flask** (REST API framework)
- **MySQL** (database)
- **bcrypt** (password hashing)
- **PyJWT** (JWT authentication)
- **Flask-CORS** (CORS support)
- **python-dotenv** (environment variable management)

## Project Structure
```
app.py           # Main Flask app and API routes
methods.py       # Business logic and database operations
utils.py         # Utility functions, JWT, decorators, DB connection
config.py        # Configuration and environment variables
requirements.txt # Python dependencies
```

## Setup & Installation
1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Accverse-Admin-Backend-jwt_tryexcept_implemented
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables**
   - Copy `.env.example` to `.env` and set values, or set environment variables directly.
   - Key variables:
     - `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `MYSQL_PORT`
     - `UPLOAD_FOLDER`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASS`
     - `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES`

4. **Run the server**
   ```bash
   python app.py
   ```
   The server will start on `http://0.0.0.0:5000` by default.

## API Overview
- **Authentication**: `/api/login`, `/api/request-password-reset`, `/api/reset-password`
- **Users/Clients**: `/api/users`, `/api/clients`
- **Tax Forms**: `/api/tax-forms/user/<user_id>`, `/api/tax-forms/<form_id>`, `/api/tax-forms/user/<user_id>/type/<form_type>`, `/api/tax-form-files/<form_id>`
- **Appointments**: `/api/appointments`
- **Services**: `/api/services`, `/api/services/<service_id>`
- **Form Payments**: `/api/form-payments`, `/api/form-payments/user/<user_id>`
- **Pricing Configs**: `/api/form-pricing-configs`, `/api/form-pricing-configs/<config_id>`
- **Notifications**: `/api/notifications`, `/api/notifications/<notification_id>/read`, `/api/notifications/<notification_id>/archive`, `/api/notifications/<notification_id>/unarchive`, `/api/notifications/mark-all-read`
- **Booking Config**: `/api/booking-config`, `/api/booking-config/<config_id>`
- **File Uploads**: `/uploads/tax_forms/<filename>`, `/api/tax-form-files/blob/<file_id>`, `/api/tax-form-files/<form_id>/file/<file_name>`

Most endpoints require JWT authentication and/or admin role. See `app.py` for full details.

## Configuration
Configuration is managed via environment variables (see `config.py`). Example variables:
```env
MYSQL_HOST=localhost
MYSQL_USER=youruser
MYSQL_PASSWORD=yourpass
MYSQL_DB=yourdb
MYSQL_PORT=3306
UPLOAD_FOLDER=/opt/app/accverse-backend/uploads
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your@email.com
EMAIL_PASS=your-email-password
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRES=86400
```

## Security Notes
- Change all default secrets and credentials before deploying to production.
- Use strong, unique values for `JWT_SECRET_KEY` and database credentials.
- Ensure your email credentials are secure.

## License
Proprietary. All rights reserved. 
