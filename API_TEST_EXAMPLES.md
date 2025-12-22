# API Test Examples - What to Enter

## Registration Endpoint (`POST /api/v1/auth/register`)

### Example Request Body:

```json
{
  "email": "john.doe@student.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "student_id": "STU2024001"
}
```

### Or Use This Simpler Example:

```json
{
  "email": "test@student.com",
  "password": "test123",
  "full_name": "Test Student",
  "student_id": "TEST001"
}
```

### Field Descriptions:

- **email**: Any valid email address (must be unique)
- **password**: Any password (will be hashed)
- **full_name**: Student's full name (optional)
- **student_id**: Unique student ID (optional)

---

## Login Endpoint (`POST /api/v1/auth/login`)

### Example Request Body:

```json
{
  "email": "test@student.com",
  "password": "test123"
}
```

**Use the same email and password you used for registration!**

---

## Upload Endpoint (`POST /api/v1/upload`)

### Steps:
1. Click "Authorize" button (top right)
2. Enter: `Bearer YOUR_TOKEN_HERE` (token from login)
3. Click "Authorize" and "Close"
4. Click "Try it out"
5. Click "Choose File"
6. Select a PDF or DOCX file from your computer
7. Click "Execute"

**No JSON needed** - just upload a file!

---

## Get Analysis (`GET /api/v1/analysis/{analysis_id}`)

### Example:
- **analysis_id**: `1` (or any number from upload response)

**Just enter the number** in the path parameter field.

---

## Search Sources (`GET /api/v1/sources`)

### Query Parameters:

- **query**: `machine learning` (or any search term)
- **top_k**: `5` (number of results to return)

### Example:
- query: `artificial intelligence`
- top_k: `5`

---

## Quick Test Sequence

### Step 1: Register
```json
{
  "email": "demo@student.com",
  "password": "demo123",
  "full_name": "Demo Student",
  "student_id": "DEMO001"
}
```

### Step 2: Login (use same credentials)
```json
{
  "email": "demo@student.com",
  "password": "demo123"
}
```

### Step 3: Copy the `access_token` from login response

### Step 4: Authorize (top right button)
- Enter: `Bearer YOUR_ACCESS_TOKEN`
- Click "Authorize"

### Step 5: Upload File
- Click "Choose File"
- Select any PDF or DOCX file
- Click "Execute"

### Step 6: Get Analysis
- Use the `assignment_id` from upload response
- Enter it in the `analysis_id` field
- Click "Execute"

---

## All Example Values Summary

| Endpoint | Field | Example Value |
|----------|-------|---------------|
| **Register** | email | `test@student.com` |
| | password | `test123` |
| | full_name | `Test Student` |
| | student_id | `TEST001` |
| **Login** | email | `test@student.com` |
| | password | `test123` |
| **Upload** | file | (Select PDF/DOCX file) |
| **Analysis** | analysis_id | `1` |
| **Sources** | query | `machine learning` |
| | top_k | `5` |

---

**Just copy and paste these examples into the Swagger UI!** 🚀

