import strawberry
from typing import List, Optional
from datetime import datetime
from app.models.user import UserInDB
from app.models.payment import PaymentStatus
from app.core.deps import get_db

@strawberry.type
class User:
    id: str
    email: str
    is_active: bool
    created_at: str

@strawberry.type
class License:
    id: str
    user_id: str
    type: str
    features: List[str]
    status: str
    expires_at: str

@strawberry.type
class Payment:
    id: str
    user_id: str
    amount: float
    currency: str
    status: str
    provider: str
    created_at: str

@strawberry.type
class Query:
    @strawberry.field
    async def user(self, info, id: str) -> Optional[User]:
        db = get_db()
        user_data = await db.users.find_one({"_id": id})
        if user_data:
            return User(
                id=str(user_data["_id"]),
                email=user_data["email"],
                is_active=user_data["is_active"],
                created_at=user_data["created_at"].isoformat()
            )
        return None

    @strawberry.field
    async def licenses(self, info, user_id: str) -> List[License]:
        db = get_db()
        licenses = await db.licenses.find({"user_id": user_id}).to_list(None)
        return [
            License(
                id=str(license["_id"]),
                user_id=license["user_id"],
                type=license["type"],
                features=license["features"],
                status=license["status"],
                expires_at=license["expires_at"].isoformat()
            )
            for license in licenses
        ]

    @strawberry.field
    async def payments(self, info, user_id: str) -> List[Payment]:
        db = get_db()
        payments = await db.payments.find({"user_id": user_id}).to_list(None)
        return [
            Payment(
                id=str(payment["_id"]),
                user_id=payment["user_id"],
                amount=payment["amount"],
                currency=payment["currency"],
                status=payment["status"],
                provider=payment["provider"],
                created_at=payment["created_at"].isoformat()
            )
            for payment in payments
        ]

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_payment(
        self,
        info,
        user_id: str,
        amount: float,
        currency: str,
        provider: str
    ) -> Payment:
        db = get_db()
        payment_data = {
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "status": PaymentStatus.PENDING,
            "provider": provider,
            "created_at": datetime.now()
        }
        result = await db.payments.insert_one(payment_data)
        payment_data["_id"] = result.inserted_id
        
        return Payment(
            id=str(result.inserted_id),
            user_id=payment_data["user_id"],
            amount=payment_data["amount"],
            currency=payment_data["currency"],
            status=payment_data["status"],
            provider=payment_data["provider"],
            created_at=payment_data["created_at"].isoformat()
        )

    @strawberry.mutation
    async def update_license_status(
        self,
        info,
        license_id: str,
        status: str
    ) -> License:
        db = get_db()
        await db.licenses.update_one(
            {"_id": license_id},
            {"$set": {"status": status}}
        )
        
        license_data = await db.licenses.find_one({"_id": license_id})
        return License(
            id=str(license_data["_id"]),
            user_id=license_data["user_id"],
            type=license_data["type"],
            features=license_data["features"],
            status=license_data["status"],
            expires_at=license_data["expires_at"].isoformat()
        )

schema = strawberry.Schema(query=Query, mutation=Mutation)
