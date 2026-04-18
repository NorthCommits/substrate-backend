from fastapi import HTTPException, status


class AgentNotFoundException(HTTPException):
    def __init__(self, agent_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id '{agent_id}' not found"
        )


class AgentNameConflictException(HTTPException):
    def __init__(self, name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with name '{name}' already exists"
        )


class ContextNotFoundException(HTTPException):
    def __init__(self, context_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context with id '{context_id}' not found"
        )


class SubscriptionNotFoundException(HTTPException):
    def __init__(self, subscription_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with id '{subscription_id}' not found"
        )


class SubscriptionConflictException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subscription already exists for this agent and context type"
        )


class EmbeddingServiceException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service is currently unavailable"
        )