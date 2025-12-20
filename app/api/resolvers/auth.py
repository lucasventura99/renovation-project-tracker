# app/api/resolvers/auth.py
import strawberry
from strawberry.types import Info
from app.services.user_service import authenticate_user, generate_user_token, create_user
from app.models.user import UserRole

@strawberry.type
class AuthPayload:
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str

@strawberry.type
class AuthMutation:
    @strawberry.mutation
    async def login(self, info: Info, email: str, password: str) -> AuthPayload:
        # Access the database session from the context
        db = info.context["db"]
        
        user = await authenticate_user(db, email, password)
        if not user:
            raise Exception("Invalid credentials")
            
        token = generate_user_token(user)
        return AuthPayload(
            access_token=token, 
            user_id=user.id, 
            role=user.role.value
        )

    @strawberry.mutation
    async def register(self, info: Info, email: str, password: str, role: str) -> AuthPayload:
        db = info.context["db"]
        
        # Convert string input to Enum safely
        try:
            # We use .upper() to be forgiving if they send "contractor"
            user_role = UserRole(role.upper())
        except ValueError:
             raise Exception("Invalid role. Must be CONTRACTOR or HOMEOWNER")

        try:
            user = await create_user(db, email, password, user_role)
        except ValueError as e:
            raise Exception(str(e)) # "Email already registered"

        token = generate_user_token(user)
        
        return AuthPayload(
            access_token=token, 
            user_id=user.id, 
            role=user.role.value
        )