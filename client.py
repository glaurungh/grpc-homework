import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "proto"))

import grpc
import proto.tasks_pb2
import proto.tasks_pb2_grpc


def main():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = proto.tasks_pb2_grpc.TaskServiceStub(channel)

        for title in ("создать задачу", "настроить задачу", "выполнить задачу"):
            task = stub.CreateTask(
                proto.tasks_pb2.CreateTaskRequest(title=title, description=title)
            )
            print(f"id={task.id} title={task.title!r} status={proto.tasks_pb2.Task.Status.Name(task.status)}")

        task = stub.GetTask(proto.tasks_pb2.GetTaskRequest(id=1))
        print(f"id={task.id} title={task.title!r}")

        try:
            stub.GetTask(proto.tasks_pb2.GetTaskRequest(id=999))
        except grpc.RpcError as e:
            print(f"error: {e.code().name} — {e.details()}")

        try:
            for task in stub.ListTasks(proto.tasks_pb2.ListTasksRequest()):
                print(f"task: id={task.id} title={task.title!r}")
        except grpc.RpcError as e:
            print(f"stream error: {e.code().name} — {e.details()}")


if __name__ == "__main__":
    main()