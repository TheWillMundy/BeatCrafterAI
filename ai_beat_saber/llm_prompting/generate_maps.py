"""
Generate Beat Saber maps using LLM prompting.
"""

import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MapGenerator:
    """Generate Beat Saber maps using LLM."""
    
    def __init__(self, formatted_data_dir: Path, output_dir: Path, api_key: Optional[str] = None):
        """Initialize the generator.
        
        Args:
            formatted_data_dir: Directory containing formatted training data
            output_dir: Directory to save generated maps
            api_key: OpenAI API key (optional, will use environment variable if not provided)
            
        Raises:
            ValueError: If no API key is provided and OPENAI_API_KEY is not set in environment
        """
        self.formatted_data_dir = Path(formatted_data_dir)
        self.output_dir = Path(output_dir)
        self.maps_dir = self.output_dir / "new_maps"
        self.logs_dir = self.output_dir / "logs"
        
        # Create necessary directories
        self.maps_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Get API key from args or environment
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Either pass it to the constructor or "
                "set the OPENAI_API_KEY environment variable in your .env file"
            )
        
        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}")
        
        # Load and validate training data
        self._load_training_data()
    
    def _load_training_data(self) -> None:
        """Load and validate the training dataset."""
        self.training_data = []
        
        # Load all JSON files from the formatted directory
        json_files = list(self.formatted_data_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} training examples")
        
        for json_file in json_files:
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    # Basic validation - check for required fields in pruned data
                    if all(k in data for k in ['info', 'difficulties', 'midi_data']):
                        self.training_data.append(data)
                    else:
                        logger.warning(f"Skipping {json_file.name} - missing required fields")
            except Exception as e:
                logger.error(f"Error loading {json_file.name}: {str(e)}")
    
    def _create_prompt(self, midi_data: str) -> str:
        """Create the prompt for map generation."""
        # Select a subset of training examples (limit to 5)
        examples = self.training_data[:3]
        
        prompt = (
            "You are an expert Beat Saber map creator. Your task is to generate a Hard difficulty map "
            "for a new song based on its MIDI representation.\n\n"
            
            "Important timing instructions:\n"
            "1. Each note in the MIDI data includes its beat position (Beat: X.XXX).\n"
            "2. Use these beat positions directly for the '_time' value in the map.\n"
            "3. The beat position represents exactly when the note should be hit in the song.\n"
            "4. Maintain the rhythm by placing notes at their exact beat positions.\n"
            "5. IMPORTANT: Generate notes for the ENTIRE length of the song - from the first beat to the last beat in the MIDI data.\n"
            "6. For Hard difficulty:\n"
            "   - Use a mix of quarter and half beats\n"
            "   - Include both main melody and supporting notes\n"
            "   - Create patterns that are challenging but not overwhelming\n"
            "   - Aim for at least 100 notes in a typical song\n\n"
            
            "Pattern guidelines:\n"
            "1. Alternate between red (0) and blue (1) notes for better flow\n"
            "2. Use cut directions that flow naturally with the music\n"
            "3. Place notes in a way that creates comfortable arm movements\n"
            "4. Avoid awkward patterns or impossible cuts\n"
            "5. Match the intensity of patterns to the song's energy\n"
            "6. Ensure consistent note density throughout the entire song\n\n"
            
            "Here are some example Hard difficulty Beat Saber maps with their MIDI data for reference:\n"
        )
        
        # Add examples
        for i, example in enumerate(examples):
            prompt += f"\nExample Map {i+1}:\n"
            prompt += f"MIDI:\n{example['midi_data']}\n"
            prompt += "Map Data:\n"
            # Only show Hard difficulty data
            for diff_name, diff_data in example['difficulties'].items():
                if "hard" in diff_name.lower():
                    prompt += json.dumps(diff_data) + "\n"
        
        # Add the new song's MIDI data
        prompt += (
            f"\nNow, please generate a Hard difficulty map for this new song with the following MIDI data.\n"
            f"Use the beat positions provided in the MIDI data for precise note timing:\n\n"
            f"{midi_data}\n"
        )

        # Remove all prompt newlines
        prompt = prompt.replace("\n", "")
        
        return prompt
    
    def _generate_maps_with_openai(self, midi_data: str, request_id: str) -> Dict[str, Any]:
        """Generate maps using OpenAI's function calling.
        
        Args:
            midi_data: Text representation of the MIDI file
            request_id: Unique identifier for this generation request
            
        Returns:
            Generated map data for Hard difficulty
            
        Raises:
            OpenAIError: If there's an error calling the OpenAI API
            ValueError: If the response format is invalid
        """
        # Create debug log file
        debug_log_file = self.logs_dir / f"debug_{request_id}.log"
        with open(debug_log_file, 'w') as f:
            f.write(f"=== Debug Log for Request {request_id} ===\n\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("\n=== Input MIDI Data ===\n")
            f.write(midi_data[:1000] + "...\n" if len(midi_data) > 1000 else midi_data)
        
        prompt = self._create_prompt(midi_data)
        
        # Log the prompt
        with open(debug_log_file, 'a') as f:
            f.write("\n=== Generated Prompt ===\n")
            f.write(prompt[:2000] + "...\n" if len(prompt) > 2000 else prompt)
            
        # Save full prompt to markdown file for inspection
        prompt_file = self.logs_dir / f"prompt_{request_id}.md"
        with open(prompt_file, 'w') as f:
            f.write("# Beat Saber Map Generation Prompt\n\n")
            f.write("## System Message\n")
            f.write("```\nYou are an expert Beat Saber map creator. Generate a Hard difficulty map based on MIDI data.\n```\n\n")
            f.write("## User Message\n")
            f.write("```\n")
            f.write(prompt)
            f.write("\n```\n")
            
        print(f"\nFull prompt saved to: {prompt_file}")
        
        # Define the tool schema for map generation
        tools = [{
            "type": "function",
            "function": {
                "name": "create_beat_saber_map",
                "description": (
                    "Create a Hard difficulty Beat Saber map based on MIDI data. "
                    "Convert MIDI timings (in seconds) to beat positions using: beats = seconds * (BPM / 60). "
                    "Place notes at their corresponding beat positions to match the song's rhythm."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "_notes": {
                            "type": "array",
                            "description": "Array of note objects for the map (minimum 20 notes for Hard difficulty)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "_time": {"type": "number", "description": "Time in beats when the note appears"},
                                    "_lineIndex": {"type": "integer", "description": "Horizontal position (0-3)"},
                                    "_lineLayer": {"type": "integer", "description": "Vertical position (0-2)"},
                                    "_type": {"type": "integer", "description": "Note type (0=red, 1=blue)"},
                                    "_cutDirection": {"type": "integer", "description": "Direction to cut (0-8)"}
                                },
                                "required": ["_time", "_lineIndex", "_lineLayer", "_type", "_cutDirection"]
                            },
                            "minItems": 20
                        },
                        "_obstacles": {
                            "type": "array",
                            "description": "Array of obstacle objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "_time": {"type": "number", "description": "Time in beats when the obstacle appears"},
                                    "_lineIndex": {"type": "integer", "description": "Starting horizontal position (0-3)"},
                                    "_type": {"type": "integer", "description": "Obstacle type (0=full height, 1=crouch)"},
                                    "_duration": {"type": "number", "description": "Duration in beats"},
                                    "_width": {"type": "integer", "description": "Width of the obstacle (1-4)"},
                                    "_lineLayer": {"type": "integer", "description": "Starting vertical position (0-2)"}
                                },
                                "required": ["_time", "_lineIndex", "_type", "_duration", "_width", "_lineLayer"]
                            },
                            "default": []
                        },
                        "_events": {
                            "type": "array",
                            "description": "Array of event objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "_time": {"type": "number", "description": "Time in beats when the event occurs"},
                                    "_type": {"type": "integer", "description": "Event type (0-15)"},
                                    "_value": {"type": "integer", "description": "Event value (0-7)"}
                                },
                                "required": ["_time", "_type", "_value"]
                            },
                            "default": []
                        }
                    },
                    "required": ["_notes", "_obstacles", "_events"]
                }
            }
        }]
        
        try:
            print(f"\n=== Making OpenAI API Call for Request {request_id} ===")
            print("Model: gpt-4o-2024-11-20")
            print("Tools configured: create_beat_saber_map")
            print("\n=== Prompt Preview ===")
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-11-20",
                # model="o1-2024-12-17",
                messages=[
                    {"role": "developer", "content": "You are an expert Beat Saber map creator. Generate a Hard difficulty map based on MIDI data."},
                    {"role": "user", "content": prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "create_beat_saber_map"}}
            )
            
            print("\n=== Received OpenAI Response ===")
            print(f"Response status: Success")
            print(f"Number of choices: {len(response.choices)}")
            
            # Log the raw response
            with open(debug_log_file, 'a') as f:
                f.write("\n=== Raw OpenAI Response ===\n")
                f.write(str(response))
            
            # Parse the response
            message = response.choices[0].message
            if message.tool_calls and message.tool_calls[0].function:
                map_data = json.loads(message.tool_calls[0].function.arguments)
                
                print("\n=== Parsed Map Data ===")
                print(f"Number of notes: {len(map_data.get('_notes', []))}")
                
                # Log the parsed data
                with open(debug_log_file, 'a') as f:
                    f.write("\n=== Parsed Map Data ===\n")
                    f.write(json.dumps(map_data, indent=2))
                
                # Log the response
                log_file = self.logs_dir / f"{request_id}.json"
                with open(log_file, 'w') as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "request_id": request_id,
                        "prompt": prompt,
                        "response": map_data
                    }, f, indent=2)
                
                print(f"\n=== Logs saved to: ===")
                print(f"Debug log: {debug_log_file}")
                print(f"Response log: {log_file}")
                
                return map_data
            else:
                error_msg = "No tool call in response"
                print(f"\n=== Error: {error_msg} ===")
                with open(debug_log_file, 'a') as f:
                    f.write(f"\n=== Error: {error_msg} ===\n")
                raise ValueError(error_msg)
                
        except OpenAIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            print(f"\n=== Error: {error_msg} ===")
            with open(debug_log_file, 'a') as f:
                f.write(f"\n=== Error: {error_msg} ===\n")
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Error generating maps: {str(e)}"
            print(f"\n=== Error: {error_msg} ===")
            with open(debug_log_file, 'a') as f:
                f.write(f"\n=== Error: {error_msg} ===\n")
            logger.error(error_msg)
            raise
    
    def generate_map(self, midi_text: str, difficulty: str = "Hard") -> Dict[str, Any]:
        """Generate a map for a given MIDI text representation.
        
        Args:
            midi_text: Text representation of the MIDI data
            difficulty: Desired difficulty level (defaults to Hard)
            
        Returns:
            Generated map data
            
        Raises:
            ValueError: If the difficulty level is not Hard
            OpenAIError: If there's an error calling the OpenAI API
        """
        if difficulty.lower() != "hard":
            raise ValueError("Only Hard difficulty is supported")
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Generate map
        return self._generate_maps_with_openai(midi_text, request_id)
    
    def generate_full_set(self, midi_text: str, song_name: str) -> List[Dict[str, Any]]:
        """Generate a full set of difficulties for a MIDI text representation.
        
        Args:
            midi_text: Text representation of the MIDI data
            song_name: Name of the song (used for file naming)
            
        Returns:
            List of generated maps at different difficulties
            
        Raises:
            OpenAIError: If there's an error calling the OpenAI API
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Generate all maps
        maps_data = self._generate_maps_with_openai(midi_text, request_id)
        
        # Save maps to output directory
        output_path = self.maps_dir / song_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create info.dat
        info_data = {
            "_songName": song_name,
            "_songSubName": "",
            "_songAuthorName": "AI Generated",
            "_levelAuthorName": "AI Beat Saber",
            "_beatsPerMinute": 120,  # This should be extracted from MIDI text
            "_shuffle": 0,
            "_shufflePeriod": 0.5,
            "_previewStartTime": 12,
            "_previewDuration": 10,
            "_songFilename": "song.egg",
            "_coverImageFilename": "cover.jpg",
            "_environmentName": "DefaultEnvironment",
            "_difficultyBeatmapSets": [{
                "_beatmapCharacteristicName": "Standard",
                "_difficultyBeatmaps": []
            }]
        }
        
        # Add each difficulty
        difficulty_files = []
        for diff_name, diff_data in maps_data.items():
            # Save difficulty file
            diff_filename = f"{diff_name.capitalize()}Standard.dat"
            diff_path = output_path / diff_filename
            with open(diff_path, 'w') as f:
                json.dump(diff_data, f, indent=2)
            
            # Add to info.dat
            info_data["_difficultyBeatmapSets"][0]["_difficultyBeatmaps"].append({
                "_difficulty": diff_name.capitalize(),
                "_difficultyRank": {"easy": 1, "normal": 3, "expert": 7}[diff_name],
                "_beatmapFilename": diff_filename,
                "_noteJumpMovementSpeed": {"easy": 10, "normal": 13, "expert": 16}[diff_name],
                "_noteJumpStartBeatOffset": 0
            })
            
            difficulty_files.append({"name": diff_name, "data": diff_data})
        
        # Save info.dat
        with open(output_path / "info.dat", 'w') as f:
            json.dump(info_data, f, indent=2)
        
        return difficulty_files 