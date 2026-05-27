import subprocess


def run_model_container(image, command, volumes=None):

    docker_cmd = ["docker", "run", "--rm"]

    if volumes:
        for host, container in volumes.items():
            docker_cmd.extend(["-v", f"{host}:{container}"])

    docker_cmd.append(image)

    docker_cmd.extend(command)

    subprocess.run(docker_cmd, check=True)