from typing import List, Dict, Optional, Any, Tuple
import uuid
from datetime import datetime
from llm import LLMWrapper
from retrievers import ChromaRetriever
import logging
from const import always_evolve_user, always_evolve_system, optional_evolution_user, optional_evolution_system
from utils import *

logger = logging.getLogger(__name__)

class MemoryNote:
    """A memory note that represents a single unit of information in the memory system.
    
    This class encapsulates all metadata associated with a memory, including:
    - Core content and identifiers
    - Temporal information (creation and access times)
    - Semantic metadata (keywords, context, tags)
    - Relationship data (links to other memories)
    - Usage statistics (retrieval count)
    - Evolution tracking (history of changes)
    """
    
    def __init__(self, 
                 content: str,
                 id: Optional[str] = None,
                 keywords: Optional[List[str]] = None,
                 links: Optional[Dict] = None,
                 timestamp: Optional[str] = None,
                 last_accessed: Optional[str] = None,
                 context: Optional[str] = None,
                 evolution_history: Optional[List] = None,
                 category: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 tags_history: Optional[List[List[str]]] = None,
                 context_history: Optional[List[str]] = None,
                 ):
        """Initialize a new memory note with its associated metadata.
        
        Args:
            content (str): The main text content of the memory
            id (Optional[str]): Unique identifier for the memory. If None, a UUID will be generated
            keywords (Optional[List[str]]): Key terms extracted from the content
            links (Optional[Dict]): References to related memories
            timestamp (Optional[str]): Creation time in format YYYYMMDDHHMM
            last_accessed (Optional[str]): Last access time in format YYYYMMDDHHMM
            context (Optional[str]): The broader context or domain of the memory
            evolution_history (Optional[List]): Record of how the memory has evolved
            category (Optional[str]): Classification category
            tags (Optional[List[str]]): Additional classification tags
        """
        # Core content and ID
        self.content = content
        self.id = id or str(uuid.uuid4())
        
        # Semantic metadata
        self.keywords = keywords or []
        self.links = links or {}
        self.context = context or "General"
        self.category = category or "Uncategorized"
        self.tags = tags or []
        self.tags_history = tags_history or []
        self.context_history = context_history or []

        # Temporal information
        current_time = datetime.now().strftime("%Y%m%d%H%M")
        self.timestamp = timestamp or current_time
        self.last_accessed = last_accessed or current_time
        
        # Usage and evolution data
        self.evolution_history = evolution_history or []

