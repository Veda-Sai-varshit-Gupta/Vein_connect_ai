"""
Notification Routes
====================
GET    /notifications/               user's notification list
GET    /notifications/unread-count
PATCH  /notifications/{id}/read
PATCH  /notifications/read-all
"""

from uuid import UUID
from fastapi import APIRouter, Query
from app.dependencies import CurrentUser, DbSession, Pagination
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.services.notification_service import NotificationService

router = APIRouter()
notification_service = NotificationService()


@router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
    unread_only: bool = Query(default=False),
):
    """Get notification inbox for the current user."""
    return await notification_service.get_notifications(
        db, current_user.id,
        skip=pagination.offset,
        limit=pagination.page_size,
        unread_only=unread_only,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(current_user: CurrentUser, db: DbSession):
    count = await notification_service.get_unread_count(db, current_user.id)
    return UnreadCountResponse(count=count)


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    await notification_service.mark_read(db, notification_id, current_user.id)
    return {"message": "Marked as read"}


@router.patch("/read-all")
async def mark_all_read(current_user: CurrentUser, db: DbSession):
    await notification_service.mark_all_read(db, current_user.id)
    return {"message": "All notifications marked as read"}
