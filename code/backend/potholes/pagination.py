from rest_framework.pagination import PageNumberPagination


class DynamicPageSizePagination(PageNumberPagination):
    """
    Custom pagination class that allows clients to control page size
    while setting reasonable limits for performance.
    """
    page_size = 20  # Default page size
    page_size_query_param = 'page_size'
    max_page_size = 100  # Maximum allowed page size for performance
    
    def get_page_size(self, request):
        """
        Determine the page size to use for pagination.
        
        Allows clients to set page_size via query parameter,
        but limits it to max_page_size for performance.
        """
        page_size = self.page_size
        
        if self.page_size_query_param:
            try:
                page_size = int(request.query_params[self.page_size_query_param])
                if page_size > 0:
                    # Limit to max_page_size for performance
                    page_size = min(page_size, self.max_page_size)
                else:
                    page_size = self.page_size
            except (KeyError, ValueError):
                page_size = self.page_size
                
        return page_size
