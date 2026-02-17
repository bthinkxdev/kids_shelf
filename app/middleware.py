"""
Middleware for guest checkout and session handling.
"""


class EnsureGuestSessionMiddleware:
    """
    Ensures anonymous users have a session key on every request.
    Required for session-based cart and wishlist before any cart/wishlist access.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.session.session_key:
            request.session.create()
        return self.get_response(request)
