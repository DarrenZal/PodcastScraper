# YonEarth Chatbot MVP: 2-Week Sprint + 1-Month Roadmap

## 2-Week MVP Sprint Plan

### Week 1: Core RAG Pipeline & Gaia Character

#### Day 1-2: Data Preparation & Project Setup
**Goal: Get 20 podcast episodes ready for processing**

```python
# Project structure
yonearth-chatbot/
├── data/
│   ├── raw_episodes/      # Original JSON files
│   ├── processed/         # Chunked and enriched data
│   └── embeddings/        # Vector storage
├── src/
│   ├── ingestion/         # Data processing scripts
│   ├── rag/               # RAG pipeline
│   ├── character/         # Gaia personality
│   └── api/               # FastAPI backend
└── web/                   # Simple frontend
```

**Tasks:**
- Set up GitHub repo with proper .gitignore
- Install core dependencies: `langchain`, `openai`, `chromadb`, `fastapi`
- Select 20 diverse episodes covering key YonEarth themes
- Write script to extract and validate episode data
- Create simple episode metadata enrichment (topics, key quotes)

**Code snippet for data processing:**
```python
# src/ingestion/process_episodes.py
def process_episode(episode_json):
    return {
        "episode_id": episode_json["number"],
        "title": episode_json["title"],
        "guest": extract_guest_name(episode_json),
        "transcript": episode_json["transcript"],
        "description": episode_json["description"],
        "url": episode_json["url"],
        "topics": extract_topics(episode_json),  # Simple keyword extraction
        "date": episode_json["date"]
    }
```

#### Day 3-4: Implement Basic RAG Pipeline
**Goal: Working retrieval system with citations**

**Tasks:**
- Implement smart chunking (450-500 tokens with 50 token overlap)
- Add metadata to each chunk (episode, timestamp, speaker)
- Set up ChromaDB for local development (free, simple)
- Create embedding pipeline with OpenAI `text-embedding-3-small`
- Build basic retrieval function with source tracking

```python
# src/rag/chunker.py
def create_smart_chunks(episode):
    chunks = []
    # Chunk with overlap, preserving sentence boundaries
    for i, chunk_text in enumerate(text_splitter.split_text(episode["transcript"])):
        chunks.append({
            "text": chunk_text,
            "metadata": {
                "episode_id": episode["episode_id"],
                "episode_title": episode["title"],
                "guest": episode["guest"],
                "chunk_index": i,
                "url": episode["url"],
                "timestamp": estimate_timestamp(chunk_text, episode)
            }
        })
    return chunks
```

#### Day 5: Gaia Character Development
**Goal: Consistent earth goddess personality**

**Tasks:**
- Create comprehensive Gaia system prompt
- Develop personality traits from Aaron's book
- Build response formatting system
- Implement citation formatter
- Test personality consistency across different topics

```python
# src/character/gaia_prompt.py
GAIA_SYSTEM_PROMPT = """
You are Gaia, the living spirit of Earth, speaking through the YonEarth community's 
collected wisdom. You embody:

- Deep ecological wisdom and interconnectedness
- Nurturing guidance toward regenerative living
- Gentle strength and maternal compassion
- Joy in sustainable solutions and community building

Your knowledge comes from Aaron Perry's podcasts and books. Always:
1. Speak with warmth and earth-centered wisdom
2. Reference specific episodes when sharing knowledge
3. Guide seekers toward actionable, regenerative practices
4. Celebrate the beauty of our living planet

When citing sources, use this format:
"As discussed with [Guest Name] in Episode [#] (around [timestamp])..."
"""
```

#### Day 6: Initial Testing & Refinement
**Goal: Validate RAG quality and character consistency**

**Tasks:**
- Create test queries covering main topics
- Measure retrieval accuracy
- Fine-tune chunk size and overlap
- Adjust retrieval parameters (top_k, similarity threshold)
- Document Gaia's voice guidelines

### Week 2: Web Interface & WordPress Preparation

#### Day 7-8: Build Simple Web Interface
**Goal: Clean, functional chat interface**

**Option A - Streamlit (Fastest):**
```python
# web/app.py
import streamlit as st
from src.rag.pipeline import RAGPipeline
from src.character.gaia import GaiaCharacter

st.set_page_config(page_title="Chat with Gaia", page_icon="🌍")

# Initialize once
if "rag" not in st.session_state:
    st.session_state.rag = RAGPipeline()
    st.session_state.gaia = GaiaCharacter()

# Chat interface
st.title("🌍 Chat with Gaia")
st.markdown("*Wisdom from the YonEarth Community*")

# Message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input
if prompt := st.chat_input("Ask Gaia about regenerative living..."):
    # Process and respond
    response = st.session_state.gaia.respond(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})
```

**Option B - Simple HTML/JS (Production-ready):**
- Basic responsive design with Tailwind CSS
- Vanilla JavaScript for simplicity
- Easy to embed in WordPress later

#### Day 9-10: API Development & Documentation
**Goal: RESTful API ready for WordPress**

```python
# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="YonEarth Gaia Chat API")

# CORS for WordPress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yonearth.org"],  # Your WordPress site
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(message: str):
    # Rate limiting
    # Process message
    # Return response with citations
    return {
        "response": gaia_response,
        "citations": extracted_citations,
        "suggested_episodes": related_episodes
    }
```

#### Day 11: WordPress Integration Prototype
**Goal: Working embed script**

