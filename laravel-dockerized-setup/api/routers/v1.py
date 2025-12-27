from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from api.services.DockerFacade import DockerFacade

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/download")
async def download_laravel(
    app_name: str = Query(..., description="Application name"),
    php_version: str = Query(..., description="PHP version"),
    node_version: int = Query(..., description="Node version"),
    react: bool = Query(False, description="Include React"),
    phpunit: bool = Query(False, description="Include PHPUnit"),
    npm: bool = Query(False, description="Include NPM"),
):
    react_flag = ""
    phpunit_flag = ""
    npm_flag = ""

    if react:
        react_flag = "--react"

    if phpunit:
        phpunit_flag = "--phpunit"

    if npm:
        npm_flag = "--npm"

    instructions = f"{react_flag} {phpunit_flag} {npm_flag}".strip()

    zip_path = DockerFacade.build_docker_image(
        app_name=app_name,
        php_version=php_version,
        node_version=node_version,
        instructions=instructions,
    )
    
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"{app_name}.zip",
        headers={"Content-Disposition": f"attachment; filename={app_name}.zip"}
    )
