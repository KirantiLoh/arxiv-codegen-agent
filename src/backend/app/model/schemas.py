# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

# ==========================================
# Incoming Messages (Frontend -> Backend)
# ==========================================

class UserPromptMessage(BaseModel):
    type: Literal["USER_PROMPT"]
    content: str

IncomingWSMessage = UserPromptMessage

# ==========================================
# Outgoing Messages (Backend -> Frontend)
# ==========================================

class AgentThoughtMessage(BaseModel):
    type: Literal["AGENT_THOUGHT"]
    content: str

class AgentOutputMessage(BaseModel):
    type: Literal["AGENT_OUTPUT"]
    content: str

class FileCreatedMessage(BaseModel):
    type: Literal["FILE_CREATED"]
    fileName: str
    language: str
    path: str

class TokenStreamMessage(BaseModel):
    type: Literal["TOKEN_STREAM"]
    fileName: str
    token: str


OutgoingWSMessage = AgentThoughtMessage | AgentOutputMessage | FileCreatedMessage | TokenStreamMessage

# ==========================================
# HTTP Request/Response Models
# ==========================================

class ProjectCreateRequest(BaseModel):
    arxiv_id: str = Field(..., pattern=r"^\d{4}\.\d{4,5}(v\d+)?$")

class ProjectCreateResponse(BaseModel):
    project_id: str
    status: str
    message: str

# --- NEW: Project List and Detail Models ---

class ProjectSummary(BaseModel):
    project_id: str
    arxiv_id: str
    status: str

class ProjectDetail(ProjectSummary):
    title: str
    # You can add more fields here later, like chunk_count, total_tokens, etc.
