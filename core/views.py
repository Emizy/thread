from datetime import datetime

import pytz
import logging
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from traceback_with_variables import format_exc
from django.contrib.auth import authenticate, logout
from django.utils.timezone import make_aware
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from drf_psq import PsqMixin, Rule, psq
from core.models import User, Post, Comment
from core.serializer import UserSerializer, LoginFormSerializer, UserRegisterFormSerializer, PostSerializer, \
    PostFormSerializer, CommentFormSerializer, CommentSerializer
from services.base import BaseViewSet
from services.permissions import global_permission
from services.utility import error_message_formatter, get_tokens_for_user

logger = logging.getLogger('core')


def account_logout(request):
    try:
        logout(request)
    except Exception as ex:
        logger.error(f'Error occurred while logging user out due to {str(ex)}')
    return redirect('/api')


class AuthViewSet(ViewSet):
    serializer_class = UserSerializer
    permission_classes = [
        AllowAny,
    ]

    @staticmethod
    def get_user(username):
        try:
            user = User.objects.get(email=username)
            return user
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_data(request) -> dict:
        return request.data if isinstance(request.data, dict) else request.data.dict()

    @swagger_auto_schema(
        request_body=LoginFormSerializer,
        operation_description="",
        responses={},
        operation_summary="LOGIN ENDPOINT FOR ALL USERS",
    )
    @action(detail=False, methods=["post"], description="Login authentication")
    def login(self, request, *args, **kwargs):
        context = {"status": status.HTTP_200_OK}
        try:
            data = self.get_data(request)
            serializer = LoginFormSerializer(data=data)
            if serializer.is_valid():
                user = authenticate(request, username=data.get("username"), password=data.get("password"))
                if user:
                    user.last_login = make_aware(datetime.today(), timezone=pytz.utc)
                    user.save(update_fields=['last_login'])
                    context.update(
                        {
                            "data": UserSerializer(user).data,
                            "token": get_tokens_for_user(user)
                        }
                    )
                else:
                    context.update({'status': status.HTTP_400_BAD_REQUEST,
                                    'message': 'Invalid credentials, Kindly supply valid credentials'})
            else:
                context.update({'status': status.HTTP_400_BAD_REQUEST,
                                'errors': error_message_formatter(serializer_errors=serializer.errors)})
        except Exception as ex:
            context.update({"status": status.HTTP_400_BAD_REQUEST, "message": str(ex)})
        return Response(context, status=context["status"])

    @swagger_auto_schema(
        request_body=UserRegisterFormSerializer,
        operation_description="This endpoint handles creating new account for user",
        responses={},
        operation_summary="CREATE ACCOUNT",
    )
    @action(
        detail=False,
        methods=["post"],
        description="CREATE AN ACCOUNT",
    )
    def register(self, request, *args, **kwargs):
        context = {"status": status.HTTP_201_CREATED}
        try:
            data = self.get_data(request)
            serializer = UserRegisterFormSerializer(data=data)
            if serializer.is_valid():
                _ = serializer.create(validated_data=serializer.validated_data)
                context.update({'status': status.HTTP_201_CREATED, 'message': 'Account created successfully'})
            else:
                context.update({'errors': error_message_formatter(serializer_errors=serializer.errors),
                                'status': status.HTTP_400_BAD_REQUEST})
        except Exception as ex:
            context.update({'status': status.HTTP_400_BAD_REQUEST, 'message': 'Something went wrong while making '
                                                                              'provision for your account,Kindly '
                                                                              'try again'})
            logger.error(f'Something occurred while processing user account creation due to {str(ex)}')
            logger.error(format_exc(ex))
        return Response(context, status=context["status"])


