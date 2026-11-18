#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI command processing for AIOS with Voice Control & Ollama AI
Enhanced with Speech-to-Command Matrix Generator
"""

import os
import sys
import json
import queue
import threading
import time
import re
import subprocess
import shlex
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable, Any, Set, Union
import config
from core.ollama_client import OllamaClient

# Initialize voice availability at module level
VOICE_AVAILABLE = False
OLLAMA_AVAILABLE = False

# Try to import voice modules
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    pass  # Voice modules not available


# ==================== COMMAND MATRIX GENERATOR ====================
class CommandMatrixGenerator:
    """
    Generates structured command matrices from natural language speech
    Converts spoken words to executable system commands with parameters
    """
    
    def __init__(self):
        # Command action mappings
        self.action_keywords = {
            'file_operations': {
                'create': ['create', 'make', 'new', 'add', 'generate'],
                'delete': ['delete', 'remove', 'erase', 'trash', 'destroy'],
                'read': ['read', 'open', 'view', 'show', 'display', 'cat'],
                'write': ['write', 'edit', 'modify', 'update', 'append'],
                'copy': ['copy', 'duplicate', 'clone', 'replicate'],
                'move': ['move', 'relocate', 'transfer', 'shift'],
                'rename': ['rename', 'rechristen', 'relabel']
            },
            'system_operations': {
                'navigate': ['go to', 'change to', 'enter', 'cd', 'navigate'],
                'monitor': ['status', 'health', 'usage', 'performance', 'stats'],
                'control': ['start', 'stop', 'restart', 'kill', 'launch', 'run'],
                'config': ['configure', 'setup', 'settings', 'preferences']
            },
            'peripheral_operations': {
                'detect': ['detect', 'scan', 'find', 'list', 'show'],
                'read': ['read from', 'get from', 'listen to', 'monitor'],
                'write': ['write to', 'send to', 'output to'],
                'control': ['control', 'command', 'operate', 'drive']
            }
        }
        
        # Object types and their synonyms
        self.object_types = {
            'file': ['file', 'document', 'text', 'data', 'record', 'log'],
            'folder': ['folder', 'directory', 'path', 'location', 'place'],
            'process': ['process', 'program', 'app', 'application', 'service'],
            'device': ['device', 'peripheral', 'hardware', 'component', 'usb'],
            'network': ['network', 'connection', 'wifi', 'ethernet', 'internet'],
            'system': ['system', 'computer', 'machine', 'device', 'hardware']
        }
        
        # Parameter extraction patterns
        self.param_patterns = {
            'name': r'(?:named|called|titled|labeled|with name)\s+(["\']?)([^"\'\s]+(?:\s+[^"\'\s]+)*)\1',
            'path': r'(?:at|in|from|to)\s+(?:the\s+)?(?:path\s+)?(["\']?)((?:/\w+)+(?:/\w*)?|\.\.?/?|~/?)\1',
            'size': r'(?:size|length)\s+(?:of\s+)?(\d+)\s*(bytes?|KB|MB|GB|TB)',
            'type': r'(?:type|format)\s+(?:of\s+)?(\w+)',
            'content': r'(?:containing|with|having)\s+(?:the\s+)?(?:content\s+)?(["\'])(.*?)\1',
            'time': r'(?:for|in)\s+(\d+)\s*(seconds?|minutes?|hours?)'
        }
        
        # Command templates
        self.command_templates = {
            # File operations
            'create_file': {
                'pattern': r'(?:create|make|new)\s+(?:a\s+)?(?:new\s+)?file',
                'template': 'touch {name}',
                'params': ['name']
            },
            'create_folder': {
                'pattern': r'(?:create|make|new)\s+(?:a\s+)?(?:new\s+)?(?:folder|directory)',
                'template': 'mkdir -p {name}',
                'params': ['name']
            },
            'delete_file': {
                'pattern': r'(?:delete|remove|erase)\s+(?:the\s+)?file',
                'template': 'rm {name}',
                'params': ['name']
            },
            'delete_folder': {
                'pattern': r'(?:delete|remove|erase)\s+(?:the\s+)?(?:folder|directory)',
                'template': 'rm -rf {name}',
                'params': ['name']
            },
            'read_file': {
                'pattern': r'(?:read|show|display|view|cat)\s+(?:the\s+)?file',
                'template': 'cat {name}',
                'params': ['name']
            },
            'navigate': {
                'pattern': r'(?:go\s+to|change\s+to|enter|cd)\s+(?:the\s+)?(?:folder|directory)',
                'template': 'cd {path}',
                'params': ['path']
            },
            'list_files': {
                'pattern': r'(?:list|show|display)\s+(?:files|contents|ls)',
                'template': 'ls {options} {path}',
                'params': ['options', 'path'],
                'defaults': {'options': '-la'}
            },
            
            # System operations
            'system_info': {
                'pattern': r'(?:system|computer)\s+(?:info|status|health)',
                'template': 'system_profiler SPHardwareDataType',
                'params': []
            },
            'process_list': {
                'pattern': r'(?:show|list)\s+(?:running\s+)?(?:processes|apps|programs)',
                'template': 'ps aux',
                'params': []
            },
            'cpu_usage': {
                'pattern': r'(?:cpu|processor)\s+(?:usage|load|status)',
                'template': 'top -l 1 | grep "CPU usage"',
                'params': []
            },
            'memory_usage': {
                'pattern': r'(?:memory|ram)\s+(?:usage|status|available)',
                'template': 'vm_stat | grep "Pages free"',
                'params': []
            },
            
            # Peripheral operations
            'list_usb': {
                'pattern': r'(?:list|show)\s+(?:usb|peripheral|device)s?',
                'template': 'system_profiler SPUSBDataType',
                'params': []
            },
            'detect_devices': {
                'pattern': r'(?:detect|find|scan)\s+(?:devices|peripherals|hardware)',
                'template': 'ioreg -p IOUSB',
                'params': []
            },
            
            # AIOS Widget commands
            'open_terminal': {
                'pattern': r'(?:open|start|launch)\s+(?:the\s+)?terminal',
                'template': 'widget:terminal',
                'params': []
            },
            'open_calculator': {
                'pattern': r'(?:open|start|launch|calculate)\s+(?:the\s+)?calculator',
                'template': 'widget:calculator',
                'params': []
            },
            'open_notes': {
                'pattern': r'(?:open|start|launch|show)\s+(?:the\s+)?notes',
                'template': 'widget:notes',
                'params': []
            },
            'open_info': {
                'pattern': r'(?:open|start|launch|show)\s+(?:system\s+)?info',
                'template': 'widget:info',
                'params': []
            },
            'open_monitor': {
                'pattern': r'(?:open|start|launch|show)\s+(?:system\s+)?monitor',
                'template': 'widget:monitor',
                'params': []
            },
            'open_explorer': {
                'pattern': r'(?:open|start|launch|show)\s+(?:file\s+)?explorer',
                'template': 'widget:explorer',
                'params': []
            }
        }
        
        # Precompile regex patterns for performance
        self.compiled_patterns = {}
        for key, patterns in self.param_patterns.items():
            self.compiled_patterns[key] = re.compile(patterns, re.IGNORECASE)
        
        # Context memory for follow-up commands
        self.context = {
            'last_object': None,
            'last_action': None,
            'last_location': os.getcwd(),
            'recent_files': []
        }
    
    def generate_matrix(self, speech_text: str) -> Dict[str, Any]:
        """
        Generate command matrix from speech text
        Returns structured data for command execution
        """
        speech_text = speech_text.lower().strip()
        
        matrix = {
            'original_text': speech_text,
            'detected_action': None,
            'detected_object': None,
            'detected_object_type': None,
            'parameters': {},
            'command_template': None,
            'executable_command': None,
            'confidence_score': 0.0,
            'requires_confirmation': False,
            'context_aware': False,
            'error': None
        }
        
        try:
            # Step 1: Extract action and object
            action_info = self._extract_action(speech_text)
            object_info = self._extract_object(speech_text)
            
            matrix['detected_action'] = action_info.get('action')
            matrix['detected_object'] = object_info.get('object')
            matrix['detected_object_type'] = object_info.get('type')
            
            # Step 2: Extract parameters
            params = self._extract_parameters(speech_text)
            matrix['parameters'] = params
            
            # Step 3: Apply context awareness
            self._apply_context(matrix, speech_text)
            
            # Step 4: Match to command template
            template_match = self._match_to_template(speech_text, matrix)
            
            if template_match:
                matrix['command_template'] = template_match['template']
                matrix['executable_command'] = self._generate_command(
                    template_match['template'],
                    matrix['parameters']
                )
                matrix['confidence_score'] = template_match['confidence']
                
                # Set confirmation requirement for destructive actions
                destructive_actions = ['delete', 'remove', 'erase', 'kill', 'stop']
                if any(action in speech_text for action in destructive_actions):
                    matrix['requires_confirmation'] = True
            
            # Step 5: Calculate confidence score
            matrix['confidence_score'] = self._calculate_confidence(
                matrix['detected_action'],
                matrix['detected_object'],
                matrix['parameters']
            )
            
            # Step 6: Update context
            self._update_context(matrix)
            
        except Exception as e:
            matrix['error'] = str(e)
            matrix['confidence_score'] = 0.0
        
        return matrix
    
    def _extract_action(self, text: str) -> Dict[str, str]:
        """Extract the action from speech text"""
        result = {'action': None, 'category': None}
        
        for category, actions in self.action_keywords.items():
            for action, keywords in actions.items():
                for keyword in keywords:
                    if keyword in text:
                        result['action'] = action
                        result['category'] = category
                        return result
        
        # Try pattern matching for complex actions
        patterns = [
            (r'create.*file', 'create', 'file_operations'),
            (r'make.*folder', 'create', 'file_operations'),
            (r'go.*to', 'navigate', 'system_operations'),
            (r'list.*usb', 'detect', 'peripheral_operations'),
            (r'open.*terminal', 'open', 'system_operations'),
            (r'open.*calculator', 'open', 'system_operations'),
            (r'open.*notes', 'open', 'system_operations'),
        ]
        
        for pattern, action, category in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                result['action'] = action
                result['category'] = category
                break
        
        return result
    
    def _extract_object(self, text: str) -> Dict[str, str]:
        """Extract the object from speech text"""
        result = {'object': None, 'type': None}
        
        # Look for specific object mentions
        for obj_type, synonyms in self.object_types.items():
            for synonym in synonyms:
                pattern = r'\b' + re.escape(synonym) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    result['type'] = obj_type
                    
                    # Try to extract the object name
                    name_pattern = r'(?:file|folder|directory|device)\s+(?:named|called)?\s*["\']?([^"\'\s]+(?:\s+[^"\'\s]+)*)["\']?'
                    match = re.search(name_pattern, text, re.IGNORECASE)
                    if match:
                        result['object'] = match.group(1)
                    break
        
        return result
    
    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """Extract parameters from speech text"""
        params = {}
        
        for param_name, pattern in self.compiled_patterns.items():
            match = pattern.search(text)
            if match:
                if param_name == 'name':
                    params['name'] = match.group(2)
                elif param_name == 'path':
                    params['path'] = match.group(2)
                elif param_name == 'content':
                    params['content'] = match.group(2)
                else:
                    params[param_name] = match.group(1)
        
        # Extract numeric parameters
        numeric_patterns = [
            (r'(\d+)\s*(?:times|repeats?)', 'repeat_count'),
            (r'size\s+(\d+)', 'size'),
            (r'(\d+)\s*MB', 'size_mb'),
            (r'(\d+)\s*GB', 'size_gb'),
        ]
        
        for pattern, param_name in numeric_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                params[param_name] = int(match.group(1))
        
        return params
    
    def _apply_context(self, matrix: Dict, text: str):
        """Apply context awareness to the matrix"""
        # Use last mentioned object if current object is ambiguous
        if not matrix['detected_object'] and self.context['last_object']:
            if 'it' in text or 'that' in text:
                matrix['detected_object'] = self.context['last_object']
                matrix['detected_object_type'] = self.context.get('last_object_type')
                matrix['context_aware'] = True
        
        # Use last location if no path specified
        if 'path' not in matrix['parameters']:
            matrix['parameters']['path'] = self.context['last_location']
            matrix['context_aware'] = True
    
    def _match_to_template(self, text: str, matrix: Dict) -> Optional[Dict]:
        """Match speech to a command template"""
        best_match = None
        highest_confidence = 0
        
        for template_name, template_info in self.command_templates.items():
            pattern = template_info['pattern']
            if re.search(pattern, text, re.IGNORECASE):
                # Calculate match confidence
                confidence = self._calculate_template_confidence(text, template_info)
                
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = {
                        'name': template_name,
                        'template': template_info['template'],
                        'params': template_info.get('params', []),
                        'defaults': template_info.get('defaults', {}),
                        'confidence': confidence
                    }
        
        return best_match
    
    def _generate_command(self, template: str, params: Dict) -> str:
        """Generate executable command from template and parameters"""
        command = template
        
        # Apply defaults
        defaults = self._get_template_defaults(template)
        for key, value in defaults.items():
            if key not in params:
                params[key] = value
        
        # Replace parameters in template
        for key, value in params.items():
            placeholder = '{' + key + '}'
            if placeholder in command:
                if value is not None:
                    command = command.replace(placeholder, str(value))
                else:
                    command = command.replace(placeholder, '')
        
        # Clean up any remaining placeholders
        command = re.sub(r'\{\w+\}', '', command).strip()
        
        return command
    
    def _get_template_defaults(self, template: str) -> Dict:
        """Get default values for a template"""
        for template_info in self.command_templates.values():
            if template_info['template'] == template:
                return template_info.get('defaults', {})
        return {}
    
    def _calculate_confidence(self, action: str, obj: str, params: Dict) -> float:
        """Calculate confidence score for the matrix"""
        confidence = 0.0
        
        if action:
            confidence += 0.3
        
        if obj:
            confidence += 0.3
        
        if params:
            confidence += min(0.4, len(params) * 0.1)
        
        return min(confidence, 1.0)
    
    def _calculate_template_confidence(self, text: str, template_info: Dict) -> float:
        """Calculate confidence for template matching"""
        base_confidence = 0.5
        
        # Check if all required parameters are mentioned
        required_params = template_info.get('params', [])
        if required_params:  
            param_coverage = 0
            for param in required_params:
                if param in text:
                    param_coverage += 1
            base_confidence += (param_coverage / len(required_params)) * 0.5
        
        return min(base_confidence, 1.0)
    
    def _update_context(self, matrix: Dict):
        """Update context memory"""
        if matrix['detected_object']:
            self.context['last_object'] = matrix['detected_object']
            self.context['last_object_type'] = matrix['detected_object_type']
        
        if 'path' in matrix['parameters']:
            self.context['last_location'] = matrix['parameters']['path']
        
        if matrix['detected_action']:
            self.context['last_action'] = matrix['detected_action']
        
        # Keep track of recent files
        if matrix['detected_object_type'] == 'file' and matrix['detected_object']:
            if matrix['detected_object'] not in self.context['recent_files']:
                self.context['recent_files'].append(matrix['detected_object'])
                if len(self.context['recent_files']) > 10:
                    self.context['recent_files'].pop(0)
    
    def explain_matrix(self, matrix: Dict) -> str:
        """Generate human-readable explanation of the command matrix"""
        lines = []
        lines.append("🔍 Command Analysis Report:")
        lines.append("-" * 40)
        
        if matrix['error']:
            lines.append(f"❌ Error: {matrix['error']}")
            return "\n".join(lines)
        
        lines.append(f"📝 Original: \"{matrix['original_text']}\"")
        lines.append(f"🎯 Action: {matrix['detected_action'] or 'Not detected'}")
        lines.append(f"📦 Object: {matrix['detected_object'] or 'Not specified'}")
        lines.append(f"📁 Type: {matrix['detected_object_type'] or 'Unknown'}")
        
        if matrix['parameters']:
            lines.append("⚙️ Parameters:")
            for key, value in matrix['parameters'].items():
                lines.append(f"  • {key}: {value}")
        
        if matrix['command_template']:
            lines.append(f"📋 Template: {matrix['command_template']}")
        
        if matrix['executable_command']:
            lines.append(f"⚡ Command: {matrix['executable_command']}")
        
        lines.append(f"📊 Confidence: {matrix['confidence_score']:.1%}")
        
        if matrix['requires_confirmation']:
            lines.append("⚠️  Requires confirmation (destructive action)")
        
        if matrix['context_aware']:
            lines.append("🔄 Context-aware adjustment applied")
        
        return "\n".join(lines)
    
    def get_suggestions(self, partial_text: str) -> List[str]:
        """Get command suggestions based on partial input"""
        suggestions = []
        
        for template_name, template_info in self.command_templates.items():
            pattern = template_info['pattern']
            if re.search(pattern, partial_text, re.IGNORECASE):
                # Extract example from pattern
                example = pattern.replace(r'(?:', '').replace(r')', '').replace(r'\s+', ' ')
                example = re.sub(r'\\b', '', example)
                example = re.sub(r'\[.*?\]', '', example)
                
                # Generate example command
                example_params = {param: f'<{param}>' for param in template_info.get('params', [])}
                example_cmd = self._generate_command(template_info['template'], example_params)
                
                suggestions.append(f"{example_cmd} - {template_name.replace('_', ' ')}")
        
        return suggestions[:5]  # Return top 5 suggestions


# ==================== VOICE ASSISTANT ====================
class VoiceAssistant:
    """Simple voice assistant integrated with Ollama - RELIABLE VERSION"""
    
    def __init__(self, ollama_client: OllamaClient = None, app_callback=None):
        self.ollama = ollama_client or OllamaClient()
        self.voice_active = False
        self.voice_thread = None
        self.audio_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # Store callback to AIOSApp
        self.app_callback = app_callback
        
        # Matrix command generator
        self.matrix_generator = CommandMatrixGenerator()
        self.last_matrix = None
        
        # Use the module-level VOICE_AVAILABLE variable
        self.voice_enabled = VOICE_AVAILABLE
        
        # Print status
        if self.voice_enabled:
            self._debug_audio_devices()
        else:
            print("🎤 Voice assistant not available - install speechrecognition and pyttsx3")
    
    def _safe_tts_speak(self, text: str):
        """Safely speak text using TTS with fresh engine each time"""
        if not self.voice_enabled:
            print(f"[TTS] {text[:100]}..." if len(text) > 100 else f"[TTS] {text}")
            return
        
        def tts_task():
            try:
                # Create fresh TTS engine each time
                engine = pyttsx3.init()
                
                # Get available voices and pick the best one
                voices = engine.getProperty('voices')
                if voices:
                    # Try to find a natural-sounding voice
                    preferred_voices = ['Microsoft David', 'Microsoft Zira', 'English']
                    for voice in voices:
                        if any(pref in voice.name for pref in preferred_voices):
                            engine.setProperty('voice', voice.id)
                            break
                
                # Adjust settings for better AI response clarity
                engine.setProperty('rate', 170)  # Slightly slower for comprehension
                engine.setProperty('volume', 1.0)  # Maximum volume
                
                # If text is very long, split into manageable chunks
                if len(text) > 500:
                    # Split by sentences if possible
                    import re
                    sentences = re.split(r'(?<=[.!?]) +', text)
                    
                    # Speak in chunks of 3 sentences at a time
                    chunk_size = 3
                    for i in range(0, len(sentences), chunk_size):
                        chunk = ' '.join(sentences[i:i+chunk_size])
                        if chunk.strip():
                            engine.say(chunk)
                    
                else:
                    # Normal length text
                    engine.say(text)
                
                engine.runAndWait()
                
            except Exception as e:
                print(f"❌ TTS Error: {e}")
                # Fallback: print to console
                print(f"[TTS Failed] {text[:150]}..." if len(text) > 150 else f"[TTS Failed] {text}")
        
        # Run TTS in thread to avoid blocking
        tts_thread = threading.Thread(target=tts_task, daemon=True)
        tts_thread.start()
    
    def speak(self, text: str):
        """Speak text aloud - uses safe TTS method"""
        self._safe_tts_speak(text)
    
    def _safe_listen(self, timeout: int = 5) -> Optional[str]:
        """Safely listen for voice command with fresh instances"""
        if not self.voice_enabled:
            return "Voice not available. Install required packages."
        
        try:
            # Create fresh recognizer and microphone each time
            recognizer = sr.Recognizer()
            
            # Use context manager for microphone to ensure proper cleanup
            with sr.Microphone() as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                try:
                    # Listen with timeout
                    audio = recognizer.listen(
                        source, 
                        timeout=timeout, 
                        phrase_time_limit=8
                    )
                    
                    # Recognize using Google Web Speech API
                    text = recognizer.recognize_google(audio)
                    return text
                    
                except sr.WaitTimeoutError:
                    return "Listening timeout"
                except sr.UnknownValueError:
                    return "Could not understand audio"
                except sr.RequestError as e:
                    return f"Speech recognition error: {e}"
                except Exception as e:
                    return f"Error during recognition: {str(e)}"
                    
        except Exception as e:
            return f"Microphone/recognition error: {str(e)}"
    
    def listen(self, timeout: int = 3) -> Optional[str]:
        """Listen for voice command - uses safe listening method"""
        return self._safe_listen(timeout)
    
    def voice_ai_chat(self, prompt: str) -> str:
        """Process voice command with AI"""
        # Remove common voice prefixes
        prefixes = ["hey aios", "okay aios", "computer", "assistant", "aios"]
        for prefix in prefixes:
            if prompt.lower().startswith(prefix):
                prompt = prompt[len(prefix):].strip()
        
        print(f"🤖 Processing voice command: {prompt[:50]}...")
        
        # Check if this is a widget command
        matrix = self.matrix_generator.generate_matrix(prompt)
        
        if self._is_aios_widget_command(matrix):
            widget_name = self._extract_widget_name(matrix)
            if widget_name and self.app_callback:
                print(f"🔄 Detected widget command: {widget_name}")
                # Call the app_callback with the widget name
                response = self.app_callback(widget_name)
                return response
        
        # If not a widget command, use app_callback for general command processing
        if self.app_callback:
            print(f"🔄 Routing to AIOS command system: {prompt}")
            response = self.app_callback(prompt)
            return response
        else:
            # Fallback: Get AI response from Ollama
            response = self.ollama.chat(prompt)
            return response
    
    def start_voice_mode(self):
        """Start voice listening in a background thread"""
        if not self.voice_enabled:
            return "Voice assistant not available. Install: pip install speechrecognition pyttsx3"
        
        if self.voice_active:
            return "Voice assistant is already active"
        
        self.voice_active = True
        self.speak("Voice assistant activated. Say 'Hey AIOS' followed by your command.")
        
        # Start the voice loop thread
        if not self.voice_thread or not self.voice_thread.is_alive():
            self.voice_thread = threading.Thread(target=self._voice_loop, daemon=True)
            self.voice_thread.start()
        
        return "Voice assistant started"
    
    def stop_voice_mode(self):
        """Stop voice listening"""
        if not self.voice_enabled or not self.voice_active:
            return
        
        self.voice_active = False
        self.speak("Voice assistant deactivated")
        
        # Wait for thread to finish gracefully
        if self.voice_thread and self.voice_thread.is_alive():
            self.voice_thread.join(timeout=2.0)
    
    def _voice_loop(self):
        """Continuous voice listening loop for wake words - WORKING VERSION"""
        if not self.voice_enabled:
            return
        
        wake_words = ["hey aios", "okay aios", "computer", "assistant", "aios"]
        print("🔊 Voice loop started, waiting for wake words...")
        
        while self.voice_active:
            try:
                # Listen briefly for wake words
                command = self._safe_listen(timeout=2)
                
                if isinstance(command, str) and command not in ["Listening timeout", "Could not understand audio", "Microphone/recognition error"]:
                    # Check for wake words
                    cmd_lower = command.lower()
                    wake_word_detected = False
                    
                    for wake_word in wake_words:
                        if wake_word in cmd_lower:
                            wake_word_detected = True
                            print(f"🎯 Wake word detected: {wake_word}")
                            
                            # Remove wake word from command
                            clean_command = cmd_lower.replace(wake_word, "").strip()
                            
                            if clean_command:
                                # Process the command immediately
                                print(f"📝 Processing command: {clean_command}")
                                self.speak("Yes")
                                
                                # Process the command
                                matrix, response = self.process_voice_command(clean_command)
                                
                                # Put in command queue for app to handle
                                self.command_queue.put(("voice", clean_command, response))
                                
                                # Speak brief confirmation
                                if response and len(response) < 100:
                                    self.speak(response[:100])
                            else:
                                # No command after wake word, listen again
                                self.speak("I'm listening")
                                time.sleep(0.5)
                                
                                # Listen for command
                                real_command = self._safe_listen(timeout=5)
                                if isinstance(real_command, str) and real_command not in ["Listening timeout", "Could not understand audio"]:
                                    print(f"📝 Processing follow-up command: {real_command}")
                                    matrix, response = self.process_voice_command(real_command)
                                    self.command_queue.put(("voice", real_command, response))
                                    if response and len(response) < 100:
                                        self.speak(response[:100])
                            
                            break
                    
                    # If no wake word but command was heard, process it anyway (for quick commands)
                    if not wake_word_detected and len(command.split()) >= 2:
                        print(f"⚠️ No wake word, but processing anyway: {command}")
                        matrix, response = self.process_voice_command(command)
                        self.command_queue.put(("voice", command, response))
                        if response and len(response) < 100:
                            self.speak(response[:100])
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Voice loop error: {e}")
                time.sleep(1)
    
    def test_voice(self) -> str:
        """Test voice functionality"""
        if not self.voice_enabled:
            return "Voice not available. Install: pip install speechrecognition pyttsx3"
        
        try:
            # Test TTS
            test_text = "Testing one two three"
            self.speak(test_text)
            
            # Give TTS time to start
            time.sleep(0.5)
            
            # Test microphone
            result = self._safe_listen(timeout=3)
            
            if isinstance(result, str) and result not in ["Listening timeout", "Could not understand audio"]:
                return f"✅ Voice test passed!\nHeard: {result}"
            else:
                return f"⚠️ Voice test partial: {result}\n(TTS worked, microphone had issues)"
                
        except Exception as e:
            return f"❌ Voice test failed: {str(e)}"
    
    def _debug_audio_devices(self):
        """Debug audio devices and settings"""
        if not self.voice_enabled:
            print("🎤 Voice not enabled - skipping audio debug")
            return
        
        try:
            import pyttsx3
            
            print("\n" + "="*50)
            print("🔊 AUDIO SYSTEM DIAGNOSTICS")
            print("="*50)
            
            # Check TTS engine
            try:
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                print(f"✅ TTS Engine: {len(voices)} voice(s) available")
                engine.stop()
                
            except Exception as e:
                print(f"❌ TTS Engine Error: {e}")
            
            # Check microphone availability
            try:
                import speech_recognition as sr
                mics = sr.Microphone.list_microphone_names()
                print(f"\n🎤 Microphones: {len(mics)} device(s) available")
                    
            except Exception as e:
                print(f"❌ Microphone check error: {e}")
            
            print("="*50 + "\n")
            
        except ImportError:
            print("❌ Cannot debug audio - pyttsx3 not installed")
    
    def process_voice_command(self, speech_text: str) -> Tuple[Dict, str]:
        """
        Process voice command with matrix generation
        Returns (matrix, response)
        """
        if not speech_text or len(speech_text.strip()) < 2:
            return {}, "I didn't hear a command"
        
        print(f"\n🎯 Processing voice command: '{speech_text}'")
        
        # Generate command matrix
        matrix = self.matrix_generator.generate_matrix(speech_text)
        self.last_matrix = matrix
        
        response = ""
        
        # Check if this is an AIOS widget command
        if self._is_aios_widget_command(matrix):
            widget_name = self._extract_widget_name(matrix)
            if widget_name and self.app_callback:
                print(f"🎯 Detected widget command: {widget_name}")
                response = self.app_callback(widget_name)
                return matrix, response
        
        # Check for system commands with high confidence
        elif matrix['confidence_score'] >= 0.6 and matrix['executable_command']:
            if matrix['requires_confirmation']:
                response = f"This is a destructive action: {matrix['executable_command']}. Please confirm."
            else:
                # Execute system command
                result = self._execute_system_command(matrix['executable_command'])
                response = f"Executed: {matrix['executable_command']}. Result: {result[:100]}..."
        
        # Use AI for everything else
        else:
            response = self.voice_ai_chat(speech_text)
        
        return matrix, response
    
    def _execute_system_command(self, command: str) -> str:
        """Execute a system command safely"""
        try:
            # Security check - prevent dangerous commands
            dangerous = ['rm -rf /', 'format', 'dd', 'mkfs', ':(){:|:&};:']
            if any(danger in command.lower() for danger in dangerous):
                return "❌ Command blocked for security reasons"
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout[:500]  # Limit output length
            else:
                return f"❌ Error: {result.stderr[:200]}"
                
        except subprocess.TimeoutExpired:
            return "❌ Command timed out"
        except Exception as e:
            return f"❌ Execution error: {str(e)}"
    
    def get_command_suggestions(self, partial_text: str) -> List[str]:
        """Get command suggestions based on partial speech"""
        return self.matrix_generator.get_suggestions(partial_text)
    
    def _is_aios_widget_command(self, matrix: Dict) -> bool:
        """Check if the command is for an AIOS widget"""
        widget_keywords = ['terminal', 'calculator', 'notes', 'info', 'screensaver', 
                          'network', 'process', 'explorer', 'monitor', 'console']
        
        command_text = matrix.get('original_text', '').lower()
        executable_cmd = matrix.get('executable_command', '').lower()
        
        # Check for widget keywords in command
        for widget in widget_keywords:
            if widget in command_text or widget in executable_cmd:
                return True
        
        # Check action types
        if matrix.get('detected_action') in ['open', 'start', 'launch']:
            return True
            
        return False
    
    def _extract_widget_name(self, matrix: Dict) -> Optional[str]:
        """Extract widget name from command matrix"""
        command_text = matrix.get('original_text', '').lower()
        
        widget_mapping = {
            'terminal': ['terminal', 'console', 'command line', 'shell'],
            'calculator': ['calculator', 'calc', 'calculate'],
            'notes': ['notes', 'notepad', 'text editor'],
            'info': ['info', 'information', 'system info', 'about'],
            'screensaver': ['screensaver', 'screen saver'],
            'network': ['network', 'net', 'connection'],
            'process': ['process', 'processes', 'task manager'],
            'explorer': ['explorer', 'file explorer', 'files'],
            'monitor': ['monitor', 'system monitor', 'performance'],
            'console': ['console', 'ai console', 'chat']
        }
        
        for widget_name, keywords in widget_mapping.items():
            for keyword in keywords:
                if keyword in command_text:
                    return widget_name
        
        return None
    
    def cleanup(self):
        """Clean up voice resources"""
        self.voice_active = False


# ==================== ENHANCED VOICE ASSISTANT ====================

class EnhancedVoiceAssistant(VoiceAssistant):
    """Enhanced voice assistant with advanced matrix command processing"""
    
    def __init__(self, ollama_client: OllamaClient = None, app_callback=None):
        super().__init__(ollama_client, app_callback)
        self.matrix_available = True
    
    def generate_matrix(self, text: str) -> Dict:
        """Generate command matrix from text"""
        return self.matrix_generator.generate_matrix(text)
    
    def explain_matrix(self, matrix: Dict) -> str:
        """Explain a command matrix"""
        return self.matrix_generator.explain_matrix(matrix)


# ==================== COMMAND REGISTRY ====================
class CommandRegistry:
    """Registry for managing commands with AI and voice support"""
    
    def __init__(self):
        self.commands = {}
        self._register_default_commands()
    
    def _register_default_commands(self):
        """Register default commands"""
        commands = [
            # Core commands
            ("help", self._cmd_help, "Show help"),
            ("?", self._cmd_help, "Show help (alias)"),
            ("clear", self._cmd_clear, "Clear console"),
            ("exit", self._cmd_exit, "Exit AIOS"),
            ("quit", self._cmd_exit, "Exit AIOS (alias)"),
            ("cpu", self._cmd_cpu, "Show CPU usage"),
            ("mem", self._cmd_memory, "Show memory usage"),
            
            # File commands
            ("ls", self._cmd_ls, "List files"),
            ("pwd", self._cmd_pwd, "Current directory"),
            ("cd", self._cmd_cd, "Change directory"),
            ("mkdir", self._cmd_mkdir, "Create folder"),
            ("touch", self._cmd_touch, "Create file"),
            ("rm", self._cmd_rm, "Delete file/folder"),
            ("fileinfo", self._cmd_info, "File information"),
            
            # AI Commands
            ("ai", self._cmd_ai, "Chat with AI"),
            ("ask", self._cmd_ai, "Chat with AI (alias)"),
            ("chat", self._cmd_ai, "Chat with AI (alias)"),
            ("models", self._cmd_models, "List AI models"),
            ("clearai", self._cmd_clear_ai, "Clear AI conversation"),
            
            # Voice Commands
            ("voice", self._cmd_voice, "Voice assistant control"),
            ("speak", self._cmd_speak, "Speak text"),
            ("listen", self._cmd_listen, "Listen for voice command"),
            ("voicetest", self._cmd_voice_test, "Test voice system"),
        ]
        
        for name, handler, desc in commands:
            self.register_command(name, handler, desc)
    
    def register_command(self, name: str, handler: Callable, description: str = ""):
        """Register a command"""
        self.commands[name] = {"handler": handler, "description": description}
    
    def get_command(self, name: str) -> Optional[Dict]:
        """Get command by name"""
        return self.commands.get(name)
    
    def get_suggestions(self, prefix: str) -> List[str]:
        """Get command suggestions"""
        return [cmd for cmd in self.commands if cmd.startswith(prefix)][:5]
    
    def get_all_commands(self) -> Dict[str, Dict]:
        """Get all registered commands"""
        return self.commands.copy()

    
    # ========== CORE COMMAND HANDLERS ==========
    
    def _cmd_help(self, args: List[str], context: Dict) -> str:
        return """Available commands:

