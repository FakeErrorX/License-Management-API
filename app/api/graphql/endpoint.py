from fastapi import APIRouter, Depends
from strawberry.fastapi import GraphQLRouter
from app.api.graphql.schema import schema
from app.api.deps import get_current_user

# Create a GraphQL router with authentication
graphql_router = GraphQLRouter(
    schema,
    path="/graphql",
    context_getter=lambda: {"user": get_current_user()}
)

# Create an API router and include the GraphQL router
router = APIRouter()
router.include_router(graphql_router)
