from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ViewSet

from services.pagination import CustomPaginator

import logging


class CustomFilter(DjangoFilterBackend):
    def get_filterset_kwargs(self, request, queryset, view):
        kwargs = super().get_filterset_kwargs(request, queryset, view)

        # merge filterset kwargs provided by view class
        if hasattr(view, "get_filterset_kwargs"):
            kwargs.update(view.get_filterset_kwargs())
        return kwargs


class AbstractBaseViewSet:
    custom_filter_class = CustomFilter()
    search_backends = SearchFilter()
    order_backend = OrderingFilter()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    paginator_class = CustomPaginator()

    @staticmethod
    def get_data(request) -> dict:
        """Returns a dictionary from the request"""
        return request.data if isinstance(request.data, dict) else request.data.dict()


class BaseViewSet(ViewSet, AbstractBaseViewSet):
    logger_name = '__file__'

    def logger(self):
        return logging.getLogger(self.logger_name)

    def get_list(self, queryset):
        query_set = queryset
        if "search" in self.request.query_params:
            query_set = self.search_backends.filter_queryset(
                request=self.request, queryset=queryset, view=self
            )
        elif self.request.query_params:
            query_set = self.custom_filter_class.filter_queryset(
                request=self.request, queryset=queryset, view=self
            )
        if "ordering" in self.request.query_params:
            query_set = self.order_backend.filter_queryset(request=self.request, queryset=queryset, view=self)
        return query_set

    def get_paginated_data(self, queryset, serializer_class):
        paginated_data = self.paginator_class.generate_response(
            queryset, serializer_class, self.request
        )
        return paginated_data
