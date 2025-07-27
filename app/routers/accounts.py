from fastapi import APIRouter, Depends, Request

from fastapi.middleware import Middleware


router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get('/')
async def validar_token(request: Request):
    user = request.state.user
    userData = {
        'id': user.get('id'),
        'username': user.get('username'),
        'email': user.get('email'),
        'isVerified': user.get('isVerified'),
        'role': user.get('role'),
        'profilePic': user.get('profilePic')
    }

    return ({'userData': userData})