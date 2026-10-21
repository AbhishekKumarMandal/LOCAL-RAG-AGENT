import psycopg

DB_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "dbname": "local_rag_agent",
    "user": "rag_user",
    "password": "rag_password"
}


def get_connection():
    """
    Creates and returns a PostgreSQL connection.

    host:
        PostgreSQL is running on our local machine.

    port:
        5434 because Docker maps:

        localhost:5434
              ↓
        container:5432

    dbname:
        Database used by this project.
    """

    return psycopg.connect(
        **DB_CONFIG
    )