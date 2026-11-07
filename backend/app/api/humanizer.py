from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from services.humanizer_policy import Profile, profile, set_profile

router = APIRouter(prefix='/api/research/settings', tags=['output settings'])


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    profile: Profile


@router.get('/academic-humanizer')
def get_policy(request: Request):
    return {'enabled': True, 'profile': profile(), 'editable': not request.app.state.security_config.deployment}


@router.put('/academic-humanizer')
def update_policy(request: Request, update: ProfileUpdate):
    if request.app.state.security_config.deployment:
        raise HTTPException(403, 'The deployment administrator manages the global editing profile.')
    set_profile(update.profile)
    return get_policy(request)
