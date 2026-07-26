from db_service import db


async def get_user(email: str):
    user = await db.user.find_unique(
        where={
            'email': email
        }
    )

    return user
    