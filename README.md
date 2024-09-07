# web-algaeid-monitoring
API System for Collecting Gas Data Sensor

## Installation
To install and run the web-algaeid-monitoring project, follow these steps:

1. Clone the repository to your local machine:

    ```shell
    git clone https://github.com/riparuk/web-algaeid-monitoring.git
    ```

2. Navigate to the project directory:

    ```shell
    cd web-algaeid-monitoring
    ```

3. Create a virtual environment and activate it:

    ```shell
    python3 -m venv venv
    source venv/bin/activate
    ```

4. Install the required dependencies:

    ```shell
    pip install -r requirements.txt
    ```

5. Copy `.env.example` to `.env` and fill the key

## Running the Application

To run the web-algaeid-monitoring project, execute the following command:

```shell
fastapi dev app/main.py
```

This will start the FastAPI development server and reload the application whenever changes are made.

You can now access the API at `http://localhost:8000`.

## Running with Uvicorn and Logging

To run the application using uvicorn and save logs to a file, use the following command:

```shell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload >> txt.log 2>&1
```

This command will start the FastAPI server, and all logs (including stdout and stderr) will be saved to txt.log.