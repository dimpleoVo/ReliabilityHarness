import docker
import time
import uuid
import tarfile
import io


EXEC_DIR = "/workspace/reactx_exec"
EXEC_FILE_PREFIX = "reactx_job"


class DockerSandboxExecutor:
    def __init__(self):
        self.client = docker.from_env()

    def run_python(self, code: str, timeout: int = 10, image: str = "python:3.11-slim"):
        start = time.time()
        container = None

        try:
            # 1️⃣ 启动容器
            container = self.client.containers.run(
                "python:3.11-slim",
                command="sleep 30",
                detach=True,
                network_disabled=True,
                mem_limit="256m",
                pids_limit=64,
            )

            filename = f"{EXEC_FILE_PREFIX}_{uuid.uuid4().hex}.py"
            filepath = f"{EXEC_DIR}/{filename}"

            # 2️⃣ 创建目录
            container.exec_run(f"mkdir -p {EXEC_DIR}")

            # 3️⃣ 用 tar 流写文件（🔥核心）
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                data = code.encode("utf-8")
                tarinfo = tarfile.TarInfo(name=filename)
                tarinfo.size = len(data)
                tar.addfile(tarinfo, io.BytesIO(data))

            tar_stream.seek(0)
            container.put_archive(EXEC_DIR, tar_stream)

            # 4️⃣ 执行
            exec_result = container.exec_run(
                cmd=f"python {filepath}",
                stdout=True,
                stderr=True,
            )

            output = exec_result.output.decode("utf-8", errors="ignore")

            return {
                "status": "success" if exec_result.exit_code == 0 else "error",
                "stdout": output if exec_result.exit_code == 0 else "",
                "stderr": "" if exec_result.exit_code == 0 else output,
                "return_code": exec_result.exit_code,
                "timeout": False,
                "runtime": round(time.time() - start, 4),
            }

        except Exception as e:
            return {
                "status": "error",
                "stdout": "",
                "stderr": str(e),
                "return_code": 1,
                "timeout": False,
                "runtime": round(time.time() - start, 4),
            }

        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass