"""Command to manage database migrations."""

def run():
    """Run all database migrations."""
    from fitler.database import db, migrate_tables
    from fitler.metadata import ActivityMetadata
    from fitler.provider_sync import ProviderSync
    
    print("Running database migrations...")
    
    try:
        migrate_tables([ActivityMetadata, ProviderSync])
        print("Successfully migrated database tables:")
        print("- ActivityMetadata")
        print("- ProviderSync")
    except Exception as e:
        print(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    run()
