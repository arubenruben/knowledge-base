import os
import zipfile
import tempfile
import subprocess
from fastapi import HTTPException

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_DIR = os.path.join(CURRENT_DIR, "docker")


class DockerFacade:
    @staticmethod
    def build_docker_image(
        app_name: str, php_version: str, node_version: int, instructions: str
    ):
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
                docker_volume_path = temp_dir.replace("\\", "/")
                if len(docker_volume_path) > 1 and docker_volume_path[1:3] == ":/":
                    docker_volume_path = (
                        f"/{docker_volume_path[0].lower()}{docker_volume_path[2:]}"
                    )

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
                try:
                    created_files = os.listdir(project_path)
                    print(
                        f"Created {len(created_files)} files in the Laravel project directory."
                    )
                except FileNotFoundError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Laravel project directory not found. Docker output: {result.stdout}",
                    )

                # Create a zip file of the Laravel project
                zip_filename = f"{app_name}.zip"
                zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(project_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)

                print(f"Created zip file at: {zip_path}")
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
