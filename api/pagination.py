from rest_framework.pagination import PageNumberPagination

# Кастомная пагинация, позволяющая задать параметр `?limit=...`
class CustomPagination(PageNumberPagination):
    page_size_query_param = "limit"
