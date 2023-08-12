from rest_framework import status
from rest_framework.pagination import PageNumberPagination

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 3


class CustomPaginator(PageNumberPagination):
    page = DEFAULT_PAGE
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "limit"

    def generate_response(self, query_set, serializer_obj, request):
        try:
            page_data = self.paginate_queryset(query_set, request)
        except Exception as ex:
            response = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "No results found for the requested page",
            }
            return response
        serialized_page = serializer_obj(page_data, many=True, context={"request": request})
        response = {
            "status": status.HTTP_200_OK,
            "message": "ok",
            "total": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "page": int(request.GET.get("page", DEFAULT_PAGE)),
            "limit": int(request.GET.get("limit", self.page_size)),
            "results": serialized_page.data,
        }
        return response
