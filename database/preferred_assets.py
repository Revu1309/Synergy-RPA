"""Preferred Assets Management Module"""

from database.connection import create_connection

class PreferredAssetsManager:
    """Manage user preferred cryptocurrency assets."""
    
    @staticmethod
    def create_table():
        """Create the preferred_assets table if it doesn't exist."""
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
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
        conn = create_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
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
        conn = create_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = conn.cursor()
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
            cursor = conn.cursor()
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
            cursor = conn.cursor()
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
            cursor = conn.cursor()
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
        assets = PreferredAssetsManager.get_all_assets()
        
        if not assets:
            # Major crypto assets in the $0.01-$1 price range
            default_assets = [
                ('XLM', 'Stellar Lumens'),         # ~$0.08-0.12
                ('TRX', 'TRON'),                   # ~$0.05-0.10
                ('ADA', 'Cardano'),                # ~$0.35-0.50
                ('DOGE', 'Dogecoin'),              # ~$0.08-0.15
                ('VET', 'VeChain'),                # ~$0.02-0.05
                ('ALGO', 'Algorand'),              # ~$0.15-0.40
                ('XTZ', 'Tezos'),                  # ~$0.80-1.20
                ('ZIL', 'Zilliqa'),                # ~$0.02-0.05
                ('ONE', 'Harmony One'),            # ~$0.01-0.05
                ('GRT', 'The Graph'),              # ~$0.08-0.30
                ('LRC', 'Loopring'),               # ~$0.20-0.60
                ('ICP', 'Internet Computer'),      # ~$3-8 (some range overlap)
                ('ARB', 'Arbitrum'),               # ~$0.50-1.50
                ('OP', 'Optimism'),                # ~$0.50-1.50
                ('APE', 'ApeCoin'),                # ~$0.50-2.00
            ]
            
            for symbol, name in default_assets:
                PreferredAssetsManager.add_asset(symbol, name)
            
            print(f"Initialized {len(default_assets)} default cryptocurrency assets (price range: $0.01-$1)")

