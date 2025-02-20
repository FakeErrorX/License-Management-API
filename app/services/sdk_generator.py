from typing import Dict, List
from fastapi import HTTPException
import json
import os
from jinja2 import Template
from app.core.config import settings

class SDKGenerator:
    def __init__(self):
        self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.load_templates()

    def load_templates(self):
        """Load SDK templates for different languages."""
        self.templates = {
            "python": self._load_template("python_sdk.py.j2"),
            "javascript": self._load_template("javascript_sdk.js.j2"),
            "java": self._load_template("java_sdk.java.j2"),
            "csharp": self._load_template("csharp_sdk.cs.j2"),
            "go": self._load_template("go_sdk.go.j2")
        }

    def _load_template(self, template_name: str) -> Template:
        """Load a specific template file."""
        template_path = os.path.join(self.templates_dir, template_name)
        with open(template_path, "r") as f:
            return Template(f.read())

    async def generate_sdk(self, language: str, api_spec: Dict) -> Dict:
        """Generate SDK for specified language."""
        try:
            if language not in self.templates:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported language: {language}"
                )

            # Generate SDK code
            template = self.templates[language]
            sdk_code = template.render(
                api_spec=api_spec,
                base_url=settings.API_URL,
                version=settings.VERSION
            )

            # Generate documentation
            docs = await self._generate_sdk_docs(language, api_spec)

            # Generate examples
            examples = await self._generate_sdk_examples(language, api_spec)

            return {
                "language": language,
                "sdk_code": sdk_code,
                "documentation": docs,
                "examples": examples,
                "version": settings.VERSION
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"SDK generation failed: {str(e)}"
            )

    async def generate_multi_language_sdk(self, api_spec: Dict) -> Dict:
        """Generate SDKs for all supported languages."""
        try:
            sdks = {}
            for language in self.templates.keys():
                sdk = await self.generate_sdk(language, api_spec)
                sdks[language] = sdk

            return {
                "sdks": sdks,
                "version": settings.VERSION,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Multi-language SDK generation failed: {str(e)}"
            )

    async def _generate_sdk_docs(self, language: str, api_spec: Dict) -> str:
        """Generate SDK documentation."""
        doc_template = self._load_template(f"{language}_docs.md.j2")
        return doc_template.render(
            api_spec=api_spec,
            version=settings.VERSION
        )

    async def _generate_sdk_examples(self, language: str, api_spec: Dict) -> List[Dict]:
        """Generate SDK usage examples."""
        examples = []
        for path, methods in api_spec["paths"].items():
            for method, details in methods.items():
                example = await self._generate_method_example(
                    language,
                    path,
                    method,
                    details
                )
                examples.append(example)
        return examples

    async def _generate_method_example(
        self,
        language: str,
        path: str,
        method: str,
        details: Dict
    ) -> Dict:
        """Generate example for a specific API method."""
        example_template = self._load_template(f"{language}_example.{language}.j2")
        
        # Generate example code
        example_code = example_template.render(
            path=path,
            method=method,
            details=details
        )

        return {
            "path": path,
            "method": method,
            "description": details.get("description", ""),
            "code": example_code
        }

    async def generate_sdk_package(self, language: str, api_spec: Dict) -> Dict:
        """Generate complete SDK package with dependencies."""
        try:
            # Generate base SDK
            sdk = await self.generate_sdk(language, api_spec)

            # Generate package files
            package_files = await self._generate_package_files(language, sdk)

            # Generate tests
            tests = await self._generate_sdk_tests(language, api_spec)

            return {
                "language": language,
                "sdk": sdk,
                "package_files": package_files,
                "tests": tests,
                "version": settings.VERSION
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"SDK package generation failed: {str(e)}"
            )

    async def _generate_package_files(self, language: str, sdk: Dict) -> Dict:
        """Generate necessary package files."""
        package_files = {}

        if language == "python":
            package_files["setup.py"] = self._generate_python_setup(sdk)
            package_files["requirements.txt"] = self._generate_python_requirements()
        elif language == "javascript":
            package_files["package.json"] = self._generate_npm_package(sdk)
        elif language == "java":
            package_files["pom.xml"] = self._generate_maven_pom(sdk)
        elif language == "csharp":
            package_files["csproj"] = self._generate_csharp_project(sdk)
        elif language == "go":
            package_files["go.mod"] = self._generate_go_mod(sdk)

        return package_files

    async def _generate_sdk_tests(self, language: str, api_spec: Dict) -> List[Dict]:
        """Generate SDK tests."""
        test_template = self._load_template(f"{language}_tests.{language}.j2")
        
        tests = []
        for path, methods in api_spec["paths"].items():
            for method, details in methods.items():
                test = test_template.render(
                    path=path,
                    method=method,
                    details=details
                )
                tests.append({
                    "path": path,
                    "method": method,
                    "test_code": test
                })
        
        return tests
