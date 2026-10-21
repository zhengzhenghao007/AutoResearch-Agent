from fastapi import APIRouter, Depends
from backend.app.api.research import get_workflow, invoke
from schemas.research_jobs import JobRequest
from services.research_jobs import manager_for

router = APIRouter(prefix='/api/research/jobs', tags=['background jobs'])


def get_manager(flow=Depends(get_workflow)):
    return invoke(lambda: manager_for(flow.store))


@router.get('')
def list_jobs(manager=Depends(get_manager)):
    return invoke(manager.list)


@router.post('')
def submit_job(request: JobRequest, manager=Depends(get_manager)):
    return invoke(lambda: manager.submit(request.model_dump()))


@router.get('/{job_id}')
def get_job(job_id: str, manager=Depends(get_manager)):
    return invoke(lambda: manager.get(job_id))


@router.post('/{job_id}/cancel')
def cancel_job(job_id: str, manager=Depends(get_manager)):
    return invoke(lambda: manager.cancel(job_id))


@router.post('/{job_id}/retry')
def retry_job(job_id: str, manager=Depends(get_manager)):
    return invoke(lambda: manager.retry(job_id))


@router.delete('/{job_id}')
def delete_job(job_id: str, manager=Depends(get_manager)):
    invoke(lambda: manager.delete(job_id))
    return {'removed':job_id}
