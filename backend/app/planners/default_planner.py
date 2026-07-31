from __future__ import annotations

from uuid import uuid4

from app.contracts.planner import Planner
from app.runtime.context import RuntimeContext
from app.runtime.execution_plan import ExecutionPlan
from app.runtime.task import Task


class DefaultPlanner(Planner):
    """
    Default planner implementation.

    Generates agent-aware execution plans.

    Responsibilities:
    - Understand the user goal
    - Create executable tasks
    - Define required capabilities

    The planner does NOT select agents.
    Agent selection is handled by AgentRegistry.
    """


    async def plan(
        self,
        context: RuntimeContext,
    ) -> ExecutionPlan:
        """
        Generate execution plan from runtime context.
        """


        # In future:
        # LLM planner will analyze the goal
        # and generate required capabilities dynamically.

        required_capabilities = [
            "general-execution"
        ]


        task = Task(
            id=uuid4(),

            name="Echo Goal",

            description=(
                f"Execute goal: {context.goal}"
            ),


            # Dynamic routing:
            # AgentRegistry will select
            # the best matching agent.
            agent="default-agent",


            required_capabilities=(
                required_capabilities
            ),


            tool=None,
        )


        return ExecutionPlan(
            goal=context.goal,

            tasks=[
                task
            ],


            required_capabilities=(
                required_capabilities
            ),


            agent_requirements={
                task.name: required_capabilities
            },


            estimated_duration_seconds=1.0,

            estimated_cost=0.0,
        )