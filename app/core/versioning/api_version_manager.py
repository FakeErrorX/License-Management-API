from typing import Dict, Any, List, Optional
from datetime import datetime
import semver
from app.core.logger import logger
from app.models.versioning import APIVersion, VersionMigration, VersionCompatibility

class APIVersionManager:
    def __init__(self):
        self.versions: Dict[str, APIVersion] = {}
        self.migrations: Dict[str, List[VersionMigration]] = {}
        self.compatibility_matrix: Dict[str, Dict[str, VersionCompatibility]] = {}
        
    async def manage_version_lifecycle(self, version: str) -> Dict[str, Any]:
        try:
            # Check version compatibility
            compatibility = await self._check_version_compatibility(version)
            
            # Plan deprecation if needed
            if await self._should_deprecate(version):
                await self._plan_version_deprecation(version)
                
            # Generate migration paths
            migrations = await self._generate_migration_paths(version)
            
            return {
                "version": version,
                "compatibility": compatibility,
                "migrations": migrations,
                "status": self.versions[version].status
            }
        except Exception as e:
            logger.error(f"Version lifecycle management failed: {str(e)}")
            raise

    async def _check_version_compatibility(self, version: str) -> VersionCompatibility:
        # Check compatibility with other versions
        compatibility = VersionCompatibility(
            version=version,
            compatible_versions=[],
            breaking_changes=[],
            timestamp=datetime.utcnow()
        )
        
        for other_version in self.versions:
            if await self._are_versions_compatible(version, other_version):
                compatibility.compatible_versions.append(other_version)
            else:
                changes = await self._identify_breaking_changes(version, other_version)
                compatibility.breaking_changes.extend(changes)
                
        return compatibility 