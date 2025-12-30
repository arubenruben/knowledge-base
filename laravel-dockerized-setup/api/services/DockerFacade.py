import os
import time
import shutil
import zipfile
import tempfile
import subprocess
from fastapi import HTTPException

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_DIR = os.path.join(CURRENT_DIR, "docker")
NGINX_DIR = os.path.join(DOCKER_DIR, "nginx")
PHP_FPM_DIR = os.path.join(DOCKER_DIR, "php-fpm")


class DockerFacade:
    @staticmethod
    def build_docker_image(
        app_name: str, php_version: str, node_version: int, instructions: str
    ) -> str:
        # Verify if "./docker/laravel" directory exists
        dockerfile_path = os.path.join(DOCKER_DIR, "laravel")

        if not os.path.isdir(dockerfile_path):
            raise HTTPException(
                status_code=400,
                detail=f"Dockerfile directory not found at path: {dockerfile_path}",
            )
        # Verify if Dockerfile exists in the specified directory
        dockerfile_full_path = os.path.join(dockerfile_path, "Dockerfile")

        if not os.path.isfile(dockerfile_full_path):
            raise HTTPException(
                status_code=400,
                detail=f"Dockerfile not found at path: {dockerfile_full_path}",
            )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert Windows path to Docker-compatible format
                if os.name == "nt":
                    docker_volume_path = temp_dir.replace("\\", "/")
                    if len(docker_volume_path) > 1 and docker_volume_path[1:3] == ":/":
                        docker_volume_path = (
                            f"/{docker_volume_path[0].lower()}{docker_volume_path[2:]}"
                        )
                else:
                    docker_volume_path = temp_dir

                # First, build the Docker image from the current directory
                subprocess.run(
                    [
                        "docker",
                        "build",
                        "-t",
                        "laravel-dockerized-setup",
                        "--build-arg",
                        f"PHP_VERSION={php_version}",
                        "--build-arg",
                        f"NODE_VERSION={node_version}",
                        ".",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=dockerfile_path,
                )

                # Then run the container with the built image
                result = subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "-e",
                        f"APP_NAME={app_name}",
                        "-e",
                        f"INSTRUCTIONS={instructions}",
                        "-v",
                        f"{docker_volume_path}:/app/out",
                        "laravel-dockerized-setup",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Verify the Laravel project was created
                project_path = os.path.join(temp_dir, app_name)

                # Debug: List contents of temp_dir
                try:
                    temp_contents = os.listdir(temp_dir)
                    print(f"Contents of temp_dir ({temp_dir}): {temp_contents}")
                except Exception as e:
                    print(f"Error listing temp_dir: {e}")

                # Wait a moment for filesystem sync on Linux
                time.sleep(1)

                if not os.path.exists(project_path):
                    # List what's actually in temp_dir for debugging
                    try:
                        temp_contents = os.listdir(temp_dir)
                        raise HTTPException(
                            status_code=400,
                            detail=f"Laravel project directory not found at {project_path}. "
                            f"Temp dir ({temp_dir}) contains: {temp_contents}. "
                            f"Docker output: {result.stdout}",
                        )
                    except OSError as e:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Failed to access temp directory {temp_dir}: {str(e)}. "
                            f"Docker output: {result.stdout}",
                        )

                try:
                    created_files = os.listdir(project_path)
                    print(
                        f"Created {len(created_files)} files in the Laravel project directory."
                    )
                except FileNotFoundError as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Laravel project directory not found at {project_path}: {str(e)}. "
                        f"Docker output: {result.stdout}",
                    )

                # Create a zip file of the Laravel project
                zip_filename = f"{app_name}.zip"
                zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

                # Copy Nginx folder to a new 'nginx' folder inside the project directory
                nginx_dest = os.path.join(project_path, "nginx")
                shutil.copytree(NGINX_DIR, nginx_dest)

                # Copy PHP-FPM folder to a new 'php-fpm' folder inside the project directory
                php_fpm_dest = os.path.join(project_path, "php-fpm")
                shutil.copytree(PHP_FPM_DIR, php_fpm_dest)

                # Copy the dev.docker-compose.yml to the project directory
                compose_src = os.path.join(DOCKER_DIR, "dev.docker-compose.yml")
                compose_dest = os.path.join(project_path, "dev.docker-compose.yml")
                shutil.copyfile(compose_src, compose_dest)

                # Copy the template.docker-compose.yml to the project directory
                compose_src = os.path.join(DOCKER_DIR, "template.docker-compose.yml")
                compose_dest = os.path.join(project_path, "template.docker-compose.yml")
                shutil.copyfile(compose_src, compose_dest)

                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(project_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)

                return zip_path

        except subprocess.CalledProcessError as e:
            error_message = e.stderr if e.stderr else e.stdout if e.stdout else str(e)
            raise HTTPException(
                status_code=400, detail=f"Docker command failed: {error_message}"
            )
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Docker command not found. Please ensure Docker is installed and in PATH. Error: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to build Docker image: {str(e)}"
            )