class QAMemoryNote(MemoryNote):
    def __init__(self, 
                 question_id: str,
                 question_text: str,
                 question_type: str,
                 required_operations: List[str],
                 correct_answer: Optional[str] = None,
                 model_answer: Optional[str] = None,
                 correct_steps: Optional[List[str]] = None,
                 wrong_steps: Optional[List[str]] = None,
                 error_type: Optional[str] = None,
                 error_reason: Optional[str] = None,
                 content: str = "",
                 context: str = "",
                 tags: Optional[List[str]] = None,
                 keywords: Optional[List[str]] = None,
                 category: Optional[str] = None,
                 id: Optional[str] = None,
                 links: Optional[Dict] = None,
                 timestamp: Optional[str] = None,
                 last_accessed: Optional[str] = None,
                 evolution_history: Optional[List] = None,
                 strengthen_distance: List[List[float]] =[],
                 update_neighbour_distance: List[List[float]] =[],
                 tags_history: Optional[List[List[str]]] = None,
                 context_history: Optional[List[str]] = None):
        super().__init__(content=content,
            id=id,
            keywords=keywords,
            links=links,
            timestamp=timestamp,
            last_accessed=last_accessed,
            context=context,
            evolution_history=evolution_history,
            category=category,
            tags=tags,
            tags_history=tags_history,
            context_history=context_history)

        self.question_id = question_id
        self.question_text = question_text
        self.question_type = question_type
        self.required_operations = required_operations
        self.correct_answer = correct_answer
        self.model_answer = model_answer
        self.correct_steps = correct_steps or []
        self.wrong_steps = wrong_steps or []
        self.error_type = error_type
        self.error_reason = error_reason
        self.strengthen_distance = strengthen_distance
        self.update_neighbour_distance = update_neighbour_distance

    def __str__(self) -> str:
        lines = []
        lines.append("[QAMemoryNote]")
        lines.append(f"ID: {self.id}")
        lines.append(f"Question ID: {self.question_id}")
        lines.append(f"Question: {self.question_text}")
        lines.append(f"Question Type: {self.question_type}")
        lines.append(f"Required Operations: {', '.join(self.required_operations or [])}")
        lines.append(f"Correct Answer: {self.correct_answer}")
        lines.append(f"Model Answer: {self.model_answer or 'N/A'}")
        lines.append(f"Error Type: {self.error_type}")
        lines.append(f"Error Reason: {self.error_reason}")
        lines.append(f"Category: {self.category}")
        lines.append(f"Context: {self.context}")
        lines.append(f"Tags: {', '.join(self.tags or [])}")
        lines.append(f"Keywords: {', '.join(self.keywords or [])}")
        lines.append(f"Links: {', '.join(self.links or {})}")
        lines.append(f"Last Accessed: {self.last_accessed}")
        lines.append(f"Timestamp: {self.timestamp}")
        lines.append("Correct Steps:")
        for step in self.correct_steps or []:
            lines.append(f"  - {step}")
        lines.append("Wrong Steps:")
        for step in self.wrong_steps or []:
            lines.append(f"  - {step}")
        lines.append("Evolution History:")
        for h in self.evolution_history or []:
            lines.append(f"  - {h}")
        lines.append("Content Preview:")
        preview = self.content[:500] + ("..." if len(self.content) > 500 else "")
        lines.append(preview)
        return "\n".join(lines)
    
    def to_dict(self):
        return {
            "id": self.id,
            "question_id": getattr(self, "question_id", ""),
            "question_text": getattr(self, "question_text", ""),
            "question_type": getattr(self, "question_type", ""),
            "required_operations": getattr(self, "required_operations", []),
            "correct_answer": getattr(self, "correct_answer", ""),
            "model_answer": getattr(self, "model_answer", ""),
            "correct_steps": getattr(self, "correct_steps", []),
            "wrong_steps": getattr(self, "wrong_steps", []),
            "error_type": getattr(self, "error_type", ""),
            "error_reason": getattr(self, "error_reason", ""),
            "content": self.content,
            "keywords": self.keywords,
            "tags": self.tags,
            "context": self.context,
            "timestamp": self.timestamp,
            "last_accessed": self.last_accessed,
            "links": self.links,
            "category": self.category,
            "evolution_history": self.evolution_history,
            "strengthen_distance": getattr(self, "strengthen_distance", []),
            "update_neighbour_distance": getattr(self, "update_neighbour_distance", []),
            "tags_history": self.tags_history,
            "context_history": self.context_history
        }


