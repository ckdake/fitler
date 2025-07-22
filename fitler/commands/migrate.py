"""Command to manage database migrations."""

def run():
    """Run database migrations."""
    print("Running database migrations...")
    
    try:
        from fitler.activity import Activity
        from fitler.provider_sync import ProviderSync
        from fitler.database import migrate_tables
        
        migrate_tables([Activity, ProviderSync])
        
        print("Successfully migrated database tables:")
        print("- Activity")
        print("- ProviderSync")
    except Exception as e:
        print(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run()
