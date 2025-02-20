from datetime import datetime
from typing import Dict, List, Optional
import json
import yaml
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.openapi.utils import get_openapi
import httpx
import jinja2
import os
from pathlib import Path

from app.core.config import settings

class DeveloperService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.sdk_logs = self.db.sdk_logs
        self.api_docs = self.db.api_docs
        self.templates = jinja2.Environment(
            loader=jinja2.FileSystemLoader("app/templates/sdk")
        )

    async def generate_sdk(self, language: str, version: str) -> Dict:
        """
        Generate SDK for specified language.
        """
        try:
            # Get OpenAPI schema
            schema = self.get_openapi_schema()
            
            # Load language-specific template
            template = self.templates.get_template(f"{language}/client.{self.get_extension(language)}")
            
            # Generate SDK code
            sdk_code = template.render(
                schema=schema,
                version=version,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # Create SDK package
            package_path = await self.create_sdk_package(language, version, sdk_code)
            
            # Log SDK generation
            await self.sdk_logs.insert_one({
                "language": language,
                "version": version,
                "timestamp": datetime.utcnow(),
                "schema_version": schema.get("info", {}).get("version")
            })
            
            return {
                "language": language,
                "version": version,
                "package_path": package_path
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SDK generation failed: {str(e)}"
            )

    def get_openapi_schema(self) -> Dict:
        """
        Get OpenAPI schema for the API.
        """
        from app.main import app  # Import here to avoid circular imports
        
        return get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes
        )

    def get_extension(self, language: str) -> str:
        """
        Get file extension for language.
        """
        extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "csharp": "cs",
            "go": "go",
            "ruby": "rb",
            "php": "php"
        }
        return extensions.get(language, "txt")

    async def create_sdk_package(
        self,
        language: str,
        version: str,
        sdk_code: str
    ) -> str:
        """
        Create SDK package with necessary files.
        """
        # Create package directory
        package_dir = f"generated_sdks/{language}/{version}"
        os.makedirs(package_dir, exist_ok=True)
        
        # Write SDK code
        main_file = f"client.{self.get_extension(language)}"
        with open(f"{package_dir}/{main_file}", "w") as f:
            f.write(sdk_code)
        
        # Generate package files
        await self.generate_package_files(language, version, package_dir)
        
        return package_dir

    async def generate_package_files(
        self,
        language: str,
        version: str,
        package_dir: str
    ) -> None:
        """
        Generate necessary package files based on language.
        """
        if language == "python":
            await self.generate_python_package_files(version, package_dir)
        elif language in ["javascript", "typescript"]:
            await self.generate_node_package_files(version, package_dir)
        # Add more language-specific package generation

    async def generate_python_package_files(
        self,
        version: str,
        package_dir: str
    ) -> None:
        """
        Generate Python package files.
        """
        # Create setup.py
        setup_template = self.templates.get_template("python/setup.py.jinja2")
        setup_content = setup_template.render(version=version)
        
        with open(f"{package_dir}/setup.py", "w") as f:
            f.write(setup_content)
        
        # Create requirements.txt
        with open(f"{package_dir}/requirements.txt", "w") as f:
            f.write("requests>=2.25.1\npydantic>=1.8.2\n")
        
        # Create README.md
        readme_template = self.templates.get_template("python/README.md.jinja2")
        readme_content = readme_template.render(version=version)
        
        with open(f"{package_dir}/README.md", "w") as f:
            f.write(readme_content)

    async def generate_node_package_files(
        self,
        version: str,
        package_dir: str
    ) -> None:
        """
        Generate Node.js package files.
        """
        # Create package.json
        package_template = self.templates.get_template("node/package.json.jinja2")
        package_content = package_template.render(version=version)
        
        with open(f"{package_dir}/package.json", "w") as f:
            f.write(package_content)
        
        # Create README.md
        readme_template = self.templates.get_template("node/README.md.jinja2")
        readme_content = readme_template.render(version=version)
        
        with open(f"{package_dir}/README.md", "w") as f:
            f.write(readme_content)

    async def generate_api_documentation(self) -> Dict:
        """
        Generate comprehensive API documentation.
        """
        try:
            schema = self.get_openapi_schema()
            
            # Generate Markdown documentation
            markdown_docs = await self.generate_markdown_docs(schema)
            
            # Generate Postman collection
            postman_collection = await self.generate_postman_collection(schema)
            
            # Store documentation
            doc_version = schema.get("info", {}).get("version")
            await self.api_docs.insert_one({
                "version": doc_version,
                "markdown": markdown_docs,
                "postman_collection": postman_collection,
                "timestamp": datetime.utcnow()
            })
            
            return {
                "version": doc_version,
                "formats": ["markdown", "postman"]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Documentation generation failed: {str(e)}"
            )

    async def generate_markdown_docs(self, schema: Dict) -> str:
        """
        Generate Markdown documentation from OpenAPI schema.
        """
        template = self.templates.get_template("docs/api.md.jinja2")
        return template.render(schema=schema)

    async def generate_postman_collection(self, schema: Dict) -> Dict:
        """
        Generate Postman collection from OpenAPI schema.
        """
        collection = {
            "info": {
                "name": schema.get("info", {}).get("title"),
                "description": schema.get("info", {}).get("description"),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        # Convert paths to Postman format
        for path, methods in schema.get("paths", {}).items():
            for method, details in methods.items():
                collection["item"].append({
                    "name": details.get("summary", path),
                    "request": {
                        "method": method.upper(),
                        "url": {
                            "raw": f"{{baseUrl}}{path}",
                            "host": ["{{baseUrl}}"],
                            "path": path.strip("/").split("/")
                        },
                        "description": details.get("description", ""),
                        "header": [],
                        "body": self.generate_request_body(details)
                    }
                })
        
        return collection

    def generate_request_body(self, endpoint_details: Dict) -> Dict:
        """
        Generate request body for Postman collection.
        """
        request_body = endpoint_details.get("requestBody", {})
        if not request_body:
            return {}
        
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        
        return {
            "mode": "raw",
            "raw": json.dumps(json_content.get("example", {}), indent=2),
            "options": {
                "raw": {
                    "language": "json"
                }
            }
        }

    async def create_webhook_simulator(self, event_type: str, payload: Dict) -> Dict:
        """
        Create a webhook simulation.
        """
        try:
            # Validate event type and payload
            if not await self.validate_webhook_event(event_type, payload):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid webhook event or payload"
                )
            
            # Create simulation
            simulation = {
                "event_type": event_type,
                "payload": payload,
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            
            result = await self.db.webhook_simulations.insert_one(simulation)
            simulation["id"] = str(result.inserted_id)
            
            # Trigger webhook in background
            await self.trigger_webhook_simulation(simulation)
            
            return simulation
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Webhook simulation failed: {str(e)}"
            )

    async def validate_webhook_event(self, event_type: str, payload: Dict) -> bool:
        """
        Validate webhook event and payload.
        """
        # Implementation would validate against schema
        return True

    async def trigger_webhook_simulation(self, simulation: Dict) -> None:
        """
        Trigger webhook simulation.
        """
        # Implementation would send webhook to configured endpoint
        pass

    async def get_interactive_api_console(self) -> Dict:
        """
        Get interactive API console configuration.
        """
        try:
            schema = self.get_openapi_schema()
            
            return {
                "schema": schema,
                "endpoints": [
                    {
                        "path": path,
                        "method": method,
                        "summary": details.get("summary"),
                        "parameters": details.get("parameters", []),
                        "requestBody": details.get("requestBody")
                    }
                    for path, methods in schema.get("paths", {}).items()
                    for method, details in methods.items()
                ],
                "authentication": {
                    "types": ["api_key", "oauth2", "jwt"],
                    "oauth2_config": settings.OAUTH2_CONFIG
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get API console: {str(e)}"
            )
