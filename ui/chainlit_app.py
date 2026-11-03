import chainlit as cl
import httpx

LOGIN_URL = "http://localhost:8000/api/auth/login"
API_URL = "http://localhost:8000/api/documents/chat"
HISTORY_URL = "http://localhost:8000/api/documents/chat/history"
UPLOAD_URL = "http://localhost:8000/api/documents/upload"
DOCUMENTS_URL = "http://localhost:8000/api/documents/list"


@cl.on_message
async def main(message: cl.Message):
    role = cl.user_session.get("role")

    if role == "admin":
        await cl.Message(content="Admin cannot use chat. You can upload documents.").send()
        return

    token = cl.user_session.get("token")
    if not token:
        await cl.Message(content="Please log in first.").send()
        return

    username = cl.user_session.get("username", "customer")

    async with httpx.AsyncClient(timeout=120.0) as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            API_URL,
            json={"question": message.content, "session_id": username},
            headers=headers,
        )

    if response.status_code != 200:
        await cl.Message(content=f"Error ({response.status_code}): {response.text}").send()
        return

    data = response.json()
    answer = data.get("answer")
    if not answer or answer.strip() == "":
        answer = "I don't have that information in the documentation."

    sources = data.get("sources", [])
    source_text = ""
    if sources:
        source_text = "\n\n---\n**Sources:**\n\n" + "\n\n".join(
            [f"[Source {s['id']}]\n{s['text'][:200]}..." for s in sources]
        )

    final_response = answer + source_text
    await cl.Message(content=final_response).send()


@cl.on_chat_start
async def on_start():
    # 1. Ask username
    username_msg = await cl.AskUserMessage(content="Enter username:").send()
    username = username_msg["output"] if username_msg else None

    if not username:
        await cl.Message(content="Login cancelled.").send()
        return

    # 2. Ask password
    password_msg = await cl.AskUserMessage(content="Enter password:").send()
    password = password_msg["output"] if password_msg else None

    # 3. Call backend login
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                LOGIN_URL,
                data={"username": username, "password": password},
            )
        except Exception as e:
            await cl.Message(content=f"Failed to connect to backend: {e}").send()
            return

    if response.status_code != 200:
        await cl.Message(content="Login failed. Please refresh and check your credentials.").send()
        return

    data = response.json()
    token = data["access_token"]
    role = data.get("role")

    cl.user_session.set("token", token)
    cl.user_session.set("role", role)
    cl.user_session.set("username", username)

    await cl.Message(content=f"Logged in as **{username}** ({role.upper()})").send()

    headers = {"Authorization": f"Bearer {token}"}

    # If Admin -> Allow document upload
    if role == "admin":
        await cl.Message(content="Welcome Admin! You can upload knowledge base documents below:").send()
        files = await cl.AskFileMessage(
            content="Upload a document (PDF, TXT, MD)",
            accept=["application/pdf", "text/plain", "text/markdown"],
            max_size_mb=10,
            timeout=180,
        ).send()

        if files:
            file = files[0]
            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(file.path, "rb") as f:
                    upload_res = await client.post(
                        UPLOAD_URL,
                        files={"file": (file.name, f, "application/pdf")},
                        headers=headers,
                    )

            if upload_res.status_code == 200:
                await cl.Message(
                    content="Document uploaded successfully! Processing will begin automatically."
                ).send()
                # Fetch status
                async with httpx.AsyncClient() as client:
                    docs_res = await client.get(DOCUMENTS_URL, headers=headers)
                    if docs_res.status_code == 200:
                        docs = docs_res.json()[-5:]
                        status_text = "\n".join([f"- **{d['filename']}** → {d['status']}" for d in docs])
                        await cl.Message(content=f"**Recent Documents:**\n\n{status_text}").send()
            else:
                await cl.Message(content=f"Upload failed: {upload_res.text}").send()

    # If Customer -> Load existing chat history
    else:
        await cl.Message(content="Welcome to Customer Support! Ask any question about company policies or products.").send()
        async with httpx.AsyncClient() as client:
            try:
                hist_res = await client.get(
                    HISTORY_URL,
                    params={"session_id": username},
                    headers=headers,
                )
                if hist_res.status_code == 200:
                    history = hist_res.json()
                    for msg in history:
                        await cl.Message(content=msg["content"], author=msg["role"]).send()
            except Exception:
                pass
