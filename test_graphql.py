import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

# Use a unique email for each test run to avoid collision if DB isn't reset
CONTRACTOR_EMAIL = "ci_contractor@example.com"
PASSWORD = "password123"

@pytest.fixture
async def client():
    """
    Creates an async HTTP client that runs directly against the FastAPI app.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_token(client):
    """
    Registers/Logins a user and returns the access token.
    """
    # 1. Register
    register_query = """
    mutation {
        register(email: "%s", password: "%s", role: "CONTRACTOR") {
            accessToken
        }
    }
    """ % (CONTRACTOR_EMAIL, PASSWORD)
    
    response = await client.post("/graphql", json={"query": register_query})
    data = response.json()
    
    # If user already exists (from previous run), login instead
    if not (data.get("data") or {}).get("register"):
        login_query = """
        mutation {
            login(email: "%s", password: "%s") {
                accessToken
            }
        }
        """ % (CONTRACTOR_EMAIL, PASSWORD)
        response = await client.post("/graphql", json={"query": login_query})
        data = response.json()
        return data["data"]["login"]["accessToken"]
        
    return data["data"]["register"]["accessToken"]

@pytest.mark.asyncio
async def test_create_job_and_subtasks(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    # 1. Create Job
    create_job_query = """
    mutation {
        createJob(
            description: "CI Test Job", 
            location: "CI Lab", 
            cost: "5000.00"
        ) {
            id
            description
            status
        }
    }
    """
    response = await client.post("/graphql", json={"query": create_job_query}, headers=headers)
    data = response.json()
    
    assert "errors" not in data
    job = data["data"]["createJob"]
    assert job["description"] == "CI Test Job"
    job_id = job["id"]

    # 2. Add Subtask
    add_task_query = f"""
    mutation {{
        addSubtask(jobId: {job_id}, description: "CI Subtask", cost: "100.00") {{
            id
            subtasks {{
                description
                cost
            }}
        }}
    }}
    """
    response = await client.post("/graphql", json={"query": add_task_query}, headers=headers)
    data = response.json()
    
    assert "errors" not in data
    subtasks = data["data"]["addSubtask"]["subtasks"]
    assert len(subtasks) == 1
    assert subtasks[0]["description"] == "CI Subtask"

    # 3. Verify via Query
    query_job = f"""
    query {{
        job(jobId: {job_id}) {{
            id
            subtasks {{
                description
            }}
        }}
    }}
    """
    response = await client.post("/graphql", json={"query": query_job}, headers=headers)
    data = response.json()
    
    fetched_job = data["data"]["job"]
    assert fetched_job["id"] == str(job_id)
    assert fetched_job["subtasks"][0]["description"] == "CI Subtask"