class PostViewSet(BaseViewSet):
    serializer_class = PostSerializer
    serializer_form_class = PostFormSerializer
    queryset = Post.objects.prefetch_related('comments').all().order_by('-created_at')
    filterset_fields = ['user__id', 'publish']
    search_fields = ['title', ]
    logger_name = 'core'

    def get_object(self):
        return get_object_or_404(Post, id=self.kwargs.get('pk'))

    def get_queryset(self):
        return self.queryset

    @swagger_auto_schema(
        operation_description="Display available post",
        operation_summary="List all available post",
        manual_parameters=[
            openapi.Parameter(
                "user__id",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Filter by user id",
            ), openapi.Parameter(
                "publish",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Filter by publish status",
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        context = {'status': status.HTTP_400_BAD_REQUEST}
        try:
            paginate = self.get_paginated_data(queryset=self.get_list(self.get_queryset()),
                                               serializer_class=self.serializer_class)
            context.update({"status": status.HTTP_200_OK, "message": "OK", "data": paginate})
        except Exception as ex:
            context.update({'status': status.HTTP_400_BAD_REQUEST, 'message': str(ex)})
            self.logger().error(f'Something went wrong while fetching user post due to {format_exc(ex)}')
        return Response(context, status=context['status'])

    @swagger_auto_schema(
        operation_description="Retrieve post information",
        operation_summary="Retrieve post information",
    )
    def retrieve(self, request, *args, **kwargs):
        context = {"status": status.HTTP_200_OK}
        try:
            context.update({"data": self.serializer_class(self.get_object()).data})
        except Exception as ex:
            context.update({"status": status.HTTP_400_BAD_REQUEST, "message": str(ex)})
        return Response(context, status=context["status"])

    @swagger_auto_schema(
        operation_description="Add a post",
        operation_summary="Add a post",
        request_body=PostFormSerializer
    )
    @method_decorator(global_permission(), name="dispatch")
    def create(self, request, *args, **kwargs):
        context = {'status': status.HTTP_201_CREATED}
        try:
            data = self.get_data(request)
            serializer = self.serializer_form_class(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.validated_data.update({'user': request.user})
                if Post.objects.filter(title=serializer.validated_data.get('title'), user=request.user).exists():
                    context.update({'status': status.HTTP_400_BAD_REQUEST,
                                    'message': 'Post with this title already exist inside your account'})
                    return Response(context, status=context['status'])
                instance = serializer.create(validated_data=serializer.validated_data)
                context.update({'data': self.serializer_class(instance).data, 'message': 'Post created'})
            else:
                context.update({
                    'status': status.HTTP_400_BAD_REQUEST,
                    'errors': error_message_formatter(serializer.errors)
                })
        except Exception as ex:
            context.update({'status': status.HTTP_400_BAD_REQUEST,
                            'message': 'Something went wrong while creating post,Kindly try again'})
            self.logger().error(f'<{self.request.user}> error creating post due to {str(ex)}')
        return Response(context, status=context['status'])

    @swagger_auto_schema(
        operation_description="Update a post",
        operation_summary="Update a post",
        request_body=PostFormSerializer
    )
    @method_decorator(global_permission(), name="dispatch")
    def update(self, request, *args, **kwargs):
        context = {'status': status.HTTP_400_BAD_REQUEST}
        try:
            data = self.get_data(request)
            instance = self.get_object()
            serializer = self.serializer_form_class(data=data, instance=instance, context={'request': request})
            if instance.user.id != request.user.id:
                context.update({'status': status.HTTP_403_FORBIDDEN,
                                'message': 'You currently do not have access to this resource'})
                return Response(context, status=context['status'])
            if serializer.is_valid():
                instance = serializer.update(validated_data=serializer.validated_data, instance=instance)
                context.update(
                    {'data': self.serializer_class(instance).data, 'message': 'UPDATED',
                     'status': status.HTTP_200_OK})
            else:
                context.update({
                    'errors': error_message_formatter(serializer.errors),
                    'status': status.HTTP_400_BAD_REQUEST})
        except Exception as ex:
            self.logger().error(f'<{self.request.user}> Something went wrong while updating post due to {str(ex)}')
            context.update({'status': status.HTTP_400_BAD_REQUEST, 'message': str(ex)})
        return Response(context, status=context['status'])

    @swagger_auto_schema(
        operation_description="Delete blog post",
        operation_summary="Delete blog post"
    )
    @method_decorator(global_permission(), name="dispatch")
    def destroy(self, request, *args, **kwargs):
        context = {'status': status.HTTP_204_NO_CONTENT}
        try:
            instance = self.get_object()
            if instance.user.id != request.user.id:
                context.update({'status': status.HTTP_403_FORBIDDEN,
                                'message': 'You currently do not have access to this resource'})
                return Response(context, status=context['status'])
            instance.delete()
        except Exception as ex:
            context.update({'message': str(ex), 'status': status.HTTP_400_BAD_REQUEST})
            self.logger().error(f'Something went wrong while deleting a blog post {kwargs} due to {format_exc(ex)}')
        return Response(context, status=context['status'])


class PostCommentViewSet(BaseViewSet):
    queryset = Comment.objects.select_related('user', 'post', 'parent_comment').all().order_by('-timestamp')
    serializer_class = CommentSerializer
    serializer_form_class = CommentFormSerializer
    filterset_fields = ['post__id']
    logger_name = 'core'
    psq_rules = {
        ('create',): [
            Rule([IsAuthenticated])
        ]
    }

    def get_queryset(self):
        if self.request.GET.get('post__id') is None:
            return self.queryset.none()
        return self.queryset

    def get_object(self):
        return get_object_or_404(Comment, id=self.kwargs.get('pk'))

    @swagger_auto_schema(
        operation_description="Display all available post comment",
        operation_summary="List all available post comment",
        manual_parameters=[
            openapi.Parameter(
                "post__id",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Filter by post id",
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        context = {'status': status.HTTP_400_BAD_REQUEST}
        try:
            paginate = self.get_paginated_data(queryset=self.get_list(self.get_queryset()),
                                               serializer_class=self.serializer_class)
            context.update({"status": status.HTTP_200_OK, "message": "OK", "data": paginate})
        except Exception as ex:
            context.update({'status': status.HTTP_400_BAD_REQUEST, 'message': str(ex)})
            self.logger().error(
                f'<{self.request.user}> Something went wrong while fetching post comment due to {format_exc(ex)}')
        return Response(context, status=context['status'])

    @swagger_auto_schema(
        operation_description="Add a post comment",
        operation_summary="Add a post comment",
        request_body=CommentFormSerializer
    )
    @method_decorator(global_permission(), name="dispatch")
    def create(self, request, *args, **kwargs):
        context = {'status': status.HTTP_201_CREATED}
        try:
            data = self.get_data(request)
            serializer = self.serializer_form_class(data=data)
            if serializer.is_valid():
                serializer.validated_data.update({'user': request.user})
                instance = serializer.create(validated_data=serializer.validated_data)
                context.update({'data': self.serializer_class(instance).data, 'message': 'Comment created'})
            else:
                context.update({
                    'status': status.HTTP_400_BAD_REQUEST,
                    'errors': error_message_formatter(serializer.errors)
                })
        except Exception as ex:
            context.update({'status': status.HTTP_400_BAD_REQUEST,
                            'message': 'Something went wrong while adding comment,Kindly try again'})
            self.logger().error(f'<{self.request.user}> error adding comment due to {format_exc(ex)}')
        return Response(context, status=context['status'])

    @action(detail=True, methods=['get'], description='Fetch comment replies')
    def replies(self, request, *args, **kwargs):
        context = {'status': status.HTTP_200_OK}
        try:
            instance = self.get_object()
            queryset = self.queryset.filter(parent_comment=instance)
            context.update({'data': self.serializer_class(queryset, many=True).data})
        except Exception as ex:
            context.update({'status': status.HTTP_400_BAD_REQUEST,
                            'message': 'Something went wrong while adding comment,Kindly try again'})
            self.logger().error(f'<{self.request.user}> error fetching comment relies due to {format_exc(ex)}')
        return Response(context, status=context['status'])
