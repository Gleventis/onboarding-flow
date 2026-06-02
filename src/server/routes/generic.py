"""
generic routes. Includes root and healthcheck
"""
from fastapi import APIRouter, responses, status
from starlette.responses import RedirectResponse

router = APIRouter()


@router.get('/', include_in_schema=False)
def index():
    """
    root, redirects to the swagger docs

    Returns:
        (RedirectResponse): redirects to swagger docs
    """
    return RedirectResponse(url='/docs')


@router.get('/healthcheck')
async def healthcheck():
    """
    healthcheck endpoint

    Returns:
        (Response): 200 response if server is available
    """
    return responses.Response(status_code=status.HTTP_200_OK)
