from app.runtime.event_bus import EventBus
from app.events.runtime_events import WorkflowStarted


def test_event_bus():

    received = []

    bus = EventBus()

    def handler(event):
        received.append(event)

    bus.subscribe(
        WorkflowStarted,
        handler,
    )

    bus.publish(
        WorkflowStarted(
            source="planner"
        )
    )

    assert len(received) == 1

    assert received[0].source == "planner"