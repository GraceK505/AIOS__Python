# core/ollama_client.py
import os
import sys
import json
import queue
import threading
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable, Any
import config

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    pass  # Ollama not available

class OllamaClient:
    """Simple Ollama client for AI commands with auto-model download"""
    
    def __init__(self, model: str = "llama3.2"):
        self.model = model
        self.conversation = []
        self.max_history = 5
        self.client = None
        self.is_available = False
        
        if OLLAMA_AVAILABLE:
            try:
                import subprocess
                import json
                import requests

                # First, test if Ollama service is running
                print(f"🔍 Checking Ollama connection for model: {model}...")
                test_url = "http://localhost:11434/api/tags"
                try:
                    response = requests.get(test_url, timeout=3)
                    
                    if response.status_code == 200:
                        # Server is running, check if our model is available
                        available_models = [m['name'] for m in response.json().get('models', [])]
                        
                        if self.model not in available_models:
                            print(f"⚠️  Model '{self.model}' not found locally.")
                            print(f"   Available models: {', '.join(available_models) if available_models else 'None'}")
                            print(f"   Attempting to pull '{self.model}'. This may take a few minutes...")
                            
                            # Try to pull the model
                            try:
                                # Show download progress
                                print("   Downloading model... (this can take 1-5 minutes)")
                                result = subprocess.run(
                                    ['ollama', 'pull', self.model], 
                                    capture_output=True, 
                                    text=True,
                                    timeout=100  # 5 minute timeout for download
                                )
                                
                                if result.returncode == 0:
                                    print(f"✅ Successfully pulled model: {self.model}")
                                    # Re-check available models after pull
                                    response = requests.get(test_url, timeout=3)
                                    available_models = [m['name'] for m in response.json().get('models', [])]
                                else:
                                    print(f"❌ Failed to pull model. Error: {result.stderr[:200]}")
                                    print(f"   Please run manually: ollama pull {self.model}")
                                    self._suggest_alternative_models(available_models)
                                    return
                            except subprocess.TimeoutExpired:
                                print("❌ Model download timed out. The model might be too large.")
                                print("   Try a smaller model: ollama pull llama3.2:3b")
                                return
                        
                        # Now connect with the model
                        self.client = ollama.Client()
                        self.is_available = True
                        print(f"✅ Ollama connected successfully with model: {model}")
                        
                    else:
                        print(f"❌ Ollama API error (status {response.status_code})")
                        
                except requests.exceptions.ConnectionError:
                    print("❌ Cannot connect to Ollama service.")
                    print("   Please ensure Ollama is running: ollama serve")
                    print("   If Ollama is running, check: curl http://localhost:11434")
                except Exception as e:
                    print(f"⚠️  Ollama connection issue: {e}")
                    self._suggest_alternative_models([])

            except Exception as e:
                print(f"❌ Error initializing Ollama client: {e}")
        else:
            print("❌ Ollama Python package not installed.")
            print("   Install with: pip install ollama")
    
    def _suggest_alternative_models(self, available_models):
        """Suggest alternative models if llama3.2 fails"""
        print("\n💡 Alternative solutions:")
        print("1. Try a smaller model:")
        print("   - llama3.2:3b (3 billion parameters, faster)")
        print("   - mistral (7 billion parameters, good balance)")
        print("   - phi (small, fast)")
        print("")
        print("2. Check if Ollama is installed correctly:")
        print("   - Run: ollama --version")
        print("   - Start Ollama: ollama serve")
        print("")
        print("3. Download a model manually:")
        print("   - ollama pull llama3.2:3b")
        print("   - ollama pull mistral")
        print("   - Then restart AIOS")
    
    def chat(self, message: str) -> str:
        """Send message to Ollama with better error handling"""
        if not self.client or not self.is_available:
            return """Ollama is not available.

Possible solutions:
1. Ensure Ollama is running: open terminal and run 'ollama serve'
2. Download a model: 'ollama pull llama3.2' (or 'ollama pull mistral')
3. Install Ollama: https://ollama.com/download

Check AIOS startup messages for more details."""
        
        try:
            # Add user message to conversation
            self.conversation.append({"role": "user", "content": message})
            
            # Keep only recent messages
            if len(self.conversation) > self.max_history * 2:
                self.conversation = self.conversation[-self.max_history * 2:]
            
            # Get response
            print(f"🤖 Sending to Ollama (model: {self.model})...")
            response = self.client.chat(
                model=self.model,
                messages=self.conversation
            )
            
            # Add assistant response
            ai_response = response['message']['content']
            self.conversation.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific error cases
            if "model" in error_msg.lower() and "not found" in error_msg.lower():
                return f"""Model '{self.model}' not found.

Quick fix: Download the model:
1. Open a terminal
2. Run: ollama pull {self.model}
3. Restart AIOS

Or use a different model:
- Change model in code to 'mistral' or 'llama3.2:3b'
- Then run: ollama pull mistral"""
            
            elif "Failed to connect" in error_msg or "connection" in error_msg.lower():
                return f"""Cannot connect to Ollama service.

Please ensure:
1. Ollama is running: open terminal and type 'ollama serve'
2. Wait for it to start (should see 'Ollama is running')
3. Then try AI command again

Error details: {error_msg}"""
            
            return f"AI Error: {error_msg}"
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation = []
        return "Conversation cleared"
    
    def list_models(self) -> str:
        """List available models - improved version"""
        if not self.is_available:
            return "Ollama not available. Please check connection."
        
        try:
            models = self.client.list()
            model_list = [m['name'] for m in models.get('models', [])]
            
            if model_list:
                # Show models with their size if available
                model_info = []
                for m in models.get('models', [])[:10]:  # Show first 10
                    size_gb = m.get('size', 0) / (1024**3)  # Convert bytes to GB
                    model_info.append(f"{m['name']} ({size_gb:.1f}GB)")
                
                return f"Available models:\n" + "\n".join(model_info)
            else:
                return "No models found. Download one with: ollama pull llama3.2"
                
        except Exception as e:
            return f"Error listing models: {e}"
    
    def change_model(self, new_model: str) -> str:
        """Change to a different model"""
        self.model = new_model
        self.conversation = []  # Clear conversation when changing models
        self.is_available = False
        
        # Re-initialize with new model
        print(f"🔄 Switching to model: {new_model}")
        self.client = None
        
        # Create a new instance-like initialization for the new model
        if OLLAMA_AVAILABLE:
            try:
                self.client = ollama.Client()
                # Test if model exists
                try:
                    # Quick test to see if model is available
                    test_response = self.client.chat(
                        model=new_model,
                        messages=[{"role": "user", "content": "hello"}]
                    )
                    self.is_available = True
                    return f"✅ Switched to model: {new_model}"
                except:
                    return f"❌ Model '{new_model}' not available. Download with: ollama pull {new_model}"
            except:
                return "Failed to connect to Ollama"
        
        return "Ollama not available"