class AgenticMemorySystem:
    """Core memory system that manages memory notes and their evolution.
    
    This system provides:
    - Memory creation, retrieval, update, and deletion
    - Content analysis and metadata extraction
    - Memory evolution and relationship management
    - Hybrid search capabilities
    """
    
    def __init__(self, 
                 args,
                 evo_threshold: int = 10,
                 ):  
        """Initialize the memory system.
        
        Args:
            model_name: Name of the sentence transformer model
            llm_backend: LLM backend to use (openai/ollama)
            llm_model: Name of the LLM model
            evo_threshold: Number of memories before triggering evolution
            api_key: API key for the LLM service
        """
        self.memories = {}
        self.evol_count = 0
        self.evol_mem_count = 0
        self.retrieval_count = {}
        
        # Initialize ChromaDB retriever with empty collection
        try:
            # First try to reset the collection if it exists
            temp_retriever = ChromaRetriever(collection_name="memories")
            temp_retriever.client.reset()
        except Exception as e:
            logger.warning(f"Could not reset ChromaDB collection: {e}")
            
        # Create a fresh retriever instance
        self.retriever = ChromaRetriever(collection_name="memories")
        
        # Initialize LLM controller
        self.llm = LLMWrapper(args)
        self.evo_threshold = evo_threshold

    def add_note(self,
                    question_id: str,
                    question_text: str,
                    question_type: str,
                    content: str,
                    retrive_result:list[Dict],
                    required_operations: List[str],
                    correct_steps: List[str],
                    wrong_steps: Optional[List[str]] = None,
                    correct_answer: Optional[str] = None,
                    model_answer: Optional[str] = None,
                    error_type: Optional[str] = None,
                    error_reason: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    category="Original note",
                    keywords: Optional[List[str]] = None,
                    context: Optional[str] = None,
                    args: Optional[Dict] = None) -> str:
        """
        Add a new QAMemoryNote to the memory system.
        Automatically builds content and adds metadata for retrieval.
        """
        
        # Step 1: Create the memory note
        note = QAMemoryNote(
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            required_operations=required_operations,
            correct_steps=correct_steps,
            wrong_steps=wrong_steps,
            correct_answer=correct_answer,
            model_answer=model_answer,
            error_type=error_type,
            error_reason=error_reason,
            content=content,
            tags=tags,
            category=category,
            context=context,
            keywords=keywords
        )
        
        # Step 2: Decide whether to evolve the memory
        evol_num = 0
        evo_label = False
        if len(retrive_result) != 0 and args.evolve_type == "LLM_based":
            evo_label, note, evol_num = self.optional_evolve(note, retrive_result)
        if len(retrive_result) != 0 and args.evolve_type == "always":
            evo_label, note, evol_num = self.always_evolve(note, retrive_result)
        if len(retrive_result) != 0 and args.evolve_type == "every_n_entries":
            if len(self.memories) % args.evolve_interval == 0:
                evo_label, note, evol_num = self.always_evolve(note, retrive_result)
        
        # step 3: add memory to the memory system
        self.memories[note.id] = note
        print(f"Add Memory {note.id} to the self memory dict")

        metadata = {
            "id": note.id,
            "content": note.content,
            "keywords": note.keywords,
            "links": note.links,
            "timestamp": note.timestamp,
            "last_accessed": note.last_accessed,
            "context": note.context,
            "evolution_history": note.evolution_history,
            "category": note.category,
            "tags": note.tags,
            "question_type": note.question_type,
            "question_text": note.question_text,
            "question_id": note.question_id,
            "required_operations": note.required_operations,
            "correct_steps": note.correct_steps,
            "wrong_steps": note.wrong_steps,
            "error_type": note.error_type,
            "error_reason": note.error_reason
        }

        self.retriever.add_document(note.content, metadata, note.id)
        print(f"Add Memory {note.id} to the retriever")

        self.evol_mem_count += evol_num
        if evo_label == True:
            self.evol_count += 1
            if self.evol_count % self.evo_threshold == 0:
                self.consolidate_memories()
                print("consolidate memories finished!")

        return note.id


    def consolidate_memories(self):
        """Consolidate memories: update retriever with new documents"""
        # Reset ChromaDB collection
        self.retriever = ChromaRetriever(collection_name="memories")
        
        # Re-add all memory documents with their complete metadata
        for memory in self.memories.values():
            metadata = {
                "id": memory.id,
                "content": memory.content,
                "keywords": memory.keywords,
                "links": memory.links,
                "timestamp": memory.timestamp,
                "last_accessed": memory.last_accessed,
                "context": memory.context,
                "evolution_history": memory.evolution_history,
                "category": memory.category,
                "tags": memory.tags,
                "question_type": memory.question_type,
                "question_text": memory.question_text,
                "question_id": memory.question_id,
                "required_operations": memory.required_operations,
                "correct_steps": memory.correct_steps,
                "wrong_steps": memory.wrong_steps,
                "error_type": memory.error_type,
                "error_reason": memory.error_reason
            }
            self.retriever.add_document(memory.content, metadata, memory.id)
    
    def find_related_memories(self, query: str, k: int = 5, threshold: float = 0.3) -> List[Dict]:
        results = self.retriever.search(query, k)
        structured_memories = []

        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            if dist <= threshold:
                structured_memories.append({
                    "id": meta.get("id", "000"),
                    "question_text": meta.get("question_text", ""),
                    "question_type": meta.get("question_type", ""),
                    "required_operations": meta.get("required_operations", []),
                    "correct_steps": meta.get("correct_steps", []),
                    "wrong_steps": meta.get("wrong_steps", []),
                    "error_type": meta.get("error_type", ""),
                    "error_reason": meta.get("error_reason", ""),
                    "distance": dist
                })
                mem_id = meta.get("id", "000")
                if mem_id in self.retrieval_count:
                    self.retrieval_count[mem_id] += 1
                else:
                    self.retrieval_count[mem_id] = 1

        return structured_memories

    def read(self, memory_id: str) -> Optional[MemoryNote]:
        """Retrieve a memory note by its ID.
        
        Args:
            memory_id (str): ID of the memory to retrieve
            
        Returns:
            MemoryNote if found, None otherwise
        """
        return self.memories.get(memory_id)
    
    def update(self, memory_id: str, **kwargs) -> bool:
        """Update a memory note.
        
        Args:
            memory_id: ID of memory to update
            **kwargs: Fields to update
            
        Returns:
            bool: True if update successful
        """
        if memory_id not in self.memories:
            return False
            
        note = self.memories[memory_id]
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(note, key):
                setattr(note, key, value)
                
        # Update in ChromaDB
        metadata = {
            "id": note.id,
            "content": note.content,
            "keywords": note.keywords,
            "links": note.links,
            "timestamp": note.timestamp,
            "last_accessed": note.last_accessed,
            "context": note.context,
            "evolution_history": note.evolution_history,
            "category": note.category,
            "tags": note.tags,
            "question_type": note.question_type,
            "question_text": note.question_text,
            "question_id": note.question_id,
            "required_operations": note.required_operations,
            "correct_steps": note.correct_steps,
            "wrong_steps": note.wrong_steps,
            "error_type": note.error_type,
            "error_reason": note.error_reason
        }
        
        # Delete and re-add to update
        self.retriever.delete_document(memory_id)
        self.retriever.add_document(document=note.content, metadata=metadata, doc_id=memory_id)
        
        return True
    
    def delete(self, memory_id: str) -> bool:
        """Delete a memory note by its ID.
        
        Args:
            memory_id (str): ID of the memory to delete
            
        Returns:
            bool: True if memory was deleted, False if not found
        """
        if memory_id in self.memories:
            # Delete from ChromaDB
            self.retriever.delete_document(memory_id)
            # Delete from local storage
            del self.memories[memory_id]
            return True
        return False
    
    def _search_raw(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Internal search method that returns raw results from ChromaDB.
        
        This is used internally by the memory evolution system to find
        related memories for potential evolution.
        
        Args:
            query (str): The search query text
            k (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: Raw search results from ChromaDB
        """
        results = self.retriever.search(query, k)
        return [{'id': doc_id, 'score': score} 
                for doc_id, score in zip(results['ids'][0], results['distances'][0])]
                
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for memories using a hybrid retrieval approach.
        
        This method combines results from both:
        1. ChromaDB vector store (semantic similarity)
        2. Embedding-based retrieval (dense vectors)
        
        The results are deduplicated and ranked by relevance.
        
        Args:
            query (str): The search query text
            k (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results, each containing:
                - id: Memory ID
                - content: Memory content
                - score: Similarity score
                - metadata: Additional memory metadata
        """
        # Get results from ChromaDB
        chroma_results = self.retriever.search(query, k)
        memories = []
        
        # Process ChromaDB results
        for i, doc_id in enumerate(chroma_results['ids'][0]):
            memory = self.memories.get(doc_id)
            if memory:
                memories.append({
                    'id': doc_id,
                    'content': memory.content,
                    'context': memory.context,
                    'keywords': memory.keywords,
                    'score': chroma_results['distances'][0][i]
                })
                
        # Get results from embedding retriever
        indices = self.retriever.search(query, k)
        
        # Combine results with deduplication
        seen_ids = set(m['id'] for m in memories)
        for idx in indices:
            document = self.retriever.documents[idx]
            memory_id = self.retriever.documents.index(document)
            if document and document not in seen_ids:
                memory = self.memories.get(memory_id)
                if memory:
                    memories.append({
                        'id': idx,
                        'content': document,
                        'context': memory.context,
                        'keywords': memory.keywords,
                        'score': chroma_results.get('score', 0.0)
                    })
                    seen_ids.add(memory_id)
                    
        return memories[:k]
    
    def _search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for memories using a hybrid retrieval approach.
        
        This method combines results from both:
        1. ChromaDB vector store (semantic similarity)
        2. Embedding-based retrieval (dense vectors)
        
        The results are deduplicated and ranked by relevance.
        
        Args:
            query (str): The search query text
            k (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results, each containing:
                - id: Memory ID
                - content: Memory content
                - score: Similarity score
                - metadata: Additional memory metadata
        """
        # Get results from ChromaDB
        chroma_results = self.retriever.search(query, k)
        memories = []
        
        # Process ChromaDB results
        for i, doc_id in enumerate(chroma_results['ids'][0]):
            memory = self.memories.get(doc_id)
            if memory:
                memories.append({
                    'id': doc_id,
                    'content': memory.content,
                    'context': memory.context,
                    'keywords': memory.keywords,
                    'score': chroma_results['distances'][0][i]
                })
                
        # Get results from embedding retriever
        embedding_results = self.retriever.search(query, k)
        
        # Combine results with deduplication
        seen_ids = set(m['id'] for m in memories)
        for result in embedding_results:
            memory_id = result.get('id')
            if memory_id and memory_id not in seen_ids:
                memory = self.memories.get(memory_id)
                if memory:
                    memories.append({
                        'id': memory_id,
                        'content': memory.content,
                        'context': memory.context,
                        'keywords': memory.keywords,
                        'score': result.get('score', 0.0)
                    })
                    seen_ids.add(memory_id)
                    
        return memories[:k]

    def search_agentic(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for memories using ChromaDB retrieval."""
        if not self.memories:
            return []
            
        try:
            # Get results from ChromaDB
            results = self.retriever.search(query, k)
            
            # Process results
            memories = []
            seen_ids = set()
            
            # Check if we have valid results
            if ('ids' not in results or not results['ids'] or 
                len(results['ids']) == 0 or len(results['ids'][0]) == 0):
                return []
                
            # Process ChromaDB results
            for i, doc_id in enumerate(results['ids'][0][:k]):
                if doc_id in seen_ids:
                    continue
                    
                if i < len(results['metadatas'][0]):
                    metadata = results['metadatas'][0][i]
                    
                    # Create result dictionary with all metadata fields
                    memory_dict = {
                        'id': doc_id,
                        'content': metadata.get('content', ''),
                        'context': metadata.get('context', ''),
                        'keywords': metadata.get('keywords', []),
                        'tags': metadata.get('tags', []),
                        'timestamp': metadata.get('timestamp', ''),
                        'category': metadata.get('category', 'Uncategorized'),
                        'is_neighbor': False
                    }
                    
                    # Add score if available
                    if 'distances' in results and len(results['distances']) > 0 and i < len(results['distances'][0]):
                        memory_dict['score'] = results['distances'][0][i]
                        
                    memories.append(memory_dict)
                    seen_ids.add(doc_id)
            
            # Add linked memories (neighbors)
            neighbor_count = 0
            for memory in list(memories):  # Use a copy to avoid modification during iteration
                if neighbor_count >= k:
                    break
                    
                # Get links from metadata
                links = memory.get('links', {})
                if not links and 'id' in memory:
                    # Try to get links from memory object
                    mem_obj = self.memories.get(memory['id'])
                    if mem_obj:
                        links = mem_obj.links
                        
                for link_id in links.keys():
                    if link_id not in seen_ids and neighbor_count < k:
                        neighbor = self.memories.get(link_id)
                        if neighbor:
                            memories.append({
                                'id': link_id,
                                'content': neighbor.content,
                                'context': neighbor.context,
                                'keywords': neighbor.keywords,
                                'tags': neighbor.tags,
                                'timestamp': neighbor.timestamp,
                                'category': neighbor.category,
                                'is_neighbor': True
                            })
                            seen_ids.add(link_id)
                            neighbor_count += 1
            
            return memories[:k]
        except Exception as e:
            logger.error(f"Error in search_agentic: {str(e)}")
            return []

    def build_content_from_fields(
        self,
        question_id: str,
        question_text: str,
        question_type: str,
        required_operations: List[str],
        correct_steps: List[str],
        wrong_steps: Optional[List[str]] = None,
        correct_answer: Optional[str] = None,
        model_answer: Optional[str] = None,
        error_type: Optional[str] = None,
        error_reason: Optional[str] = None,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ) -> str:
        """Builds a structured content string from fields in a QAMemoryNote."""
        lines = []
        
        lines.append(f"Question ID: {question_id}")
        lines.append(f"Question: {question_text}")
        lines.append(f"Question Type: {question_type}")
        lines.append(f"Required operations: {', '.join(required_operations)}")

        if context:
            lines.append(f"Context: {context}")
        if tags:
            lines.append(f"Tags: {', '.join(tags)}")
        if keywords:
            lines.append(f"Keywords: {', '.join(keywords)}")

        if correct_answer:
            lines.append(f"Correct Answer: {correct_answer}")
        if model_answer:
            lines.append(f"Model Answer: {model_answer}")

        if correct_steps:
            lines.append("Correct Steps:")
            for step in correct_steps:
                lines.append(f"- {step}")

        if wrong_steps:
            lines.append("Wrong Steps:")
            for step in wrong_steps:
                lines.append(f"- {step}")
        
        if error_type:
            lines.append(f"Error Type: {error_type}")
        if error_reason:
            lines.append(f"Error Reason: {error_reason}")

        return "\n".join(lines)

    def optional_evolve(self, note: MemoryNote, retrive_result: list[Dict]) -> Tuple[bool, MemoryNote]:
        """Process a memory note and determine if it should evolve.
        
        Args:
            note: The memory note to process
            
        Returns:
            Tuple[bool, MemoryNote]: (should_evolve, processed_note)
        """
        print("Entering LLM based evolve function")
        # For first memory or testing, just return the note without evolution
        if not self.memories:
            return False, note
        evolved_memories_number = 0
        
        distance_list = []
        distance_list = [retrive_result[i]['distance'] for i in range(len(retrive_result))]
        # Query LLM for evolution decision
        user_prompt = optional_evolution_user.format(
            content=note.content,
            nearest_neighbors_memories=retrive_result,
            neighbor_number=len(retrive_result)
        )
        prompts = self.llm.format_prompt(optional_evolution_system, user_prompt)
        print(f"finish prepareing prompts: {prompts}")
        response = self.llm.generate_responses(prompts)
        print(f"get response form llm: {response}")
        
        if response and isinstance(response, list):
            result, is_format_correct = parse_json(response[0])
        else:
            result, is_format_correct = {}, False
        if not is_format_correct:
            should_evolve = False
            note.evolution_history.append(response)
            print("Format is incorrect, not evolve this time.")
        else: # format is correct
            should_evolve = result.get("should_evolve", "false")
            clean_answer = clean_bool(should_evolve)
            if clean_answer == "true":
                should_evolve = True
                note.evolution_history.append(result)
                actions = result.get("actions", [])
                for action in actions:
                    if action == "strengthen":
                        evolved_memories_number = 1
                        suggest_connections = result.get("suggested_connections", [])
                        new_tags = result.get("tags_to_update", [])
                        for connection in suggest_connections:
                            if connection not in note.links:
                                note.links[connection] = 1
                            else:
                                note.links[connection] += 1
                        note.tags = new_tags
                        note.strengthen_distance.append(distance_list)
                        print("Format is correct, choose strengthen.")
                    elif action == "update_neighbor":
                        new_context_neighborhood = result.get("new_context_neighborhood", [])
                        new_tags_neighborhood = result.get("new_tags_neighborhood", [])
                        neighbor_ids = result.get("suggested_connections", [])
                        evolved_memories_number = len(neighbor_ids)
                        note.category = "Evolve note"
                        note.update_neighbour_distance.append(distance_list)
                        for i in range(len(neighbor_ids)):
                            note_id = neighbor_ids[i]
                            if note_id in self.memories:
                                notetmp = self.memories[note_id]
                                notetmp.category = "Evolve note"
                                if i < len(new_tags_neighborhood):
                                    notetmp.tags = new_tags_neighborhood[i]
                                if i < len(new_context_neighborhood):
                                    notetmp.context = new_context_neighborhood[i]
                                self.memories[note_id] = notetmp
                        print("Format is correct, choose update_neighbor.")
            else:
                should_evolve = False
                note.evolution_history.append(result)
                print("Format is correct, choose not to evolve this time.")
        return should_evolve, note, evolved_memories_number
    
    def always_evolve(self, note: MemoryNote, retrive_result: list[Dict]) -> Tuple[bool, MemoryNote]:

        print("Entering always evolve function")
        # For first memory or testing, just return the note without evolution
        if not self.memories:
            return False, note
        evolved_memories_number = 0
        
        distance_list = [retrive_result[i]['distance'] for i in range(len(retrive_result))]
        # Query LLM for evolution decision
        user_prompt = always_evolve_user.format(
            content=note.content,
            nearest_neighbors_memories=retrive_result,
            neighbor_number=len(retrive_result)
        )
        prompts = self.llm.format_prompt(always_evolve_system, user_prompt)
        print(f"finish prepareing prompts: {prompts}")
        response = self.llm.generate_responses(prompts)
        print(f"get response form llm: {response}")
        
        if response and isinstance(response, list):
            result, is_format_correct = parse_json(response[0])
        else:
            result, is_format_correct = {}, False
        if not is_format_correct:
            should_evolve = False
            note.evolution_history.append(response)
            print("Format is incorrect, not evolve this time.")
        else: # format is correct
            should_evolve = result.get("should_evolve", "false")
            clean_answer = clean_bool(should_evolve)
            if clean_answer == "true":
                should_evolve = True
                note.evolution_history.append(result)
                actions = result.get("actions", [])
                for action in actions:
                    if action == "strengthen":
                        evolved_memories_number = 1
                        suggest_connections = result.get("suggested_connections", [])
                        new_tags = result.get("tags_to_update", [])
                        for connection in suggest_connections:
                            if connection not in note.links:
                                note.links[connection] = 1
                            else:
                                note.links[connection] += 1
                        note.tags_history.append(note.tags)
                        note.tags = new_tags
                        note.strengthen_distance.append(distance_list)
                        print("Format is correct, choose strengthen.")
                    elif action == "update_neighbor":
                        new_context_neighborhood = result.get("new_context_neighborhood", [])
                        new_tags_neighborhood = result.get("new_tags_neighborhood", [])
                        neighbor_ids = result.get("suggested_connections", [])
                        evolved_memories_number = len(neighbor_ids)
                        note.category = "Evolve note"
                        note.update_neighbour_distance.append(distance_list)
                        for i in range(len(neighbor_ids)):
                            note_id = neighbor_ids[i]
                            if note_id in self.memories:
                                notetmp = self.memories[note_id]
                                notetmp.category = "Evolve note"
                                if i < len(new_tags_neighborhood):
                                    notetmp.tags_history.append(notetmp.tags)
                                    notetmp.tags = new_tags_neighborhood[i]
                                if i < len(new_context_neighborhood):
                                    notetmp.context_history.append(notetmp.context)
                                    notetmp.context = new_context_neighborhood[i]
                                self.memories[note_id] = notetmp
                        print("Format is correct, choose update_neighbor.")
            else:
                should_evolve = False
                note.evolution_history.append(result)
                print("Format is correct, choose not to evolve this time.")
        return should_evolve, note, evolved_memories_number
                
