## 1. Project Overview

### 1.1. Vision
The AI Beat Saber Map Generator aims to automate the process of downloading and prepping Beat Saber maps, then use a Large Language Model (LLM) to create new Beat Saber maps. Our pipeline handles everything from bulk data acquisition to final data packaging for training or inference.

### 1.2. Core Features
1. **Bulk Download of Maps**  
   - Scrape Beatsaver.com for “Ranked” or “Highest-rated” maps.  
   - Store them locally and avoid re-downloading duplicates.

2. **Automatic Extraction**  
   - Unzip each downloaded map’s contents and store them in a structured directory.  
   - Collect .dat files (map difficulties), audio, metadata, etc.

3. **Audio → MIDI Conversion**  
   - Convert various audio formats (egg, ogg, mp3, etc.) to MIDI for use in an LLM workflow.  
   - Leverage librosa and pretty_midi to detect pitch events.

4. **YouTube Integration**  
   - Accept YouTube links to fetch new audio.  
   - Convert and process user-provided songs into the same format (including MIDI).

5. **Data Formatting & Packaging**  
   - Consolidate beats, notes, audio metadata, and difficulties into a consistent JSON or text-based structure.  
   - Ensure easy ingestion by an LLM for future training or prompt-based generation.

6. **Map Generation via LLM**  
   - Prompt an LLM with known map data plus MIDI.  
   - Request new difficulties (e.g., Hard, Expert).  
   - Export the LLM output to valid Beat Saber .dat files.

### 1.3. Implementation Summary
- **Scrape & Download**: Use async Python HTTP libraries and paging for map bulk download.  
- **Extraction**: Parse .zip archives to retrieve key files.  
- **Conversion**: Transform audio into MIDI using pitch-tracking.  
- **Formatting**: Convert extracted data + MIDI into text-based training data.  
- **LLM Generation**: Provide examples plus a new MIDI, then parse the response as new .dat files.  

### 1.4. Current Status
- ♻ Bulk download & extraction stable.  
- ♻ Audio → MIDI conversion working.  
- ♻ YouTube integration built-in.  
- ♻ Data packaging final.  
- ⚠ LLM-based generation tested in a minimal capacity.  
- 🚀 Ready for expansion, community input, and advanced LLM training.

### 1.5. Next Steps
- Increase test coverage for LLM-based map generation.  
- Improve audio → MIDI accuracy and subsequent note alignment.  
- Handle advanced user preferences (custom difficulties, advanced patterns).  
- Further optimize for large-scale data (automated chunking and token management).

### 1.6. Risk Considerations
- Conversion quality remains dependent on pitch detection success.  
- Large-scale LLM prompts may exceed token limits.  
- Must respect licensing and distribution rules for any third-party content.