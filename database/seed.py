"""
seed.py
========
Seeds the database with the three hardcoded ROPIAS users.
Run once on first deployment: python database/seed.py
Called automatically by the app factory on first startup if DB is empty.
"""

def seed_users(db, User):
    """Seeds the three founding users if they don't already exist."""

    if User.query.count() > 0:
        print("Database already seeded. Skipping.")
        return

    SEED_USERS = [
        {
            "id": 1,
            "full_name": "Rebecca Chege",
            "username": "rebecca.chege",
            "email": "rebeccachegee@gmail.com",
            "password_plain": "RainySeasonKenya@2024",
            "role": "admin",
            "phone": "+254700000001",
            "is_seeded": True,
            "greeting": "Welcome back, Rebecca. Here is the current advisory status across all monitored farms.",
            "avatar_initials": "RC"
        },
        {
            "id": 2,
            "full_name": "Rushion Chege",
            "username": "rushion.chege",
            "email": "rushionchegge@gmail.com",
            "password_plain": "NasaPower@Ropias2024",
            "role": "admin",
            "phone": "+254700000002",
            "is_seeded": True,
            "greeting": "Welcome back, Rushion. All ROPIAS systems are operational.",
            "avatar_initials": "RC"
        },
        {
            "id": 3,
            "full_name": "Francis Gachuri",
            "username": "francis.gachuri",
            "email": "francisgchegge@gmail.com",
            "password_plain": "Farmer@Kakamega2024",
            "role": "farmer",
            "phone": "+254798639575",
            "farm_latitude": 0.28,
            "farm_longitude": 34.75,
            "preferred_crop": "maize",
            "is_seeded": True,
            "greeting": "Habari Francis! Here is today's planting advisory for your farm in Kakamega.",
            "avatar_initials": "FG"
        }
    ]

    for u in SEED_USERS:
        user = User(
            full_name       = u["full_name"],
            username        = u["username"],
            email           = u["email"],
            role            = u["role"],
            phone           = u.get("phone"),
            is_seeded       = u["is_seeded"],
            greeting        = u["greeting"],
            avatar_initials = u["avatar_initials"],
            farm_latitude   = u.get("farm_latitude"),
            farm_longitude  = u.get("farm_longitude"),
            preferred_crop  = u.get("preferred_crop"),
            is_active       = True
        )
        user.set_password(u["password_plain"])
        db.session.add(user)

    db.session.commit()
    print("✅ Database seeded: Rebecca Chege, Rushion Chege, Francis Gachuri")
