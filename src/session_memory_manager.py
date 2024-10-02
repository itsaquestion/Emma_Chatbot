"""
SessionMemoryManager

This class manages chat session memories, including storage, retrieval, and vector-based search 
of chat history. It uses Sentence Transformers for text embedding and FAISS for efficient 
similarity search.

The class maintains a separate storage for each chat session, organizing chat history and 
vector data in a structured directory format.

Attributes:
    BASE_DIR (str): Base directory for storing all session data.

Args:
    session_id (str): Unique identifier for the chat session.
    model_name (str, optional): Name of the Sentence Transformer model to use for text embedding. Defaults to 'TencentBAC/Conan-embedding-v1'.

Methods:
    add_message(role, content): 
        Adds a new message to the chat history and updates the vector database.
    
    save_to_file(): 
        Saves the current chat history and vector data to files.
    
    retrieve_relevant_memory(query, k=2): 
        Retrieves k most relevant memories based on the given query.
    
    get_chat_history(): 
        Returns the entire chat history for the session.

Usage:
    # Initialize a new session
    memory_manager = SessionMemoryManager("user_123")

    # Add a new message
    memory_manager.add_message("user", "Hello, how are you?")

    # Retrieve relevant memories
    relevant_memories = memory_manager.retrieve_relevant_memory("How are you?")

    # Get entire chat history
    chat_history = memory_manager.get_chat_history()

Note:
    This class automatically handles the creation and management of necessary directory 
    structures and files. It ensures type compatibility with FAISS by consistently using 
    np.float32 for vector data.
"""
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

class SessionMemoryManager:
    BASE_DIR = "memory_storage"

    def __init__(self, session_id, model_name='TencentBAC/Conan-embedding-v1'):
        
        self.session_id = session_id
        self.session_dir = os.path.join(self.BASE_DIR, session_id)
        self.chat_filename = os.path.join(self.session_dir, "chat_history.json")
        self.vector_filename = os.path.join(self.session_dir, "vector_data.npy")
        
        
        print(f"Load model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # 确保目录结构存在
        self._ensure_directory_structure()
        
        # 加载或创建聊天历史
        if os.path.exists(self.chat_filename):
            with open(self.chat_filename, 'r') as f:
                self.chat_history = json.load(f)
        else:
            self.chat_history = []
        
        print(f"Load memory: {session_id}")
        # 加载或创建向量数据库
        if os.path.exists(self.vector_filename):
            self.vectors = np.load(self.vector_filename).astype(np.float32)
            self.index = faiss.IndexFlatL2(self.vectors.shape[1])
            if self.vectors.shape[0] > 0:
                self.index.add(self.vectors)
        else:
            self.vectors = np.empty((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
            self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())

    def _ensure_directory_structure(self):
        """确保必要的目录结构存在"""
        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)

    def add_message(self, role, content):
        # 添加新消息到聊天历史
        self.chat_history.append({"role": role, "content": content})
        
        # 向量化新消息并添加到向量数据库
        new_vector = self.model.encode([f"{role}: {content}"]).astype(np.float32)
        self.vectors = np.vstack([self.vectors, new_vector])
        self.index.add(new_vector)
        
        # 保存更新后的数据
        self.save_to_file()

    def save_to_file(self):
        # 保存聊天历史
        with open(self.chat_filename, 'w') as f:
            json.dump(self.chat_history, f)
        
        with open('.'.join(self.chat_filename.split('.')[:-1])+'.txt','w') as f:
            f.write(self.get_formated_chat_history())
        
        # 保存向量数据库
        np.save(self.vector_filename, self.vectors)

    def retrieve_relevant_memory(self, query, k=2):
        if self.vectors.shape[0] == 0:
            return []
        
        query_vector = self.model.encode([query]).astype(np.float32)
        distances, indices = self.index.search(query_vector, k)
        return [self.chat_history[i] for i in indices[0]]

    def get_chat_history(self):
        return self.chat_history
    
    def get_formated_chat_history(self) -> str:
        formatted_text = ""
        for entry in self.chat_history:
            role = entry.get("role", "Unknown")
            content = entry.get("content", "")
            formatted_text += f"{role.capitalize()}:\n{content}\n\n"
        return formatted_text.strip()
