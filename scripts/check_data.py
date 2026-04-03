from database.connection import create_connection


def query_counts():
    conn = create_connection()
    if not conn:
        print('ERROR: Could not connect to database. Check environment variables.')
        return
    cursor = conn.cursor()

    queries = [
        ("crypto_assets", "SELECT COUNT(*), MAX(timestamp) FROM crypto_assets"),
        ("weather_data", "SELECT COUNT(*), MAX(timestamp) FROM weather_data"),
        ("weather_locations", "SELECT COUNT(*), MAX(updated_at) FROM weather_locations"),
    ]

    for name, q in queries:
        try:
            cursor.execute(q)
            row = cursor.fetchone()
            count = row[0] if row and row[0] is not None else 0
            latest = row[1] if row and row[1] is not None else 'N/A'
            print(f"{name}: count={count}, latest={latest}")
        except Exception as e:
            print(f"{name}: ERROR executing query: {e}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    query_counts()
