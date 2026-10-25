# API Contract — Company Handbook Intelligence AI

**Base URL**: `http://127.0.0.1:8000`

---

### 1. Health Check
* **Endpoint**: `GET /health`
* **Description**: Verifies backend availability, local vector store state, and active chunk count.
* **Success Response (200 OK)**:
```json
{
  "status": "ok",
  "rag_ready": true,
  "indexed_chunks": 378,
  "current_document": "company_handbook.pdf"
}
```

---

### 2. Upload and Index PDF
* **Endpoint**: `POST /upload`
* **Content-Type**: `multipart/form-data`
* **Parameters**:
  * `file`: Binary PDF file (Max 25 MB).
* **Success Response (200 OK)**:
```json
{
  "message": "PDF uploaded and indexed successfully",
  "filename": "company_handbook.pdf",
  "chunks_indexed": 378
}
```
* **Error Responses**:
  * `400 Bad Request`: File is not a PDF, empty, corrupted, or has no extractable text.
  * `413 Payload Too Large`: File exceeds 25 MB size limit.
  * `500 Internal Server Error`: Extraction or embedding failure.

---

### 3. Ask Question
* **Endpoint**: `POST /ask`
* **Content-Type**: `application/json`
* **Request Payload**:
```json
{
  "question": "What is the annual leave entitlement?"
}
```
* **Success Response (200 OK)**:
```json
{
  "answer": "According to page 12 of the handbook, regular employees receive 20 days of annual leave per year.",
  "sources": [
    {
      "page": 12,
      "text": "Regular full-time employees are entitled to 20 days of paid annual leave per calendar year."
    }
  ]
}
```
* **Error Responses**:
  * `400 Bad Request`: Empty or whitespace query.
  * `409 Conflict`: No handbook indexed yet.
  * `422 Unprocessable Entity`: Question exceeds 500 characters or invalid JSON.
  * `500 Internal Server Error`: Generation or retrieval error.
