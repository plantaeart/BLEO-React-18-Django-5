# Django MongoDB API

This project is a Django-based API that interacts with a MongoDB database. It provides a structured way to manage data and expose it through RESTful endpoints.

## Project Structure

```
django-mongodb-api
├── api                # Contains the API application
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── config             # Contains project configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── utils              # Contains utility functions
│   ├── __init__.py
│   └── mongodb_utils.py
├── manage.py          # Command-line utility for the project
├── requirements.txt   # Project dependencies
├── .env               # Environment variables
└── README.md          # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd django-mongodb-api
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory and add your MongoDB connection string and any other necessary environment variables.

5. **Run migrations:**
   ```
   python manage.py migrate
   ```

6. **Start the development server:**
   ```
   python manage.py runserver
   ```

## Usage

You can interact with the API endpoints defined in the `api/urls.py` file. Use tools like Postman or curl to send requests to the server.

## Testing

To run tests for the API application, use the following command:
```
python manage.py test api
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.