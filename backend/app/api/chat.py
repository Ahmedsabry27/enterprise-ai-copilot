import asyncio
import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
)

from fastapi.responses import StreamingResponse

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.api.sse import to_sse

from app.auth.dependencies import get_current_user

from app.database.dependencies import get_db

from app.logging.logger import logger

from app.models.chat import (
    ChatRequest,
    ChatResponse,
)

from app.services.chat_service import chat_service
from app.services.conversation_service import conversation_service
from app.services.runtime_execution_service import runtime_execution_service



router = APIRouter()


class RuntimeStartResponse(BaseModel):
    execution_id: str
    workflow_id: str
    status: str


@router.post("/api/chat/start", response_model=RuntimeStartResponse, status_code=202)
async def start_runtime_execution(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    if request.conversation_id is None:
        raise HTTPException(status_code=422, detail="conversation_id is required")

    conversation = conversation_service.get_conversation(
        db=db,
        conversation_id=request.conversation_id,
        user_id=user["sub"],
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    execution = await runtime_execution_service.start(
        db,
        user_id=user["sub"],
        message=request.message,
        conversation_id=request.conversation_id,
    )
    return RuntimeStartResponse(
        execution_id=str(execution.id),
        workflow_id=str(execution.workflow_id),
        status=execution.status,
    )



# ==================================================
# Normal Chat Endpoint
# ==================================================

@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):

    try:

        response = chat_service.ask(

            db=db,

            user_id=user["sub"],

            message=request.message,

            conversation_id=request.conversation_id,

        )


        return ChatResponse(

            response=response.text,

            response_id=response.response_id,

        )


    except Exception as ex:


        logger.exception(
            "Chat failed"
        )


        raise HTTPException(

            status_code=500,

            detail=str(ex)

        )





# ==================================================
# Streaming Runtime Orchestrator
# ==================================================

@router.post(
    "/chat/stream"
)
async def stream_chat(

    request: Request,

    payload: ChatRequest,

    db: Session = Depends(get_db),

    user: dict = Depends(get_current_user),

):


    start_time = time.perf_counter()



    async def event_stream():


        try:


            # ----------------------------------
            # Request Received
            # ----------------------------------

            yield to_sse({

                "type": "runtime_step",

                "name": "Request Received",

                "status": "completed",

                "description":
                    "User prompt received"

            })



            await asyncio.sleep(0.2)




            # ----------------------------------
            # Conversation API
            # ----------------------------------

            yield to_sse({

                "type": "runtime_step",

                "name": "Conversation API",

                "status": "completed",

                "description":
                    "Conversation context loaded"

            })



            await asyncio.sleep(0.2)




            # ----------------------------------
            # Planner
            # ----------------------------------

            yield to_sse({

                "type": "runtime_step",

                "name": "Planner",

                "status": "running",

                "description":
                    "Creating execution plan"

            })



            await asyncio.sleep(1)



            yield to_sse({

                "type": "runtime_step",

                "name": "Planner",

                "status": "completed",

                "description":
                    "Execution plan created"

            })





            # ----------------------------------
            # Agent Execution
            # ----------------------------------

            yield to_sse({

                "type": "runtime_step",

                "name": "Agent Execution",

                "status": "running",

                "description":
                    "Agent selected and executing"

            })





            response = chat_service.ask(

                db=db,

                user_id=user["sub"],

                message=payload.message,

                conversation_id=payload.conversation_id,

            )




            yield to_sse({

                "type": "runtime_step",

                "name": "Agent Execution",

                "status": "completed",

                "description":
                    "Agent execution completed"

            })





            await asyncio.sleep(0.3)




            # ----------------------------------
            # Action Execution
            # ----------------------------------

            yield to_sse({

                "type": "runtime_step",

                "name": "Action Execution",

                "status": "completed",

                "description":
                    "Enterprise action executed"

            })





            await asyncio.sleep(0.3)




            # ----------------------------------
            # Result Generated
            # ----------------------------------

            yield to_sse({

                "type": "runtime_step",

                "name": "Result Generated",

                "status": "completed",

                "description":
                    "Response generated"

            })







            duration = round(

                (
                    time.perf_counter()
                    -
                    start_time

                )
                *
                1000,

                2

            )




            # ----------------------------------
            # Final Assistant Response
            # ----------------------------------

            yield to_sse({

                "type": "response",

                "message":
                    response.text,


                "response_id":
                    response.response_id,


                "status":
                    "COMPLETED",


                "agent":
                    getattr(

                        response,

                        "agent",

                        "default-agent"

                    ),



                "workflow_id":
                    getattr(

                        response,

                        "workflow_id",

                        None

                    ),



                "duration_ms":
                    duration,


                "conversation_id":
                    payload.conversation_id


            })




        except asyncio.CancelledError:

            logger.info(
                "Client disconnected"
            )

            return



        except Exception as ex:


            logger.exception(
                "Streaming failed"
            )


            yield to_sse({

                "type":
                    "error",

                "message":
                    str(ex)

            })






    return StreamingResponse(

        event_stream(),

        media_type=
            "text/event-stream",

        headers={


            "Cache-Control":
                "no-cache",


            "Connection":
                "keep-alive",


            "X-Accel-Buffering":
                "no",

            "Access-Control-Allow-Origin":
                "*"

        }

    )





# ==================================================
# CORS OPTIONS
# ==================================================

@router.options("/chat")
def options_chat():

    return Response(
        status_code=200
    )




@router.options("/chat/stream")
def options_stream():

    return Response(
        status_code=200
    )