Core Commands:
* help, ?    - Show this help
* clear      - Clear console
* exit, quit - Exit AIOS
* cpu        - Show CPU usage
* mem        - Show memory usage

File Commands:
* ls         - List files
* pwd        - Current directory
* cd <dir>   - Change directory
* mkdir <name> - Create folder
* touch <name> - Create file
* rm <name>  - Delete file/folder
* fileinfo <name> - File information

AI Commands:
* ai <question> - Chat with AI
* models        - List available AI models
* clearai       - Clear AI conversation

Voice Commands:
* voice <start/stop/status> - Control voice assistant
* speak <text>  - Speak text aloud
* listen        - Listen for voice command
* voicetest     - Test voice system

Type any command name followed by ? for more info."""
    
    def _cmd_clear(self, args: List[str], context: Dict) -> str:
        return "[CLEAR]"
    
    def _cmd_exit(self, args: List[str], context: Dict) -> str:
        return "[SHUTDOWN]"
    
    def _cmd_cpu(self, args: List[str], context: Dict) -> str:
        import psutil
        return f"CPU: {psutil.cpu_percent()}%"
    
    def _cmd_memory(self, args: List[str], context: Dict) -> str:
        import psutil
        mem = psutil.virtual_memory()
        return f"Memory: {mem.percent}% ({mem.used//(1024**2)}MB used)"
    
    def _cmd_back(self, args: List[str], context: Dict) -> str:
        """Go back - navigation placeholder"""
        return "Back navigation not yet implemented"
    
    def _cmd_forward(self, args: List[str], context: Dict) -> str:
        """Go forward - navigation placeholder"""
        return "Forward navigation not yet implemented"
    
    def _cmd_info(self, args: List[str], context: Dict) -> str:
        """File information"""
        if not args:
            return "Usage: fileinfo <file_or_folder>"
        import os
        import stat
        import time
        
        target = args[0]
        if not os.path.exists(target):
            return f"Error: '{target}' not found"
        
        try:
            stat_info = os.stat(target)
            is_dir = os.path.isdir(target)
            size = stat_info.st_size
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat_info.st_mtime))
            mode = stat.filemode(stat_info.st_mode)
            
            info = []
            info.append(f"Name: {target}")
            info.append(f"Type: {'Directory' if is_dir else 'File'}")
            info.append(f"Size: {size} bytes")
            info.append(f"Modified: {mtime}")
            info.append(f"Permissions: {mode}")
            
            return "\n".join(info)
        except Exception as e:
            return f"Error getting info: {e}"
    
    # ========== BASIC SYSTEM COMMAND HANDLERS ==========
    
    def _cmd_sysinfo(self, args: List[str], context: Dict) -> str:
        """System information"""
        import platform
        import psutil
        return f"OS: {platform.system()} {platform.release()}\n" \
               f"CPU: {psutil.cpu_percent()}%\n" \
               f"Memory: {psutil.virtual_memory().percent}% used"
    
    def _cmd_time(self, args: List[str], context: Dict) -> str:
        """Current time"""
        from datetime import datetime
        return f"Current time: {datetime.now().strftime('%H:%M:%S')}"
    
    def _cmd_date(self, args: List[str], context: Dict) -> str:
        """Current date"""
        from datetime import datetime
        return f"Current date: {datetime.now().strftime('%Y-%m-%d')}"
    
    def _cmd_monitor(self, args: List[str], context: Dict) -> str:
        """System monitor - simplified version"""
        import psutil
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        return f"CPU: {cpu}%\nMemory: {mem.percent}%"
    
    def _cmd_ls(self, args: List[str], context: Dict) -> str:
        """List files"""
        import os
        return "\n".join(os.listdir('.'))
    
    def _cmd_pwd(self, args: List[str], context: Dict) -> str:
        """Current directory"""
        import os
        return os.getcwd()
    
    def _cmd_cd(self, args: List[str], context: Dict) -> str:
        """Change directory"""
        import os
        if not args:
            return "Usage: cd <directory>"
        try:
            os.chdir(args[0])
            return f"Changed to: {os.getcwd()}"
        except Exception as e:
            return f"Error: {e}"
    
    def _cmd_mkdir(self, args: List[str], context: Dict) -> str:
        """Create folder"""
        import os
        if not args:
            return "Usage: mkdir <folder_name>"
        try:
            os.makedirs(args[0], exist_ok=True)
            return f"Created folder: {args[0]}"
        except Exception as e:
            return f"Error: {e}"
    
    def _cmd_touch(self, args: List[str], context: Dict) -> str:
        """Create file"""
        if not args:
            return "Usage: touch <filename>"
        try:
            with open(args[0], 'a'):
                os.utime(args[0], None)
            return f"Created file: {args[0]}"
        except Exception as e:
            return f"Error: {e}"
    
    def _cmd_rm(self, args: List[str], context: Dict) -> str:
        """Delete file/folder"""
        import shutil
        if not args:
            return "Usage: rm <file_or_folder>"
        try:
            if os.path.isdir(args[0]):
                shutil.rmtree(args[0])
                return f"Removed folder: {args[0]}"
            else:
                os.remove(args[0])
                return f"Removed file: {args[0]}"
        except Exception as e:
            return f"Error: {e}"
    
    # ========== AI COMMAND HANDLERS ==========
    
    def _cmd_ai(self, args: List[str], context: Dict) -> str:
        """Chat with AI"""
        if not args:
            return "Usage: ai <your question>"
        
        ai_core = context.get("ai_core")
        if not ai_core or not hasattr(ai_core, 'ollama'):
            return "AI system not available"
        
        question = " ".join(args)
        return ai_core.ollama.chat(question)
    
    def _cmd_models(self, args: List[str], context: Dict) -> str:
        """List AI models"""
        ai_core = context.get("ai_core")
        if not ai_core or not hasattr(ai_core, 'ollama'):
            return "AI system not available"
        
        if hasattr(ai_core.ollama, 'list_models'):
            return ai_core.ollama.list_models()
        return "llama3.2, mistral, gemma2, qwen:7b"
    
    def _cmd_clear_ai(self, args: List[str], context: Dict) -> str:
        """Clear AI conversation"""
        ai_core = context.get("ai_core")
        if not ai_core or not hasattr(ai_core, 'ollama'):
            return "AI system not available"
        
        return ai_core.ollama.clear_conversation()
    
    
    # ========== VOICE COMMAND HANDLERS ==========
    
    def _cmd_voice(self, args: List[str], context: Dict) -> str:
        """Control voice assistant"""
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Voice assistant not available."
        
        if not args:
            status = "active" if ai.voice.voice_active else "inactive"
            return f"Voice assistant is {status}. Use: voice start/stop/status"
        
        action = args[0].lower()
        
        if action == "start":
            return ai.voice.start_voice_mode()
        elif action == "stop":
            ai.voice.stop_voice_mode()
            return "Voice assistant stopped."
        elif action == "status":
            status = "ACTIVE" if ai.voice.voice_active else "INACTIVE"
            available = "Available" if ai.voice.voice_enabled else "Not available"
            return f"Voice assistant status: {status}\nVoice system: {available}"
        else:
            return "Unknown action. Use: voice start/stop/status"
    
    def _cmd_speak(self, args: List[str], context: Dict) -> str:
        """Speak text aloud"""
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Voice assistant not available."
        
        if not args:
            return "Please provide text to speak. Example: speak Hello world"
        
        text = " ".join(args)
        ai.voice.speak(text)
        return f"Speaking: {text}"
    
    def _cmd_listen(self, args: List[str], context: Dict) -> str:
        """Listen for voice command"""
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Voice assistant not available."
        
        timeout = int(args[0]) if args and args[0].isdigit() else 3
        result = ai.voice.listen(timeout)
        
        if isinstance(result, str) and result not in ["Listening timeout", "Could not understand audio"]:
            # Process as AI command
            response = ai.ollama.chat(result)
            ai.voice.speak(response[:200])  # Speak response
            return f"Command: {result}\nResponse: {response}"
        else:
            return f"Listening result: {result}"
    
    def _cmd_voice_test(self, args: List[str], context: Dict) -> str:
        """Test voice system"""
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Voice assistant not available."
        
        return ai.voice.test_voice()


# ==================== ENHANCED COMMAND REGISTRY ====================
class EnhancedCommandRegistry(CommandRegistry):
    """Enhanced registry with matrix command support"""
    
    def __init__(self):
        super().__init__()
        self._register_matrix_commands()
    
    def _register_matrix_commands(self):
        """Register matrix-related commands"""
        matrix_commands = [
            ("matrix", self._cmd_matrix, "Analyze text as command matrix"),
            ("suggest", self._cmd_suggest, "Get command suggestions"),
            ("lastcmd", self._cmd_last_command, "Show last command matrix"),
            ("execute", self._cmd_execute, "Execute system command"),
            ("cmdmatrix", self._cmd_cmd_matrix, "Generate matrix from command"),
            ("analyze", self._cmd_analyze, "Analyze text for command intent"),
        ]
        
        for name, handler, desc in matrix_commands:
            self.register_command(name, handler, desc)
    
    # ========== MATRIX COMMAND HANDLERS ==========
    
    def _cmd_matrix(self, args: List[str], context: Dict) -> str:
        """Analyze text as command matrix"""
        if not args:
            return "Usage: matrix <text_to_analyze>"
        
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Matrix analyzer not available."
        
        text = " ".join(args)
        matrix = ai.voice.generate_matrix(text)
        
        if "error" in matrix:
            return f"Matrix generation error: {matrix['error']}"
        
        return ai.voice.explain_matrix(matrix)
    
    def _cmd_suggest(self, args: List[str], context: Dict) -> str:
        """Get command suggestions"""
        if not args:
            return "Usage: suggest <partial_command>"
        
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Suggestion system not available."
        
        text = " ".join(args)
        suggestions = ai.voice.get_command_suggestions(text)
        
        if suggestions:
            return "💡 Suggestions:\n" + "\n".join(f"• {s}" for s in suggestions)
        else:
            return "No suggestions found. Try being more specific."
    
    def _cmd_last_command(self, args: List[str], context: Dict) -> str:
        """Show last command matrix"""
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Matrix analyzer not available."
        
        if not hasattr(ai.voice, 'last_matrix') or not ai.voice.last_matrix:
            return "No command matrix generated yet."
        
        return ai.voice.explain_matrix(ai.voice.last_matrix)
    
    def _cmd_execute(self, args: List[str], context: Dict) -> str:
        """Execute system command"""
        if not args:
            return "Usage: execute <system_command>"
        
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Command executor not available."
        
        command = " ".join(args)
        result = ai.voice._execute_system_command(command)
        return f"Command: {command}\nResult:\n{result}"
    
    def _cmd_cmd_matrix(self, args: List[str], context: Dict) -> str:
        """Generate matrix from command"""
        if not args:
            return "Usage: cmdmatrix <command_text>"
        
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Matrix generator not available."
        
        text = " ".join(args)
        matrix = ai.voice.generate_matrix(text)
        
        if "error" in matrix:
            return f"Matrix generation error: {matrix['error']}"
        
        result = []
        result.append("🔍 Command Matrix Analysis:")
        result.append("-" * 40)
        result.append(f"Original: {matrix['original_text']}")
        result.append(f"Action: {matrix['detected_action']}")
        result.append(f"Object: {matrix['detected_object']}")
        result.append(f"Type: {matrix['detected_object_type']}")
        result.append(f"Confidence: {matrix['confidence_score']:.1%}")
        
        if matrix['executable_command']:
            result.append(f"Command: {matrix['executable_command']}")
        
        if matrix['parameters']:
            result.append("Parameters:")
            for key, value in matrix['parameters'].items():
                result.append(f"  {key}: {value}")
        
        return "\n".join(result)
    
    def _cmd_analyze(self, args: List[str], context: Dict) -> str:
        """Analyze text for command intent"""
        if not args:
            return "Usage: analyze <text>"
        
        ai = context.get("ai_core")
        if not ai or not hasattr(ai, 'voice'):
            return "Analyzer not available."
        
        text = " ".join(args)
        matrix = ai.voice.generate_matrix(text)
        
        if "error" in matrix:
            return f"Matrix generation error: {matrix['error']}"
        
        # Detailed analysis
        analysis = []
        analysis.append("🔍 Detailed Command Analysis")
        analysis.append("="*50)
        analysis.append(f"Input: {text}")
        analysis.append(f"Detected Intent: {matrix.get('detected_action', 'Unknown')}")
        analysis.append(f"Confidence Level: {matrix['confidence_score']:.1%}")
        
        if matrix['confidence_score'] >= 0.7:
            analysis.append("✅ High confidence - can be executed directly")
        elif matrix['confidence_score'] >= 0.4:
            analysis.append("⚠️ Medium confidence - may need clarification")
        else:
            analysis.append("❌ Low confidence - use AI for interpretation")
        
        if matrix['executable_command']:
            analysis.append(f"Generated Command: {matrix['executable_command']}")
        
        return "\n".join(analysis)


# ==================== AI CORE ====================
class AICore:
    """Main AI command processor with Voice and Ollama support"""
    
    def __init__(self, filesystem, app_callback=None):
        self.filesystem = filesystem
        self.registry = CommandRegistry()
        
        # Initialize AI components
        self.ollama = OllamaClient() if OLLAMA_AVAILABLE else None
        
        # Pass app_callback to VoiceAssistant
        self.voice = VoiceAssistant(self.ollama, app_callback)
        
        self.command_history = []
        self.context = {
            "filesystem": filesystem,
            "ai_core": self
        }
        
        # Store app_callback for use in command processing
        self.app_callback = app_callback
        
        # Start voice command processing thread if voice is available
        if hasattr(self.voice, 'voice_enabled') and self.voice.voice_enabled:
            self._start_voice_processor()
            print("✅ Voice processor thread started")
        else:
            print("⚠️  Voice processor not started - voice not available")
    
    def _start_voice_processor(self):
        """Start background thread to process voice commands"""
        def process_voice_commands():
            while True:
                try:
                    # Check for voice commands
                    if self.voice and not self.voice.command_queue.empty():
                        source, command, response = self.voice.command_queue.get()
                        print(f"\n[Voice] Command: {command}")
                        print(f"[Voice] Response: {response[:100]}...")
                
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Voice processor error: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=process_voice_commands, daemon=True)
        thread.start()
    
    def process_command(self, cmd: str) -> Tuple[str, bool, bool]:
        """Process a command"""
        cmd = cmd.strip()
        if not cmd:
            return "Please enter a command.", False, False
        
        # Special case for empty command or single ?
        if cmd == "?":
            cmd = "help"
        
        self.command_history.append(cmd)
        
        parts = cmd.split()
        command_name = parts[0].lower()
        args = parts[1:]
        
        # Check for command help (command + ?)
        if command_name.endswith('?'):
            command_name = command_name[:-1]
            return self._get_command_help(command_name), False, False
        
        command = self.registry.get_command(command_name)
        if not command:
            # Try AI chat for unknown commands
            if self.ollama:
                response = self.ollama.chat(cmd)
                return response, False, False
            else:
                # Try to find similar commands
                suggestions = self.registry.get_suggestions(command_name)
                if suggestions:
                    return f"Command not found: {command_name}. Did you mean: {', '.join(suggestions)}?", False, False
                return f"Command not found: {command_name}. Type 'help' for commands.", False, False
        
        try:
            result = command["handler"](args, self.context)
            
            if isinstance(result, tuple):
                if len(result) == 2:
                    response, refresh = result
                    return response, refresh, False
                elif len(result) == 3:
                    response, refresh, special = result
                    return response, refresh, special
            else:
                return result, False, False
        except Exception as e:
            return f"Error: {str(e)}", False, False
        
    def _get_command_help(self, command_name: str) -> str:
        """Get help for a specific command"""
        command = self.registry.get_command(command_name)
        if not command:
            return f"No help available for command: {command_name}"
        
        description = command.get("description", "No description available")
        
        # Add usage examples for specific commands
        usage_examples = {
            "cd": "Usage: cd <directory_name>\nExample: cd documents",
            "mkdir": "Usage: mkdir <folder_name>\nExample: mkdir new_folder",
            "touch": "Usage: touch <filename>\nExample: touch file.txt",
            "rm": "Usage: rm <file_or_folder>\nExample: rm old_file.txt",
            "fileinfo": "Usage: fileinfo <file_or_folder>\nExample: fileinfo document.pdf",
            "ls": "Usage: ls\nLists all files in current directory",
            "ai": "Usage: ai <question>\nExample: ai What is quantum computing?",
            "voice": "Usage: voice <start/stop/status>\nExample: voice start",
            "speak": "Usage: speak <text>\nExample: speak Hello world",
            "listen": "Usage: listen [timeout]\nExample: listen 10",
        }
        
        help_text = f"Help for '{command_name}':\n"
        help_text += f"Description: {description}\n"
        
        if command_name in usage_examples:
            help_text += f"\n{usage_examples[command_name]}"
        
        return help_text
    
    def get_command_history(self) -> List[str]:
        """Get command history"""
        return self.command_history.copy()
    
    def clear_history(self):
        """Clear command history"""
        self.command_history = []
    
    def get_voice_status(self) -> str:
        """Get voice assistant status"""
        if not self.voice:
            return "Voice assistant not available"
        
        status = "ACTIVE" if self.voice.voice_active else "INACTIVE"
        return f"Voice assistant: {status}"
    
    def quick_voice_command(self):
        """Quick voice command (for hotkey binding)"""
        if not self.voice or not self.voice.voice_enabled:
            return "Voice not available"
        
        print("\n🎤 [Voice] Listening for command (5 seconds)...")
        result = self.voice.listen(5)
        
        if isinstance(result, str) and result not in ["Listening timeout", "Could not understand audio"]:
            # Process with AI
            response = self.ollama.chat(result) if self.ollama else "AI not available"
            self.voice.speak(response[:200])
            return f"Voice command: {result}\nAI: {response}"
        
        return f"Voice result: {result}"
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'voice') and self.voice:
            self.voice.cleanup()


# ==================== ENHANCED AI CORE ====================
class EnhancedAICore(AICore):
    """Enhanced AI core with matrix command processing"""
    
    def __init__(self, filesystem, app_callback=None):
        # Don't call super().__init__ directly - we need to set up differently
        self.filesystem = filesystem
        self.registry = EnhancedCommandRegistry()
        
        # Initialize AI components
        self.ollama = OllamaClient() if OLLAMA_AVAILABLE else None
        
        # Pass app_callback to EnhancedVoiceAssistant
        self.voice = EnhancedVoiceAssistant(self.ollama, app_callback)
        
        self.command_history = []
        self.context = {
            "filesystem": filesystem,
            "ai_core": self
        }
        
        # Store app_callback for use in command processing
        self.app_callback = app_callback
        
        # Start voice command processing thread
        if hasattr(self.voice, 'voice_enabled') and self.voice.voice_enabled:
            self._start_voice_processor()
            print("✅ Enhanced AI Core initialized with Matrix support")
        else:
            print("⚠️  Voice processor not started - voice not available")
    
    def _start_voice_processor(self):
        """Start background thread to process voice commands"""
        def process_voice_commands():
            while True:
                try:
                    # Check for voice commands
                    if self.voice and not self.voice.command_queue.empty():
                        source, command, response = self.voice.command_queue.get()
                        print(f"\n[Voice] Command: {command}")
                        print(f"[Voice] Response: {response[:100]}...")
                
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Voice processor error: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=process_voice_commands, daemon=True)
        thread.start()
    
    def process_command(self, cmd: str) -> Tuple[str, bool, bool]:
        """Enhanced command processing with matrix analysis"""
        cmd = cmd.strip()
        if not cmd:
            return "Please enter a command.", False, False
        
        # Special case for empty command or single ?
        if cmd == "?":
            cmd = "help"
        
        self.command_history.append(cmd)
        
        parts = cmd.split()
        command_name = parts[0].lower()
        args = parts[1:]
        
        # Check for command help (command + ?)
        if command_name.endswith('?'):
            command_name = command_name[:-1]
            return self._get_command_help(command_name), False, False
        
        command = self.registry.get_command(command_name)
        if not command:
            # Try matrix analysis for natural language commands
            matrix = self.voice.generate_matrix(cmd)
            
            if "error" not in matrix and matrix['confidence_score'] >= 0.6 and matrix['executable_command']:
                print(f"🎯 Matrix analysis detected: {matrix['detected_action']}")
                
                if matrix['requires_confirmation']:
                    return f"⚠️ Confirm: {matrix['executable_command']} (Type 'yes' to proceed)", False, False
                
                # Check if this is an AIOS widget command
                if self.voice._is_aios_widget_command(matrix):
                    widget_name = self.voice._extract_widget_name(matrix)
                    if widget_name and self.app_callback:
                        # Use the app_callback to open the widget
                        return f"[WIDGET:{widget_name.upper()}]", False, True
                    else:
                        return "AIOS widget command detected but no app connection.", False, False
                else:
                    # Execute system command
                    result = self.voice._execute_system_command(matrix['executable_command'])
                    return f"✅ Executed via matrix analysis:\n{result}", False, False
            
            # Fall back to AI chat
            if self.ollama:
                response = self.ollama.chat(cmd)
                return response, False, False
            else:
                suggestions = self.registry.get_suggestions(command_name)
                if suggestions:
                    return f"Command not found: {command_name}. Did you mean: {', '.join(suggestions)}?", False, False
                return f"Command not found: {command_name}. Type 'help' for commands.", False, False
        
        try:
            result = command["handler"](args, self.context)
            
            if isinstance(result, tuple):
                if len(result) == 2:
                    response, refresh = result
                    return response, refresh, False
                elif len(result) == 3:
                    response, refresh, special = result
                    return response, refresh, special
            else:
                return result, False, False
        except Exception as e:
            return f"Error: {str(e)}", False, False
    
    def get_voice_status(self) -> str:
        """Get enhanced voice assistant status"""
        if not self.voice:
            return "Voice assistant not available"
        
        status = "ACTIVE" if self.voice.voice_active else "INACTIVE"
        matrix_status = "Matrix: ENABLED"
        return f"Voice assistant: {status}\n{matrix_status}"

# ==================== EXAMPLE COMMANDS & TESTING ====================
EXAMPLE_COMMANDS = [
    "create a new file called notes.txt",
    "go to the documents folder",
    "list all USB devices",
    "show me running processes",
    "create a folder named projects in home directory",
    "delete the file report.pdf",
    "what's my CPU usage right now?",
    "make a new folder for images",
    "read the file config.json",
    "scan for USB peripherals"
]


def test_matrix_generator():
    """Test the matrix generator with example commands"""
    generator = CommandMatrixGenerator()
    
    print("🧪 Testing Command Matrix Generator")
    print("="*60)
    
    for i, command in enumerate(EXAMPLE_COMMANDS, 1):
        print(f"\nTest {i}: {command}")
        print("-"*40)
        
        matrix = generator.generate_matrix(command)
        explanation = generator.explain_matrix(matrix)
        print(explanation)
        
        if matrix['executable_command']:
            print(f"💡 Would execute: {matrix['executable_command']}")
        
        time.sleep(0.5)
    
    print("\n" + "="*60)
    print("✅ Matrix generator test completed")


# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    # Test the matrix generator
    test_matrix_generator()
    
    # Example integration
    print("\n\n🚀 Integrated Example:")
    print("="*60)
    
    # Simulate voice input
    voice_input = "create a new folder called my_project in the home directory"
    
    # Generate matrix
    generator = CommandMatrixGenerator()
    matrix = generator.generate_matrix(voice_input)
    
    print(f"🎤 Voice Input: {voice_input}")
    print(f"⚡ Generated Command: {matrix.get('executable_command', 'None')}")
    print(f"📊 Confidence: {matrix['confidence_score']:.0%}")
    
    if matrix['executable_command']:
        print(f"💻 Would execute: {matrix['executable_command']}")
    
    # Test the enhanced AI core
    print("\n\n🧪 Testing Enhanced AI Core")
    print("="*60)
    
    class DummyFilesystem:
        pass
    
    # Initialize the enhanced AI core
    ai_core = EnhancedAICore(DummyFilesystem())
    
    # Test commands
    test_commands = [
        "help",
        "matrix 'create a new file called test.txt'",
        "analyze 'go to home directory'",
        "suggest 'list'"
    ]
    
    for cmd in test_commands:
        print(f"\nTesting: {cmd}")
        response, _, _ = ai_core.process_command(cmd)
        print(f"Response: {response[:200]}...")
    
    print("\n✅ Enhanced AI Core test completed!")