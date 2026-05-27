import docker
import time
import uuid
import tarfile
import io
import threading


EXEC_DIR = "/workspace/reliability_exec"
EXEC_FILE_PREFIX = "reliability_job"


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
                command=f"sleep {timeout + 10}",
                detach=True,
                network_disabled=True,
                mem_limit="256m",
                pids_limit=64,
            )

            filename = f"{EXEC_FILE_PREFIX}_{uuid.uuid4().hex}.py"
            filepath = f"{EXEC_DIR}/{filename}"

            # 2️⃣ 创建目录
            container.exec_run(f"mkdir -p {EXEC_DIR}")

            # 3️⃣ 用 tar 流写文件
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                data = code.encode("utf-8")
                tarinfo = tarfile.TarInfo(name=filename)
                tarinfo.size = len(data)
                tar.addfile(tarinfo, io.BytesIO(data))

            tar_stream.seek(0)
            container.put_archive(EXEC_DIR, tar_stream)

            # 4️⃣ 在线程中执行，通过 join(timeout) 真正 enforce timeout
            result_holder = {}

            def _exec():
                try:
                    result_holder["result"] = container.exec_run(
                        cmd=f"python {filepath}",
                        stdout=True,
                        stderr=True,
                    )
                except Exception as exc:
                    result_holder["error"] = exc

            thread = threading.Thread(target=_exec, daemon=True)
            thread.start()
            thread.join(timeout=timeout)

            if thread.is_alive():
                # 超时：kill 容器以解除 exec_run 阻塞
                try:
                    container.kill()
                except Exception:
                    pass
                return {
                    "status": "error",
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout}s",
                    "return_code": 124,
                    "timeout": True,
                    "runtime_error": True,
                    "runtime": round(time.time() - start, 4),
                }

            if "error" in result_holder:
                raise result_holder["error"]

            exec_result = result_holder["result"]
            output = exec_result.output.decode("utf-8", errors="ignore")
            succeeded = exec_result.exit_code == 0

            return {
                "status": "success" if succeeded else "error",
                "stdout": output if succeeded else "",
                "stderr": "" if succeeded else output,
                "return_code": exec_result.exit_code,
                "timeout": False,
                "runtime_error": not succeeded,
                "runtime": round(time.time() - start, 4),
            }

        except Exception as e:
            return {
                "status": "error",
                "stdout": "",
                "stderr": str(e),
                "return_code": 1,
                "timeout": False,
                "runtime_error": True,
                "runtime": round(time.time() - start, 4),
            }

        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass