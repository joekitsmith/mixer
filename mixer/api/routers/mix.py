from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from mixer.api import schemas
from mixer.api.crud import crud_mix
from mixer.api.database import get_db

mix_router = APIRouter(prefix="/mix", tags=["Mix"])


@mix_router.post("/", response_model=schemas.Mix)
def create_mix(response: Response, db: Session = Depends(get_db)):
    """
    Create a mix and attach the ID to a cookie.

    Returns
    -------
    mix : schemas.Mix
        Mix created in DB
    """
    mix = crud_mix.create_mix(db)
    response.set_cookie(key="mix_id", value=mix.id)
    return mix


@mix_router.get("/", response_model=schemas.Mix)
def get_current_mix(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    """
    Get the mix that is associated with the ID stored in the request cookie if it exists.

    Returns
    -------
    mix : schemas.Mix
        Mix created in database

    Raises
    ------
    HTTPException
        If the mix ID request cookie is not present, a 400 error is raised
    HTTPException
        If a mix could not be retrieved from the database using the ID, a 404 error is raised
    """
    mix_id = request.cookies.get("mix_id")
    if not mix_id:
        raise HTTPException(
            status_code=400, detail="A mix could not be found in the current session"
        )
    mix = crud_mix.get_mix(db, mix_id)
    if not mix:
        raise HTTPException(
            status_code=404,
            detail="A mix with ID {mix_id} could not be found in the database",
        )
    return mix


@mix_router.get("/{mix_id}", response_model=schemas.Mix)
def get_mix_by_id(mix_id: str, db: Session = Depends(get_db)):
    """
    Get a mix by its ID if it exists.

    Parameters
    ----------
    mix_id : str
        ID of mix in database

    Returns
    -------
    mix : schemas.Mix
        Mix created in database

    Raises
    ------
    HTTPException
        If a mix could not be retrieved from the database using the ID, a 404 error is raised
    """
    mix = crud_mix.get_mix(db, mix_id)
    if not mix:
        raise HTTPException(
            status_code=404, detail=f"A mix could not be found with ID {mix.id}"
        )
    return mix


@mix_router.delete("/", response_model=schemas.MixDelete)
def discard_mix(request: Request, response: Response):
    """
    Remove the mix ID request cookie if it exists.

    Returns
    -------
    mix : schemas.MixDelete
        Message describing discard action taken, if any
    """
    mix_id = request.cookies.get("mix_id")
    if not mix_id:
        return {"message": "No mix found in session"}
    response.delete_cookie("mix_id")
    return {"message": f"Mix {mix_id} removed from session"}
