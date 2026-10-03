from contextlib import asynccontextmanager
import logging
from pydantic import TypeAdapter, ValidationError

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from laya.router import Router
from langchain_classic.storage._lc_store import create_kv_docstore
from langchain_classic.retrievers import MultiVectorRetriever
from langchain_community.storage import RedisStore
from qdrant_client import QdrantClient
import redis.asyncio as redis

from arxiv_reproducer_agent.graph import create_workflow
from backend.app.core.websocket import manager
from backend.app.model.schemas import (
    AgentThoughtMessage,
    FileCreatedMessage,
    IncomingWSMessage,
    OutgoingWSMessage,
    AgentOutputMessage,
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectSummary,
    ProjectDetail,
    TokenStreamMessage,
    UserPromptMessage,
)
from backend.app.core.etl import ingest_arxiv_paper
from utils.env import EnvConfig
from utils.db import init_qdrant_vector_store

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

TOP_K = 2
RELEVANCE_THRESHOLD = 0.75

settings = EnvConfig()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up: Initializing DB connections...")
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    vectorstore = init_qdrant_vector_store(
        qdrant_client, 
        settings.EMBEDDING_MODEL,
        settings.QDRANT_COLLECTION_NAME, 
        settings.EMBEDDING_DIM, 
        settings.SPARSE_VECTOR_NAME
    )
    redis_client = redis.from_url(url=settings.REDIS_URL)
    bytestore = RedisStore(redis_url=settings.REDIS_URL, namespace="doc")
    docstore = create_kv_docstore(bytestore)

    retriever = MultiVectorRetriever(
        docstore=docstore,
        vectorstore=vectorstore,
        id_key="parent_id",
        search_kwargs={"k": TOP_K, "score_threshold": RELEVANCE_THRESHOLD}
    )
    laya_router = Router(preload=True)
    agent_workflow = create_workflow(retriever, laya_router, TOP_K)

    app.state.qdrant_client = qdrant_client
    app.state.retriever = retriever
    app.state.redis_client = redis_client
    app.state.laya_router = laya_router
    app.state.agent_workflow = agent_workflow

    yield

    logger.info("Shutting down: Closing DB connections...")
    if redis_client:
        await redis_client.aclose()
    if qdrant_client:
        qdrant_client.close()


app = FastAPI(
    title="Arxiv Codegen Backend v1",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# HTTP REST Endpoints
# ==========================================

@app.get("/", response_class=Response)
async def home():
    """
    Health check and version endpoint.
    Returns plain text as requested.
    """
    return Response(content="Arxiv Codgen Backend v1.0", media_type="text/plain")


@app.get("/projects")
async def list_projects():
    """
    Returns a list of all created projects.
    """
    return {
            "projects": []
            }


@app.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str):
    """
    Returns detailed information about a specific project.
    """
    project = None
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


@app.post("/projects", response_model=ProjectCreateResponse)
async def create_project(payload: ProjectCreateRequest, background_tasks: BackgroundTasks):
    """
    Triggers the ETL pipeline in the background and returns immediately.
    """

    # Offload heavy ETL to background task
    background_tasks.add_task(
        ingest_arxiv_paper,
        arxiv_id=payload.arxiv_id,
        qdrant_client=app.state.qdrant_client,
        redis_client=app.state.redis_client
    )

    return ProjectCreateResponse(
        project_id=payload.arxiv_id,
        status="processing",
        message=f"Paper {payload.arxiv_id} ingestion started in background."
    )


# ==========================================
# WebSocket Endpoints
# ==========================================

@app.websocket("/projects/{project_id}/ws")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """
    Handles real-time bidirectional communication for a specific project.
    """
    # if project_id:
    #     await websocket.close(code=4004, reason="Project not found")
    #     return
    incoming_message_adapter = TypeAdapter(IncomingWSMessage)
    await manager.connect(websocket, project_id)
    try:
        while True:
            data = await websocket.receive_json()
            data["type"] = "USER_PROMPT"

            try:
                incoming_message = incoming_message_adapter.validate_python(data)
            except ValidationError as e:
                logger.warning(f"Invalid message format received: {data}. Error: {e}")
                continue

            if isinstance(incoming_message, UserPromptMessage):
                logger.info(f"Received prompt for {project_id}: {incoming_message.content[:50]}...")
                await manager.send_personal_message(AgentThoughtMessage(type="AGENT_THOUGHT", content="Scaffolding..."), websocket)
                payload = {
                        "messages": [("user", incoming_message.content)],
                        "arxiv_id": project_id,
                    }
                async for chunk in websocket.app.state.agent_workflow.astream(payload, stream_mode="updates", version="v2"):
                    if chunk["type"] == "updates":
                        for node_name, state in chunk.get("data", {}).items():
                            message: OutgoingWSMessage | None = None
                            match node_name:
                                case "router":
                                    message = AgentThoughtMessage(
                                            type="AGENT_THOUGHT", 
                                            content="Retrieving relevant context..."
                                        )
                                case "retriever":
                                    message = AgentThoughtMessage(
                                        type="AGENT_THOUGHT", 
                                        content="Tinkering..."
                                    )
                                case "architect":
                                    message = AgentThoughtMessage(
                                        type="AGENT_THOUGHT", 
                                        content="Validating contract..."
                                    )
                                case "validate_contract":
                                    contract = state.get("architect_contract", {})
                                    # Pre-create tabs in frontend for all files in the contract
                                    for file_info in contract.get("files", []):
                                        fname = file_info["filename"]
                                        await manager.send_personal_message(
                                            FileCreatedMessage(
                                                type="FILE_CREATED",
                                                fileName=fname,
                                                language="python",
                                                path=f"./{fname}"
                                            ),
                                            websocket
                                        )
                                    message = AgentThoughtMessage(
                                            type="AGENT_THOUGHT",
                                            content="Generating files"
                                            )
                                case "developer":
                                    file_name = state.get("current_file_being_generated", "main.py")
                                    token_content = state.get("generated_files", {}).get(file_name, "")
                                    message = TokenStreamMessage(
                                        type="TOKEN_STREAM", 
                                        fileName=file_name, 
                                        token=token_content
                                    )
                                case "guide":
                                    message = AgentOutputMessage(
                                            type="AGENT_OUTPUT",
                                            content=state.get("messages", [])[-1].content
                                    )
                            logger.info(f"Sending message: {message}")
                            if message is not None:
                                await manager.send_personal_message(message, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, project_id)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket loop for {project_id}: {e}")
        await manager.disconnect(websocket, project_id)
