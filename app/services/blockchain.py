from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_typing import Address
import solcx
from solcx import compile_source
import ipfshttpclient
import requests
import logging
import sentry_sdk
from cryptography.fernet import Fernet

from app.core.config import settings

class BlockchainService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.blockchain = self.db.blockchain
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        
        # Initialize IPFS
        self.ipfs = ipfshttpclient.connect()
        
        # Initialize encryption
        self.fernet = Fernet(settings.ENCRYPTION_KEY)

    async def create_nft_license(
        self,
        license_data: Dict
    ) -> Dict:
        """
        Create NFT-based license.
        """
        try:
            # Generate NFT metadata
            metadata = await self.generate_nft_metadata(license_data)
            
            # Store on IPFS
            ipfs_hash = await self.store_on_ipfs(metadata)
            
            # Mint NFT
            nft = await self.mint_nft(ipfs_hash, license_data)
            
            return {
                "license_id": nft["token_id"],
                "metadata": metadata,
                "ipfs_hash": ipfs_hash,
                "blockchain_tx": nft["transaction"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"NFT license creation failed: {str(e)}"
            )

    async def manage_smart_contracts(
        self,
        contract_data: Dict
    ) -> Dict:
        """
        Manage license smart contracts.
        """
        try:
            # Deploy contract
            contract = await self.deploy_smart_contract(contract_data)
            
            # Configure contract
            config = await self.configure_contract(contract)
            
            # Setup events
            events = await self.setup_contract_events(contract)
            
            return {
                "contract_address": contract["address"],
                "config": config,
                "events": events,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Smart contract management failed: {str(e)}"
            )

    async def manage_decentralized_storage(
        self,
        storage_data: Dict
    ) -> Dict:
        """
        Manage decentralized license storage.
        """
        try:
            # Configure storage
            config = await self.configure_storage(storage_data)
            
            # Setup replication
            replication = await self.setup_replication(config)
            
            # Monitor storage
            monitoring = await self.monitor_storage(config)
            
            return {
                "config_id": config["config_id"],
                "replication": replication,
                "monitoring": monitoring,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Decentralized storage failed: {str(e)}"
            )

    async def manage_multi_signature(
        self,
        signature_config: Dict
    ) -> Dict:
        """
        Manage multi-signature approvals.
        """
        try:
            # Configure signatures
            config = await self.configure_multi_sig(signature_config)
            
            # Setup approvals
            approvals = await self.setup_approvals(config)
            
            # Monitor signatures
            monitoring = await self.monitor_signatures(config)
            
            return {
                "config_id": config["config_id"],
                "approvals": approvals,
                "monitoring": monitoring,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Multi-signature management failed: {str(e)}"
            )

    async def manage_immutable_records(
        self,
        record_data: Dict
    ) -> Dict:
        """
        Manage immutable licensing records.
        """
        try:
            # Create record
            record = await self.create_immutable_record(record_data)
            
            # Store record
            storage = await self.store_record(record)
            
            # Verify record
            verification = await self.verify_record(record)
            
            return {
                "record_id": record["record_id"],
                "storage": storage,
                "verification": verification,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Immutable record management failed: {str(e)}"
            )

    async def manage_blockchain_sync(
        self,
        sync_config: Dict
    ) -> Dict:
        """
        Manage blockchain synchronization.
        """
        try:
            # Configure sync
            config = await self.configure_sync(sync_config)
            
            # Setup sync
            sync = await self.setup_blockchain_sync(config)
            
            # Monitor sync
            monitoring = await self.monitor_sync(sync)
            
            return {
                "config_id": config["config_id"],
                "sync": sync,
                "monitoring": monitoring,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Blockchain sync failed: {str(e)}"
            )

    async def manage_smart_renewals(
        self,
        renewal_config: Dict
    ) -> Dict:
        """
        Manage smart contract renewals.
        """
        try:
            # Configure renewals
            config = await self.configure_renewals(renewal_config)
            
            # Setup automation
            automation = await self.setup_renewal_automation(config)
            
            # Monitor renewals
            monitoring = await self.monitor_renewals(automation)
            
            return {
                "config_id": config["config_id"],
                "automation": automation,
                "monitoring": monitoring,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Smart renewal management failed: {str(e)}"
            )

    async def generate_nft_metadata(self, license_data: Dict) -> Dict:
        """
        Generate NFT metadata.
        """
        try:
            return {
                "name": f"License {license_data['license_id']}",
                "description": license_data.get("description", ""),
                "image": await self.generate_nft_image(license_data),
                "attributes": await self.generate_nft_attributes(license_data)
            }
        except Exception:
            return {}

    async def store_on_ipfs(self, metadata: Dict) -> str:
        """
        Store metadata on IPFS.
        """
        try:
            # Convert to JSON
            json_data = json.dumps(metadata)
            
            # Add to IPFS
            result = await self.ipfs.add(json_data)
            
            return result["hash"]
        except Exception:
            return ""

    async def mint_nft(self, ipfs_hash: str, license_data: Dict) -> Dict:
        """
        Mint NFT on blockchain.
        """
        try:
            # Get contract
            contract = self.w3.eth.contract(
                address=settings.NFT_CONTRACT_ADDRESS,
                abi=settings.NFT_CONTRACT_ABI
            )
            
            # Build transaction
            tx = contract.functions.mint(
                license_data["owner_address"],
                ipfs_hash
            ).buildTransaction({
                "from": settings.ADMIN_ADDRESS,
                "nonce": self.w3.eth.getTransactionCount(settings.ADMIN_ADDRESS)
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.signTransaction(
                tx,
                settings.ADMIN_PRIVATE_KEY
            )
            tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            
            return {
                "token_id": contract.functions.totalSupply().call(),
                "transaction": tx_hash.hex()
            }
        except Exception:
            return {}
