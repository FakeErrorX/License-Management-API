from typing import Dict, Any, Optional
from datetime import datetime
from web3 import Web3
from eth_account import Account
from app.core.logger import logger
from app.models.blockchain import BlockchainTransaction, SmartContract, NFTLicense

class BlockchainManager:
    def __init__(self, web3_provider: str):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.contracts: Dict[str, SmartContract] = {}
        
    async def create_nft_license(self, user_id: str, license_data: Dict[str, Any]) -> NFTLicense:
        try:
            # Create NFT license on blockchain
            contract = self.contracts.get('license_nft')
            if not contract:
                raise ValueError("NFT contract not initialized")
                
            # Mint new NFT
            tx_hash = await self._mint_license_nft(contract, user_id, license_data)
            
            return NFTLicense(
                token_id=tx_hash,
                owner=user_id,
                metadata=license_data,
                created_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to create NFT license: {str(e)}")
            raise
            
    async def verify_license(self, token_id: str) -> bool:
        try:
            contract = self.contracts.get('license_nft')
            return await self._verify_nft_ownership(contract, token_id)
        except Exception as e:
            logger.error(f"License verification failed: {str(e)}")
            return False 