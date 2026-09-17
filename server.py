"""gRPC-сервер сервиса задач. Запуск: python server.py"""
import logging
from concurrent import futures
import itertools as it
import typing as t

import grpc
from grpc_reflection.v1alpha import reflection

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "proto"))
from proto import tasks_pb2
from proto import tasks_pb2_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


DATABASE: dict[int, tasks_pb2.Task]  = dict()
TASK_ID_ITERATOR: t.Iterator[int] = it.count(1)

def get_task_id() -> int:
    return next(TASK_ID_ITERATOR)


class TaskService(tasks_pb2_grpc.TaskServiceServicer):
    """Логика сервиса. Имена методов = имена rpc из .proto."""

    def CreateTask(self, request, context):
        logging.info("CreateTask: request=%s", request)
        task_id = get_task_id()
        DATABASE[task_id] = tasks_pb2.Task(
            id=task_id,
            title=request.title,
            description=request.description
        )
        return DATABASE[task_id]

    def GetTask(self, request, context):
        logging.info("GetTask: id=%s", request.id)
        task = DATABASE.get(request.id)
        if not task:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"TASK ID {request.id!r} not found",
            )
        return task

    def ListTasks(self, request, context):
        logging.info("ListTasks: request=%s", request)

        for task_id in DATABASE:
            if not context.is_active():
                logging.info("client disconnected, stop streaming")
                return
            yield DATABASE[task_id]


def serve():
    # Синхронный сервер на пуле потоков (есть и асинхронный grpc.aio.server)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tasks_pb2_grpc.add_TaskServiceServicer_to_server(TaskService(), server)

    # Reflection: чтобы grpcurl/Postman видели сервис без proto-файла
    reflection.enable_server_reflection(
        (
            tasks_pb2.DESCRIPTOR.services_by_name["TaskService"].full_name,
            reflection.SERVICE_NAME,
        ),
        server,
    )

    server.add_insecure_port("[::]:50051")  # в проде — TLS (secure_port)
    server.start()
    logging.info("server listening on :50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()