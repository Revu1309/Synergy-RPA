"""Preferred Assets Management Module"""

from database.connection import create_connection, get_cursor, is_postgres

class PreferredAssetsManager:
    """Manage user preferred cryptocurrency assets."""
    
    @staticmethod
    def create_table():
        """Create the preferred_assets table if it doesn't exist."""
        conn = create_connection()
        if conn:
            cursor = get_cursor(conn)
            if is_postgres(conn):
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS preferred_assets (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(10) NOT NULL UNIQUE,
                        name VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS preferred_assets (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        symbol VARCHAR(10) NOT NULL UNIQUE,
                        name VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            conn.commit()
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_all_assets():
        """Get all preferred assets."""
        # Hyper-resilience: Ensure table exists and is seeded
        PreferredAssetsManager.create_table()
        PreferredAssetsManager.initialize_default_assets()
        
        conn = create_connection()
        if not conn:
            return []
        
        try:
            cursor = get_cursor(conn)
            cursor.execute("SELECT id, symbol, name FROM preferred_assets ORDER BY symbol ASC")
            assets = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [{'id': a[0], 'symbol': a[1], 'name': a[2]} for a in assets]
        except Exception as e:
            print(f"Error getting assets: {e}")
            return []
    
    @staticmethod
    def add_asset(symbol, name):
        """Add a new preferred asset."""
        # Hyper-resilience: Ensure table exists and is seeded
        PreferredAssetsManager.create_table()
        PreferredAssetsManager.initialize_default_assets()
        
        conn = create_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = get_cursor(conn)
            cursor.execute(
                "INSERT INTO preferred_assets (symbol, name) VALUES (%s, %s)",
                (symbol.upper(), name)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Asset added successfully"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def update_asset(asset_id, symbol, name):
        """Update a preferred asset."""
        conn = create_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = get_cursor(conn)
            cursor.execute(
                "UPDATE preferred_assets SET symbol = %s, name = %s WHERE id = %s",
                (symbol.upper(), name, asset_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Asset updated successfully"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def delete_asset(asset_id):
        """Delete a preferred asset."""
        conn = create_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = get_cursor(conn)
            cursor.execute("DELETE FROM preferred_assets WHERE id = %s", (asset_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Asset deleted successfully"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_symbols_list():
        """Get list of all preferred asset symbols."""
        assets = PreferredAssetsManager.get_all_assets()
        return [asset['symbol'] for asset in assets]
    
    @staticmethod
    def clear_all_assets():
        """Clear all preferred assets from the table."""
        conn = create_connection()
        if conn:
            cursor = get_cursor(conn)
            try:
                cursor.execute("DELETE FROM preferred_assets")
                conn.commit()
                print("Cleared all preferred assets")
            except Exception as e:
                print(f"Error clearing assets: {e}")
            finally:
                cursor.close()
                conn.close()
    
    @staticmethod
    def initialize_default_assets():
        """Initialize with default assets if table is empty."""
        conn = create_connection()
        if not conn:
            return
            
        try:
            cursor = get_cursor(conn)
            # Check if empty WITHOUT calling get_all_assets (to avoid recursion)
            cursor.execute("SELECT COUNT(*) FROM preferred_assets")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Major crypto assets in the $0.01-$1 price range
                default_assets = [
                    ('XLM', 'Stellar Lumens'),
                    ('TRX', 'TRON'),
                    ('ADA', 'Cardano'),
                    ('DOGE', 'Dogecoin'),
                    ('VET', 'VeChain'),
                    ('ALGO', 'Algorand'),
                    ('XTZ', 'Tezos'),
                    ('ZIL', 'Zilliqa'),
                    ('ONE', 'Harmony One'),
                    ('GRT', 'The Graph'),
                    ('LRC', 'Loopring'),
                    ('ICP', 'Internet Computer'),
                    ('ARB', 'Arbitrum'),
                    ('OP', 'Optimism'),
                    ('APE', 'ApeCoin'),
                ]
                
                for symbol, name in default_assets:
                    PreferredAssetsManager.add_asset(symbol, name)
                
                print(f"Initialized {len(default_assets)} default cryptocurrency assets")
                conn.commit()
        except Exception as e:
            print(f"Error seeding assets: {e}")
        finally:
            cursor.close()
            conn.close()
