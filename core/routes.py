from rest_framework.routers import DefaultRouter

from core.views import AuthViewSet, PostViewSet, PostCommentViewSet

router = DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth-api")
router.register(r"post/comment", PostCommentViewSet, basename="comment-api")
router.register(r"post", PostViewSet, basename="post-api")
