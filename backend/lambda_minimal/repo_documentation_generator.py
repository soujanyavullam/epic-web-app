import json
import boto3
import os
import requests
import base64
from typing import Dict, Any, List
import urllib.parse
from decimal import Decimal
from datetime import datetime
import re

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('book-embeddings-dev')
bedrock = boto3.client('bedrock-runtime')

def extract_repo_info(github_url: str) -> Dict[str, str]:
    """Extract owner and repo name from GitHub URL."""
    # Handle various GitHub URL formats
    patterns = [
        r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
        r'github\.com/([^/]+)/([^/]+?)(?:/.*)?$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, github_url)
        if match:
            return {
                'owner': match.group(1),
                'repo': match.group(2).replace('.git', '')
            }
    
    raise ValueError(f"Invalid GitHub URL format: {github_url}")

def fetch_repo_content(owner: str, repo: str, token: str = None) -> Dict[str, Any]:
    """Fetch repository content using GitHub API."""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    
    # Get repository info
    repo_url = f'https://api.github.com/repos/{owner}/{repo}'
    response = requests.get(repo_url, headers=headers)
    response.raise_for_status()
    repo_info = response.json()
    
    # Get repository contents (recursive)
    contents_url = f'https://api.github.com/repos/{owner}/{repo}/contents'
    response = requests.get(contents_url, headers=headers)
    response.raise_for_status()
    contents = response.json()
    
    return {
        'repo_info': repo_info,
        'contents': contents
    }

def fetch_file_content(owner: str, repo: str, path: str, token: str = None) -> str:
    """Fetch specific file content from GitHub."""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    content_data = response.json()
    if content_data.get('encoding') == 'base64':
        return base64.b64decode(content_data['content']).decode('utf-8')
    return content_data['content']

def generate_documentation(repo_info: Dict, contents: List, owner: str, repo: str, token: str = None) -> str:
    """Generate comprehensive documentation from repository content."""
    
    doc_parts = []
    
    # 1. Repository Overview
    doc_parts.append(f"# {repo_info['name']}\n")
    doc_parts.append(f"**Repository**: {owner}/{repo}\n")
    doc_parts.append(f"**Description**: {repo_info.get('description', 'No description provided')}\n")
    doc_parts.append(f"**Language**: {repo_info.get('language', 'Unknown')}\n")
    doc_parts.append(f"**Stars**: {repo_info.get('stargazers_count', 0)}\n")
    doc_parts.append(f"**Forks**: {repo_info.get('forks_count', 0)}\n")
    doc_parts.append(f"**Created**: {repo_info.get('created_at', 'Unknown')}\n")
    doc_parts.append(f"**Last Updated**: {repo_info.get('updated_at', 'Unknown')}\n\n")
    
    # 2. README Content
    readme_files = ['README.md', 'README.txt', 'readme.md', 'readme.txt']
    for readme in readme_files:
        try:
            readme_content = fetch_file_content(owner, repo, readme, token)
            doc_parts.append(f"## README\n\n{readme_content}\n\n")
            break
        except:
            continue
    
    # 3. Project Structure
    doc_parts.append("## Project Structure\n\n")
    structure = analyze_project_structure(contents)
    doc_parts.append(structure)
    doc_parts.append("\n")
    
    # 4. Key Files Analysis
    key_files = ['package.json', 'requirements.txt', 'setup.py', 'Cargo.toml', 'pom.xml', 'build.gradle']
    for file in key_files:
        try:
            content = fetch_file_content(owner, repo, file, token)
            doc_parts.append(f"## {file}\n\n```\n{content}\n```\n\n")
        except:
            continue
    
    # 5. Code Documentation (from comments)
    code_docs = extract_code_documentation(contents, owner, repo, token)
    if code_docs:
        doc_parts.append("## Code Documentation\n\n")
        doc_parts.append(code_docs)
        doc_parts.append("\n")
    
    return "\n".join(doc_parts)

def analyze_project_structure(contents: List) -> str:
    """Analyze and document project structure."""
    structure = []
    
    def process_contents(items, level=0):
        for item in items:
            indent = "  " * level
            if item['type'] == 'dir':
                structure.append(f"{indent}📁 {item['name']}/")
                # Note: For simplicity, we're not recursively fetching subdirectories
                # In a full implementation, you'd want to fetch subdirectory contents
            else:
                ext = os.path.splitext(item['name'])[1]
                if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs']:
                    structure.append(f"{indent}📄 {item['name']} (code)")
                elif ext in ['.md', '.txt', '.rst']:
                    structure.append(f"{indent}📄 {item['name']} (documentation)")
                elif ext in ['.json', '.yaml', '.yml', '.toml']:
                    structure.append(f"{indent}📄 {item['name']} (config)")
                else:
                    structure.append(f"{indent}📄 {item['name']}")
    
    process_contents(contents)
    return "\n".join(structure)

def extract_code_documentation(contents: List, owner: str, repo: str, token: str = None) -> str:
    """Extract and generate documentation from code analysis."""
    code_files = []
    
    # Find code files
    for item in contents:
        if item['type'] == 'file':
            ext = os.path.splitext(item['name'])[1]
            if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs']:
                code_files.append(item['path'])
    
    # Generate documentation from first few code files
    docs = []
    for file_path in code_files[:8]:  # Increased limit to 8 files
        try:
            content = fetch_file_content(owner, repo, file_path, token)
            file_docs = generate_code_documentation(content, file_path)
            if file_docs:
                docs.append(f"### {file_path}\n\n{file_docs}\n")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    return "\n".join(docs)

def generate_code_documentation(content: str, file_path: str) -> str:
    """Generate comprehensive documentation from code analysis."""
    ext = os.path.splitext(file_path)[1]
    documentation = []
    
    if ext == '.py':
        documentation.extend(analyze_python_code(content, file_path))
    elif ext in ['.js', '.ts']:
        documentation.extend(analyze_javascript_code(content, file_path))
    elif ext in ['.java']:
        documentation.extend(analyze_java_code(content, file_path))
    elif ext in ['.cpp', '.c', '.h']:
        documentation.extend(analyze_cpp_code(content, file_path))
    elif ext in ['.go']:
        documentation.extend(analyze_go_code(content, file_path))
    elif ext in ['.rs']:
        documentation.extend(analyze_rust_code(content, file_path))
    
    return "\n".join(documentation)

def analyze_python_code(content: str, file_path: str) -> List[str]:
    """Analyze Python code and generate documentation."""
    lines = content.split('\n')
    documentation = []
    
    # Extract imports
    imports = []
    for line in lines:
        if line.strip().startswith(('import ', 'from ')):
            imports.append(line.strip())
    
    if imports:
        documentation.append("**Imports:**")
        documentation.extend([f"- {imp}" for imp in imports[:10]])  # Limit to first 10
        documentation.append("")
    
    # Extract classes
    classes = []
    for i, line in enumerate(lines):
        if line.strip().startswith('class ') and ':' in line:
            class_name = line.strip().split('class ')[1].split('(')[0].split(':')[0].strip()
            classes.append((i, class_name, line.strip()))
    
    if classes:
        documentation.append("**Classes:**")
        for line_num, class_name, class_line in classes[:5]:  # Limit to first 5
            documentation.append(f"- `{class_name}` (line {line_num + 1})")
            # Look for docstring
            for j in range(line_num + 1, min(line_num + 10, len(lines))):
                if lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''"):
                    doc_start = j
                    for k in range(j + 1, min(j + 10, len(lines))):
                        if lines[k].strip().endswith('"""') or lines[k].strip().endswith("'''"):
                            doc_content = ' '.join([lines[l].strip() for l in range(doc_start, k + 1)])
                            documentation.append(f"  - Docstring: {doc_content}")
                            break
                    break
        documentation.append("")
    
    # Extract functions
    functions = []
    for i, line in enumerate(lines):
        if line.strip().startswith('def ') and ':' in line:
            func_name = line.strip().split('def ')[1].split('(')[0].strip()
            functions.append((i, func_name, line.strip()))
    
    if functions:
        documentation.append("**Functions:**")
        for line_num, func_name, func_line in functions[:8]:  # Limit to first 8
            documentation.append(f"- `{func_name}` (line {line_num + 1})")
            # Look for docstring
            for j in range(line_num + 1, min(line_num + 10, len(lines))):
                if lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''"):
                    doc_start = j
                    for k in range(j + 1, min(j + 10, len(lines))):
                        if lines[k].strip().endswith('"""') or lines[k].strip().endswith("'''"):
                            doc_content = ' '.join([lines[l].strip() for l in range(doc_start, k + 1)])
                            documentation.append(f"  - Docstring: {doc_content}")
                            break
                    break
        documentation.append("")
    
    # Extract constants and variables
    constants = []
    for line in lines:
        if '=' in line and line.strip().isupper() and not line.strip().startswith('#'):
            constants.append(line.strip())
    
    if constants:
        documentation.append("**Constants:**")
        documentation.extend([f"- {const}" for const in constants[:5]])
        documentation.append("")
    
    # Generate code summary
    total_lines = len(lines)
    code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
    comment_lines = len([line for line in lines if line.strip().startswith('#')])
    
    documentation.append("**Code Summary:**")
    documentation.append(f"- Total lines: {total_lines}")
    documentation.append(f"- Code lines: {code_lines}")
    documentation.append(f"- Comment lines: {comment_lines}")
    documentation.append(f"- Classes: {len(classes)}")
    documentation.append(f"- Functions: {len(functions)}")
    
    return documentation

def analyze_javascript_code(content: str, file_path: str) -> List[str]:
    """Analyze JavaScript/TypeScript code and generate documentation."""
    lines = content.split('\n')
    documentation = []
    
    # Extract imports
    imports = []
    for line in lines:
        if line.strip().startswith(('import ', 'export ')):
            imports.append(line.strip())
    
    if imports:
        documentation.append("**Imports/Exports:**")
        documentation.extend([f"- {imp}" for imp in imports[:10]])
        documentation.append("")
    
    # Extract classes
    classes = []
    for i, line in enumerate(lines):
        if 'class ' in line and '{' in line:
            class_name = line.strip().split('class ')[1].split('{')[0].split('extends')[0].strip()
            classes.append((i, class_name, line.strip()))
    
    if classes:
        documentation.append("**Classes:**")
        for line_num, class_name, class_line in classes[:5]:
            documentation.append(f"- `{class_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Extract functions
    functions = []
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in ['function ', '=>', 'const ', 'let ', 'var ']) and '(' in line and ')' in line:
            # Extract function name
            if 'function ' in line:
                func_name = line.strip().split('function ')[1].split('(')[0].strip()
            elif '=>' in line:
                func_name = f"arrow_function_{i}"
            else:
                func_name = line.strip().split('(')[0].split('=')[0].strip()
            functions.append((i, func_name, line.strip()))
    
    if functions:
        documentation.append("**Functions:**")
        for line_num, func_name, func_line in functions[:8]:
            documentation.append(f"- `{func_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Generate code summary
    total_lines = len(lines)
    code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
    comment_lines = len([line for line in lines if line.strip().startswith('//')])
    
    documentation.append("**Code Summary:**")
    documentation.append(f"- Total lines: {total_lines}")
    documentation.append(f"- Code lines: {code_lines}")
    documentation.append(f"- Comment lines: {comment_lines}")
    documentation.append(f"- Classes: {len(classes)}")
    documentation.append(f"- Functions: {len(functions)}")
    
    return documentation

def analyze_java_code(content: str, file_path: str) -> List[str]:
    """Analyze Java code and generate documentation."""
    lines = content.split('\n')
    documentation = []
    
    # Extract imports
    imports = []
    for line in lines:
        if line.strip().startswith('import '):
            imports.append(line.strip())
    
    if imports:
        documentation.append("**Imports:**")
        documentation.extend([f"- {imp}" for imp in imports[:10]])
        documentation.append("")
    
    # Extract classes
    classes = []
    for i, line in enumerate(lines):
        if 'class ' in line and '{' in line:
            class_name = line.strip().split('class ')[1].split('{')[0].split('extends')[0].split('implements')[0].strip()
            classes.append((i, class_name, line.strip()))
    
    if classes:
        documentation.append("**Classes:**")
        for line_num, class_name, class_line in classes[:5]:
            documentation.append(f"- `{class_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Extract methods
    methods = []
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in ['public ', 'private ', 'protected ']) and '(' in line and ')' in line:
            method_name = line.strip().split('(')[0].split()[-1]
            methods.append((i, method_name, line.strip()))
    
    if methods:
        documentation.append("**Methods:**")
        for line_num, method_name, method_line in methods[:8]:
            documentation.append(f"- `{method_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Generate code summary
    total_lines = len(lines)
    code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
    comment_lines = len([line for line in lines if line.strip().startswith('//')])
    
    documentation.append("**Code Summary:**")
    documentation.append(f"- Total lines: {total_lines}")
    documentation.append(f"- Code lines: {code_lines}")
    documentation.append(f"- Comment lines: {comment_lines}")
    documentation.append(f"- Classes: {len(classes)}")
    documentation.append(f"- Methods: {len(methods)}")
    
    return documentation

def analyze_cpp_code(content: str, file_path: str) -> List[str]:
    """Analyze C++ code and generate documentation."""
    lines = content.split('\n')
    documentation = []
    
    # Extract includes
    includes = []
    for line in lines:
        if line.strip().startswith('#include '):
            includes.append(line.strip())
    
    if includes:
        documentation.append("**Includes:**")
        documentation.extend([f"- {inc}" for inc in includes[:10]])
        documentation.append("")
    
    # Extract classes
    classes = []
    for i, line in enumerate(lines):
        if 'class ' in line and '{' in line:
            class_name = line.strip().split('class ')[1].split('{')[0].split(':')[0].strip()
            classes.append((i, class_name, line.strip()))
    
    if classes:
        documentation.append("**Classes:**")
        for line_num, class_name, class_line in classes[:5]:
            documentation.append(f"- `{class_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Extract functions
    functions = []
    for i, line in enumerate(lines):
        if '(' in line and ')' in line and any(keyword in line for keyword in ['void ', 'int ', 'string ', 'bool ', 'float ', 'double ']):
            func_name = line.strip().split('(')[0].split()[-1]
            functions.append((i, func_name, line.strip()))
    
    if functions:
        documentation.append("**Functions:**")
        for line_num, func_name, func_line in functions[:8]:
            documentation.append(f"- `{func_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Generate code summary
    total_lines = len(lines)
    code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
    comment_lines = len([line for line in lines if line.strip().startswith('//')])
    
    documentation.append("**Code Summary:**")
    documentation.append(f"- Total lines: {total_lines}")
    documentation.append(f"- Code lines: {code_lines}")
    documentation.append(f"- Comment lines: {comment_lines}")
    documentation.append(f"- Classes: {len(classes)}")
    documentation.append(f"- Functions: {len(functions)}")
    
    return documentation

def analyze_go_code(content: str, file_path: str) -> List[str]:
    """Analyze Go code and generate documentation."""
    lines = content.split('\n')
    documentation = []
    
    # Extract imports
    imports = []
    for line in lines:
        if line.strip().startswith('import '):
            imports.append(line.strip())
    
    if imports:
        documentation.append("**Imports:**")
        documentation.extend([f"- {imp}" for imp in imports[:10]])
        documentation.append("")
    
    # Extract structs
    structs = []
    for i, line in enumerate(lines):
        if 'type ' in line and 'struct' in line:
            struct_name = line.strip().split('type ')[1].split(' struct')[0].strip()
            structs.append((i, struct_name, line.strip()))
    
    if structs:
        documentation.append("**Structs:**")
        for line_num, struct_name, struct_line in structs[:5]:
            documentation.append(f"- `{struct_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Extract functions
    functions = []
    for i, line in enumerate(lines):
        if 'func ' in line and '(' in line:
            func_name = line.strip().split('func ')[1].split('(')[0].strip()
            functions.append((i, func_name, line.strip()))
    
    if functions:
        documentation.append("**Functions:**")
        for line_num, func_name, func_line in functions[:8]:
            documentation.append(f"- `{func_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Generate code summary
    total_lines = len(lines)
    code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
    comment_lines = len([line for line in lines if line.strip().startswith('//')])
    
    documentation.append("**Code Summary:**")
    documentation.append(f"- Total lines: {total_lines}")
    documentation.append(f"- Code lines: {code_lines}")
    documentation.append(f"- Comment lines: {comment_lines}")
    documentation.append(f"- Structs: {len(structs)}")
    documentation.append(f"- Functions: {len(functions)}")
    
    return documentation

def analyze_rust_code(content: str, file_path: str) -> List[str]:
    """Analyze Rust code and generate documentation."""
    lines = content.split('\n')
    documentation = []
    
    # Extract use statements
    uses = []
    for line in lines:
        if line.strip().startswith('use '):
            uses.append(line.strip())
    
    if uses:
        documentation.append("**Use Statements:**")
        documentation.extend([f"- {use}" for use in uses[:10]])
        documentation.append("")
    
    # Extract structs
    structs = []
    for i, line in enumerate(lines):
        if 'struct ' in line and '{' in line:
            struct_name = line.strip().split('struct ')[1].split('{')[0].strip()
            structs.append((i, struct_name, line.strip()))
    
    if structs:
        documentation.append("**Structs:**")
        for line_num, struct_name, struct_line in structs[:5]:
            documentation.append(f"- `{struct_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Extract functions
    functions = []
    for i, line in enumerate(lines):
        if 'fn ' in line and '(' in line:
            func_name = line.strip().split('fn ')[1].split('(')[0].strip()
            functions.append((i, func_name, line.strip()))
    
    if functions:
        documentation.append("**Functions:**")
        for line_num, func_name, func_line in functions[:8]:
            documentation.append(f"- `{func_name}` (line {line_num + 1})")
        documentation.append("")
    
    # Generate code summary
    total_lines = len(lines)
    code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
    comment_lines = len([line for line in lines if line.strip().startswith('//')])
    
    documentation.append("**Code Summary:**")
    documentation.append(f"- Total lines: {total_lines}")
    documentation.append(f"- Code lines: {code_lines}")
    documentation.append(f"- Comment lines: {comment_lines}")
    documentation.append(f"- Structs: {len(structs)}")
    documentation.append(f"- Functions: {len(functions)}")
    
    return documentation

def chunk_text(text: str, max_chunk_size: int = 1000) -> List[str]:
    """Split text into chunks."""
    chunks = []
    current_chunk = []
    current_length = 0
    
    words = text.split()
    for word in words:
        if current_length + len(word) + (1 if current_chunk else 0) > max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + (1 if current_chunk else 0)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def get_embedding(text: str) -> List[float]:
    """Get embedding for text using Bedrock."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = bedrock.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=json.dumps({
                    'inputText': text
                })
            )
            response_body = json.loads(response['body'].read())
            return response_body['embedding']
        except Exception as e:
            print(f"Error getting embedding (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                raise

def store_chunk_in_dynamodb(book_title: str, chunk_id: str, text: str, embedding: List[float], token_count: int):
    """Store a single chunk with its embedding in DynamoDB."""
    try:
        item = {
            'book_title': book_title,
            'chunk_id': chunk_id,
            'text': text,
            'embedding': [Decimal(str(x)) for x in embedding],
            'token_count': token_count,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        table.put_item(Item=item)
        print(f"Successfully stored chunk {chunk_id} for book {book_title} in DynamoDB.")
    except Exception as e:
        print(f"Error storing chunk in DynamoDB: {e}")
        raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for generating documentation from GitHub repositories."""
    
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
            },
            'body': ''
        }
    
    try:
        body = json.loads(event['body'])
        github_url = body['github_url']
        
        # Extract repository information
        repo_info = extract_repo_info(github_url)
        owner = repo_info['owner']
        repo = repo_info['repo']
        
        # Generate book title
        book_title = f"{owner}-{repo}"
        
        print(f"Processing GitHub repository: {owner}/{repo}")
        
        # Fetch repository content
        content_data = fetch_repo_content(owner, repo)
        repo_info_data = content_data['repo_info']
        contents = content_data['contents']
        
        # Generate documentation
        documentation = generate_documentation(repo_info_data, contents, owner, repo)
        
        # Upload documentation to S3
        s3_key = f"repos/{book_title}.md"
        s3.put_object(
            Bucket=os.environ.get('S3_BUCKET_NAME', 'epic-s3-bucket-ramayana'),
            Key=s3_key,
            Body=documentation.encode('utf-8'),
            ContentType='text/markdown'
        )
        print(f"Successfully uploaded documentation to S3: {s3_key}")
        
        # Process documentation for embeddings
        chunks = chunk_text(documentation)
        print(f"Processing {len(chunks)} chunks for {book_title}")
        
        chunks_processed_count = 0
        for i, chunk_text_content in enumerate(chunks):
            try:
                embedding = get_embedding(chunk_text_content)
                chunk_id = f"{book_title}-{i:04d}"
                token_count = len(chunk_text_content)
                store_chunk_in_dynamodb(book_title, chunk_id, chunk_text_content, embedding, token_count)
                chunks_processed_count += 1
            except Exception as chunk_e:
                print(f"Failed to process chunk {i} for {book_title}: {chunk_e}")
                continue
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
            },
            'body': json.dumps({
                'message': 'Repository documentation generated successfully',
                'github_url': github_url,
                'owner': owner,
                'repo': repo,
                'book_title': book_title,
                's3_key': s3_key,
                'chunks_processed': chunks_processed_count,
                'documentation_length': len(documentation)
            })
        }
        
    except Exception as e:
        print(f"Error processing repository: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Length,Content-Range'
            },
            'body': json.dumps({
                'error': f'Failed to process repository: {str(e)}'
            })
        } 