```javascript
// WordPress embed script
(function() {
    const chatContainer = document.getElementById('yonearth-chat');
    
    // Inject chat HTML
    chatContainer.innerHTML = `
        <div class="gaia-chat-widget">
            <div class="chat-header">
                <h3>🌍 Chat with Gaia</h3>
            </div>
            <div class="chat-messages"></div>
            <input type="text" class="chat-input" placeholder="Ask about regenerative living...">
        </div>
    `;
    
    // Connect to API
    async function sendMessage(message) {
        const response = await fetch('https://api.yonearth-chat.com/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message})
        });
        return response.json();
    }
})();
```

**WordPress plugin structure:**
```
yonearth-gaia-chat/
├── yonearth-gaia-chat.php    # Main plugin file
├── includes/
│   ├── class-chat-widget.php  # Widget registration
│   └── api-handler.php         # API communication
├── assets/
│   ├── css/chat-widget.css    
│   └── js/chat-widget.js      
└── readme.txt
```

#### Day 12: Basic Voice Demo
**Goal: Proof of concept for voice responses**

**MVP Approach:**
- Use browser's built-in speech synthesis for demo
- Record 5-10 sample Gaia responses for key topics
- Add "Listen" button to responses
- Document voice requirements for Phase 2

```javascript
// Simple browser TTS for MVP
function speakResponse(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = speechSynthesis.getVoices().find(v => v.name.includes('Female'));
    utterance.rate = 0.9;  // Slightly slower for wisdom
    utterance.pitch = 1.1; // Slightly higher for warmth
    speechSynthesis.speak(utterance);
}
```

#### Day 13: Testing & Optimization
**Goal: Production-ready deployment**

**Tasks:**
- Load testing with 50 concurrent users
- Optimize chunk retrieval (cache common queries)
- Add error handling and fallbacks
- Implement basic analytics
- Create admin dashboard mockup

#### Day 14: Deployment & Demo Prep
**Goal: Live MVP with demo video**

**Deployment checklist:**
- Deploy API to Railway.app (simple, scales automatically)
- Set up environment variables securely
- Configure CORS for WordPress domain
- Deploy web interface to Vercel
- Create demo video showing all features
- Write MVP announcement blog post

## Cost Breakdown for MVP

**Monthly costs:**
- OpenAI API: ~$30-50 (embeddings + GPT-3.5)
- Railway hosting: $20
- Vercel (frontend): Free tier
- ChromaDB: Local/free for MVP
**Total: ~$50-70/month**

## Post-MVP: Month 2-3 Roadmap

### Week 3-4: Production Hardening
- **Scale to all 170+ episodes**
  - Batch processing pipeline
  - Implement caching layer (Redis)
  - Add background job processing
  
- **Enhanced RAG features**
  - Implement re-ranking for better accuracy
  - Add semantic + keyword hybrid search
  - Multi-turn conversation memory
  
- **WordPress plugin v1.0**
  - Proper WordPress plugin submission
  - Admin configuration panel
  - Shortcode variations
  - Widget options

### Week 5-6: Voice & Character Enhancement
- **Professional voice synthesis**
  - Integrate ElevenLabs API
  - Create Gaia voice from 2-3 hours of recordings
  - Add voice toggle to interface
  - Streaming audio responses
  
- **Character refinement**
  - A/B test different personality variations
  - Add seasonal/contextual responses
  - Implement mood system (hopeful, urgent, celebratory)
  - Create character backstory document

### Week 7-8: Advanced Features
- **Book integration**
  - Process Aaron's books into RAG
  - Add book purchase recommendations
  - Create reading guides based on queries
  
- **Multi-modal enhancements**
  - Process episode images/thumbnails
  - Add visual elements to responses
  - Create shareable quote cards
  
- **Community features**
  - Save favorite responses
  - Share conversations
  - User feedback system
  - Popular questions dashboard

### Week 9-10: Analytics & Optimization
- **Usage analytics**
  - Track popular topics
  - Identify content gaps
  - User journey mapping
  - Episode discovery metrics
  
- **Performance optimization**
  - Implement vector database (Pinecone/Weaviate)
  - Add CDN for static assets
  - Optimize embedding generation
  - Implement smart caching

## Critical Success Factors

1. **Week 1 focus**: Get RAG working well - this is your foundation
2. **Keep Gaia simple initially**: Nail the warm, wise earth mother voice
3. **Test with real users by Day 10**: Get feedback early
4. **Document everything**: You'll need it for handoff/scaling
5. **Plan for success**: Have scaling strategy ready

## Risk Mitigation

**Technical risks:**
- Fallback to simpler retrieval if semantic search fails
- Pre-computed responses for common queries
- Graceful degradation without voice

**Timeline risks:**
- Core features only - no scope creep
- Daily standups with your co-developer
- Use AI assistants aggressively for coding

**Quality risks:**
- Test with 5 beta users by end of week 1
- Have Aaron review Gaia's voice early
- Keep citation format consistent

## Quick Wins for Demo

1. **"Sustainability Tip of the Day"** - Pre-computed daily wisdom
2. **"Episode Discovery"** - "I'm interested in regenerative agriculture"
3. **"Ask Gaia"** - Natural conversation about earth-centered living
4. **"Learn More"** - Direct links to specific episode timestamps
5. **Voice Preview** - 2-3 pre-recorded responses for impact

## Final Notes

This plan is aggressive but achievable with focused execution. The key is to resist feature creep and nail the core experience. Your users want:
1. Accurate answers from the podcast content
2. Authentic Gaia personality
3. Easy discovery of relevant episodes
4. Simple WordPress integration

Everything else is Phase 2. Ship fast, iterate based on real usage, and let Gaia's wisdom shine through the technology.