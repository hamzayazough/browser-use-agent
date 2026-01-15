"""
Embedding Service - Generate OpenAI embeddings for knowledge chunks
"""
import asyncio
import logging
from typing import List, Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.schemas.content_extraction import EmbeddingConfig

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating OpenAI embeddings"""
    
    def __init__(
        self,
        api_key: str,
        config: Optional[EmbeddingConfig] = None
    ):
        """
        Initialize Embedding Service
        
        Args:
            api_key: OpenAI API key
            config: Optional embedding configuration
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.config = config or EmbeddingConfig()
        self.total_tokens_used = 0
        self.total_api_calls = 0
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            1536-dimensional embedding vector
        """
        try:
            # Clean text
            text = self._clean_text(text)
            
            # Call OpenAI API
            response = await self.client.embeddings.create(
                model=self.config.model,
                input=text,
                dimensions=self.config.dimensions
            )
            
            # Track usage
            self.total_tokens_used += response.usage.total_tokens
            self.total_api_calls += 1
            
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding (tokens: {response.usage.total_tokens})")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise
    
    async def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            
            logger.info(f"Processing embedding batch {i//self.config.batch_size + 1} ({len(batch)} texts)")
            
            try:
                # Clean all texts
                cleaned_batch = [self._clean_text(text) for text in batch]
                
                # Call OpenAI API
                response = await self.client.embeddings.create(
                    model=self.config.model,
                    input=cleaned_batch,
                    dimensions=self.config.dimensions
                )
                
                # Track usage
                self.total_tokens_used += response.usage.total_tokens
                self.total_api_calls += 1
                
                # Extract embeddings
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                
                logger.info(f"Batch complete (tokens: {response.usage.total_tokens})")
                
                # Rate limiting
                if i + self.config.batch_size < len(texts):
                    await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Batch embedding failed: {str(e)}")
                # Generate embeddings one by one for failed batch
                for text in batch:
                    try:
                        embedding = await self.generate_embedding(text)
                        embeddings.append(embedding)
                    except:
                        # Use zero vector as fallback
                        logger.warning(f"Using zero vector for failed embedding")
                        embeddings.append([0.0] * self.config.dimensions)
        
        return embeddings
    
    def _clean_text(self, text: str) -> str:
        """Clean text before embedding"""
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long (OpenAI limit: 8191 tokens ≈ 32k chars)
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters")
        
        return text
    
    def get_usage_stats(self) -> dict:
        """Get embedding usage statistics"""
        estimated_cost = (self.total_tokens_used / 1_000_000) * 0.02  # $0.02 per 1M tokens
        
        return {
            "total_api_calls": self.total_api_calls,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost_usd": round(estimated_cost, 4),
            "model": self.config.model
        }
