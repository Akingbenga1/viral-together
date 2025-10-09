import os
import uuid
from sqlalchemy import create_engine, text


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL environment variable is not set")

    engine = create_engine(database_url, future=True)

    updated_promotions = 0
    updated_collaborations = 0

    with engine.begin() as conn:
        # Promotions: set uuid for NULLs
        result = conn.execute(text("SELECT id FROM promotions WHERE uuid IS NULL"))
        promotion_ids = [row[0] for row in result]
        for pid in promotion_ids:
            conn.execute(
                text("UPDATE promotions SET uuid = :uuid WHERE id = :id"),
                {"uuid": str(uuid.uuid4()), "id": pid},
            )
            updated_promotions += 1

        # Collaborations: set uuid for NULLs
        result = conn.execute(text("SELECT id FROM collaborations WHERE uuid IS NULL"))
        collaboration_ids = [row[0] for row in result]
        for cid in collaboration_ids:
            conn.execute(
                text("UPDATE collaborations SET uuid = :uuid WHERE id = :id"),
                {"uuid": str(uuid.uuid4()), "id": cid},
            )
            updated_collaborations += 1

    print(
        {
            "updated_promotions": updated_promotions,
            "updated_collaborations": updated_collaborations,
        }
    )


if __name__ == "__main__":
    main()


