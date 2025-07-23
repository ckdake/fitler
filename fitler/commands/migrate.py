"""Command to manage database migrations."""


def run():
    """Run database migrations."""
    print("Running database migrations...")

    try:
        from fitler.database import migrate_tables, get_all_models

        models = get_all_models()
        migrate_tables(models)

        print("Successfully migrated database tables:")
        for model in models:
            print(f"- {model.__name__}")
    except Exception as e:
        print(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    run()
