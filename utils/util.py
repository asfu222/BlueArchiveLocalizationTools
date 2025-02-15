from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Generator, Iterable, Literal, Protocol
from queue import Queue
from threading import Thread, Lock, Event
from time import sleep
from keyword import kwlist

class TemplateString:
    """
    Template string generator.

    :Example:
    .. code-block:: python
        CONSTANT = TemplateString("What%s a %s %s.")
        CONSTANT("", "fast", "fox")
        "What a fast fox."
    """

    def __init__(self, template: str) -> None:
        self.template = template

    def __call__(self, *args: Any) -> str:
        return self.template % args
class Utils:
    @staticmethod
    def convert_name_to_available(variable_name: str) -> str:
        """Convert varaible name to suitable with python.

        Args:
            variable_name (str): Name.

        Returns:
            str: Available string in python.
        """
        if not variable_name:
            return "_"
        if variable_name[0].isdigit():
            variable_name = "_" + variable_name
        if variable_name in kwlist:
            variable_name = f"{variable_name}_"
        return variable_name
        
class TaskManagerWorkerProtocol(Protocol):
    def __call__(
        self, task_manager: "TaskManager", *args: Any, **kwargs: Any
    ) -> None: ...


class TaskManager:
    def __init__(
        self,
        target_workers: int,
        max_workers: int,
        worker: TaskManagerWorkerProtocol,
        tasks: Queue[Any] = Queue(),
    ) -> None:
        """A simplified thread pool manager.

        Args:
            max_workers (int): Maximum number of threads to use.
            worker (Callable[..., None]): The worker function executed by each thread.
        """
        self.target_workers = target_workers
        self.max_workers = max_workers
        self.worker = worker
        self.tasks = tasks
        self.stop_task = False
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures: list[concurrent.futures.Future] = []
        self.lock = Lock()
        self.event = Event()
        self.__cancel_callback: tuple[Callable, tuple] | None = None
        self.__pool_condition: Callable = lambda: self.tasks.empty() or self.stop_task
        self.__force_exit = False

    def __enter__(self) -> "TaskManager":
        """Start the worker pool."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Shutdown the worker pool."""
        is_force = self.stop_task or self.__force_exit
        self.executor.shutdown(wait=not is_force, cancel_futures=is_force)

    def __set_conditions(self, func: Callable | None = None) -> None:
        if not func:
            self.__pool_condition = lambda: self.tasks.empty() or self.stop_task
        else:
            self.__pool_condition = func

    def add_worker(self, *args: Any) -> None:
        """Add a task to the worker queue."""
        future = self.executor.submit(self.worker, *args)
        self.futures.append(future)

    def increase_worker(self, num: int = 1) -> None:
        """Increase worker with exsist worker parameters."""
        self.target_workers += num

    def set_cancel_callback(self, callback: Callable[..., None], *args) -> None:
        """Set a callback for task canceled."""
        self.__cancel_callback = (callback, args)

    def set_force_shutdown(self, force: bool = True) -> None:
        """Set is or not shutdown without wait."""
        self.__force_exit = force

    def set_relate(
        self, mode: Literal["event"], related_manager: "TaskManager"
    ) -> None:
        """Set a relation to another task by a flag."""
        if mode == "event":
            self.event = related_manager.event
            self.__set_conditions(
                lambda: self.stop_task or (self.tasks.empty() and self.event.is_set())
            )

    def import_tasks(self, tasks: Iterable[Any]) -> None:
        """Import tasks from iterable sequency and set to instance task

        Args:
            tasks (Iterable[Any]): Any iterable elements.
        """
        queue_tasks: Queue[Any] = Queue()
        for task in tasks:
            queue_tasks.put(task)
        self.tasks = queue_tasks

    def run_without_block(self, *worker_args: Any) -> Thread:
        """Same as run and without block."""
        thread = Thread(target=self.run, args=worker_args, daemon=True)
        thread.start()
        return thread

    def run(self, *worker_args: Any) -> None:
        """Start worker and give parameters to worker."""
        try:
            while not self.__pool_condition():
                while len(self.futures) < self.target_workers:
                    self.add_worker(*worker_args)
                self.futures = [f for f in self.futures if not f.done()]
                sleep(0.1)

        except KeyboardInterrupt:
            if self.__cancel_callback:
                self.__cancel_callback[0](*self.__cancel_callback[1])
            self.stop_task = True
            while not self.tasks.empty():
                self.tasks.get()
                self.tasks.task_done()
            self.executor.shutdown(wait=False, cancel_futures=True)
        finally:
            self.event.set()
            if not self.__force_exit:
                for future in self.futures:
                    future.result()

    def done(self) -> None:
        """Finish thread pool manually."""
        self.__exit__(None, None, None)