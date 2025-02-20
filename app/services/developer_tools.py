from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import openapi_spec_validator
from openapi_generator_cli import Generator
import graphene
from graphql import GraphQLSchema
from starlette.graphql import GraphQLApp
import markdown2
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import requests
import jwt
import websockets
import yaml

from app.core.config import settings

class DeveloperToolsService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.docs = self.db.documentation
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize OpenAPI generator
        self.generator = Generator()

    async def generate_api_docs(self, api_spec: Dict) -> Dict:
        """
        Generate comprehensive API documentation.
        """
        try:
            # Validate OpenAPI spec
            await self.validate_openapi_spec(api_spec)
            
            # Generate documentation
            docs = await self.generate_documentation(api_spec)
            
            # Generate examples
            examples = await self.generate_code_examples(api_spec)
            
            return {
                "documentation": docs,
                "examples": examples,
                "spec_version": api_spec.get("openapi", "3.0.0"),
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Documentation generation failed: {str(e)}"
            )

    async def generate_sdk(
        self,
        language: str,
        api_spec: Dict
    ) -> Dict:
        """
        Generate SDK for specified language.
        """
        try:
            # Validate language support
            await self.validate_language_support(language)
            
            # Generate SDK
            sdk = await self.generate_language_sdk(language, api_spec)
            
            # Generate documentation
            docs = await self.generate_sdk_docs(sdk)
            
            return {
                "language": language,
                "sdk": sdk,
                "documentation": docs,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SDK generation failed: {str(e)}"
            )

    async def setup_graphql_endpoint(
        self,
        schema_config: Dict
    ) -> Dict:
        """
        Setup GraphQL API endpoint.
        """
        try:
            # Generate schema
            schema = await self.generate_graphql_schema(schema_config)
            
            # Setup resolvers
            resolvers = await self.setup_graphql_resolvers(schema)
            
            # Setup playground
            playground = await self.setup_graphql_playground(schema)
            
            return {
                "schema": schema,
                "resolvers": resolvers,
                "playground": playground,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"GraphQL setup failed: {str(e)}"
            )

    async def setup_websocket_api(
        self,
        websocket_config: Dict
    ) -> Dict:
        """
        Setup WebSocket API endpoint.
        """
        try:
            # Setup WebSocket server
            server = await self.setup_websocket_server(websocket_config)
            
            # Configure handlers
            handlers = await self.configure_websocket_handlers(server)
            
            # Setup authentication
            auth = await self.setup_websocket_auth(server)
            
            return {
                "server": server,
                "handlers": handlers,
                "auth": auth,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"WebSocket setup failed: {str(e)}"
            )

    async def create_api_console(self, config: Dict) -> Dict:
        """
        Create interactive API console.
        """
        try:
            # Setup console
            console = await self.setup_api_console(config)
            
            # Configure authentication
            auth = await self.setup_console_auth(console)
            
            # Setup request builder
            builder = await self.setup_request_builder(console)
            
            return {
                "console": console,
                "auth": auth,
                "builder": builder,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Console creation failed: {str(e)}"
            )

    async def create_webhook_simulator(
        self,
        webhook_config: Dict
    ) -> Dict:
        """
        Create webhook testing simulator.
        """
        try:
            # Setup simulator
            simulator = await self.setup_webhook_simulator(webhook_config)
            
            # Configure endpoints
            endpoints = await self.configure_webhook_endpoints(simulator)
            
            # Setup event generator
            generator = await self.setup_event_generator(simulator)
            
            return {
                "simulator": simulator,
                "endpoints": endpoints,
                "generator": generator,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Webhook simulator creation failed: {str(e)}"
            )

    async def generate_postman_collection(
        self,
        api_spec: Dict
    ) -> Dict:
        """
        Generate Postman collection.
        """
        try:
            # Generate collection
            collection = await self.create_postman_collection(api_spec)
            
            # Add examples
            examples = await self.add_collection_examples(collection)
            
            # Add tests
            tests = await self.add_collection_tests(collection)
            
            return {
                "collection": collection,
                "examples": examples,
                "tests": tests,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Collection generation failed: {str(e)}"
            )

    async def setup_api_explorer(self, config: Dict) -> Dict:
        """
        Setup interactive API explorer.
        """
        try:
            # Setup explorer
            explorer = await self.setup_explorer(config)
            
            # Configure authentication
            auth = await self.setup_explorer_auth(explorer)
            
            # Setup documentation
            docs = await self.setup_explorer_docs(explorer)
            
            return {
                "explorer": explorer,
                "auth": auth,
                "docs": docs,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Explorer setup failed: {str(e)}"
            )

    async def validate_openapi_spec(self, spec: Dict) -> None:
        """
        Validate OpenAPI specification.
        """
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                openapi_spec_validator.validate_spec,
                spec
            )
        except Exception as e:
            raise ValueError(f"Invalid OpenAPI spec: {str(e)}")

    async def generate_documentation(self, spec: Dict) -> Dict:
        """
        Generate API documentation.
        """
        try:
            docs = {
                "info": spec.get("info", {}),
                "servers": spec.get("servers", []),
                "paths": await self.process_paths(spec.get("paths", {})),
                "components": await self.process_components(
                    spec.get("components", {})
                )
            }
            
            return docs
        except Exception as e:
            raise ValueError(f"Documentation generation failed: {str(e)}")

    async def generate_code_examples(self, spec: Dict) -> Dict:
        """
        Generate code examples.
        """
        try:
            examples = {}
            for path, methods in spec.get("paths", {}).items():
                examples[path] = {}
                for method, details in methods.items():
                    examples[path][method] = await self.generate_examples(
                        path,
                        method,
                        details
                    )
            return examples
        except Exception as e:
            raise ValueError(f"Example generation failed: {str(e)}")

    async def validate_language_support(self, language: str) -> None:
        """
        Validate SDK language support.
        """
        supported_languages = [
            "python",
            "javascript",
            "java",
            "csharp",
            "go",
            "ruby",
            "php"
        ]
        
        if language.lower() not in supported_languages:
            raise ValueError(f"Language {language} not supported")

    async def generate_language_sdk(
        self,
        language: str,
        spec: Dict
    ) -> Dict:
        """
        Generate SDK for language.
        """
        try:
            config = {
                "generatorName": f"{language}-client",
                "inputSpec": spec,
                "outputDir": f"./sdk/{language}"
            }
            
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.generator.generate,
                config
            )
            
            return {
                "language": language,
                "path": f"./sdk/{language}",
                "files": await self.get_sdk_files(f"./sdk/{language}")
            }
        except Exception as e:
            raise ValueError(f"SDK generation failed: {str(e)}")

    async def generate_sdk_docs(self, sdk: Dict) -> Dict:
        """
        Generate SDK documentation.
        """
        try:
            return {
                "readme": await self.generate_readme(sdk),
                "api_docs": await self.generate_api_docs(sdk),
                "examples": await self.generate_sdk_examples(sdk)
            }
        except Exception:
            return {}
