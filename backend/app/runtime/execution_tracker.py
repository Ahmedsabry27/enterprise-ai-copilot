import asyncio
from collections import defaultdict


class ExecutionTracker:


    def __init__(self):

        self.executions = defaultdict(list)

        self.listeners = defaultdict(list)



    async def publish(
        self,
        execution_id,
        event
    ):

        self.executions[execution_id].append(
            event
        )


        for queue in self.listeners[execution_id]:

            await queue.put(event)



    def subscribe(
        self,
        execution_id
    ):

        queue = asyncio.Queue()

        self.listeners[execution_id].append(
            queue
        )

        return queue