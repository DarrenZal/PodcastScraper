# YonEarth Chatbot MVP: Revised 2-Week Sprint + 1-Month Roadmap

## Tech Stack & Cost Analysis

### Primary Recommendations with Alternatives

| Component | Primary Choice | Monthly Cost | Alternative | Alt. Cost | Why Primary? |
|-----------|---------------|--------------|-------------|-----------|--------------|
| **LLM API** | OpenAI GPT-3.5-turbo | $15-25 | Anthropic Claude 3 Haiku | $20-35 | Proven reliability, great LangChain support |
| **Embeddings** | OpenAI text-embedding-3-small | $5-10 | Cohere embed-english-v3.0 | $8-15 | Same provider simplicity, excellent quality |
| **Vector DB** | Pinecone (free tier) | $0 | Supabase Vector | $0 | Purpose-built, generous free tier |
| **Backend Host** | Render.com | $7 | Fly.io | $0-5 | Client-friendly dashboard, easy deploys |
| **Frontend Host** | Vercel | $0 | Netlify | $0 | Best Next.js support if you upgrade later |
| **Voice (Phase 2)** | ElevenLabs | $5 | PlayHT | $9 | Most natural voice cloning |

**Total Monthly Cost: $27-42** (vs. original $50-70)

### When to Consider Alternatives

- **Choose Claude 3 Haiku** if: Gaia's personality needs more nuance and warmth (test both in Week 1)
- **Choose Supabase Vector** if: You need PostgreSQL for other features later
- **Choose Fly.io** if: You have Docker experience and want maximum cost savings

## Revised 2-Week MVP Sprint Plan

### Week 1: Core RAG Pipeline & Gaia Character

#### Day 1-2: Data Preparation & Project Setup
**Goal: Get 20 podcast episodes ready for processing**

```python
# Revised project structure with cloud services
yonearth-chatbot/
├── data/
│   ├── raw_episodes/      # Original JSON files
│   ├── processed/         # Chunked and enriched data
│   └── metadata/          # Episode metadata cache
├── src/
│   ├── ingestion/         # Data processing scripts
│   ├── rag/               # RAG pipeline with Pinecone
│   ├── character/         # Gaia personality
│   ├── api/               # FastAPI backend
│   └── config/            # Environment configs
├── web/                   # Simple frontend
└── deploy/
    ├── render.yaml        # Render blueprint
    └── .env.example       # Environment template
```

**Updated setup tasks:**
- Create accounts: OpenAI, Pinecone (free), Render, Vercel
- Install dependencies: 
  ```bash
  pip install langchain openai pinecone-client fastapi uvicorn python-dotenv
  ```
- Configure Pinecone:
  ```python
  # src/config/pinecone_setup.py
  import pinecone
  
  pinecone.init(
      api_key=os.getenv("PINECONE_API_KEY"),
      environment="gcp-starter"  # Free tier environment
  )
  
  # Create index if not exists
  if "yonearth-episodes" not in pinecone.list_indexes():
      pinecone.create_index(
          "yonearth-episodes",
          dimension=1536,  # OpenAI embedding dimension
          metric="cosine",
          pod_type="starter"
      )
  ```

#### Day 3-4: Implement Cloud-Based RAG Pipeline
**Goal: Working retrieval system with Pinecone**

```python
# src/rag/vectorstore.py
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
import pinecone

class YonEarthVectorStore:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment="gcp-starter"
        )
        
        self.index = pinecone.Index("yonearth-episodes")
        self.vectorstore = Pinecone(self.index, self.embeddings, "text")
    
    def add_documents(self, documents):
        # Batch upload to Pinecone
        return self.vectorstore.add_documents(documents)
    
    def similarity_search(self, query, k=5):
        return self.vectorstore.similarity_search_with_score(query, k=k)
```

#### Day 5: Enhanced Gaia Character Development
**Goal: Consistent earth goddess personality with A/B testing**

```python
# src/character/gaia_personalities.py
# Test two personality variations to find the best voice

GAIA_WARM_MOTHER = """
You are Gaia, the nurturing spirit of Earth, speaking through the YonEarth community's 
collected wisdom. Your voice is warm, maternal, and deeply compassionate...
[Personality A - more nurturing]
"""

GAIA_WISE_GUIDE = """
You are Gaia, the ancient wisdom of Earth itself, channeling insights through the 
YonEarth community's knowledge. Your voice carries timeless wisdom...
[Personality B - more sage-like]
"""

# src/character/gaia.py
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory

class GaiaCharacter:
    def __init__(self, personality_variant="warm_mother"):
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,  # Balanced creativity
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Optional: Test Claude for better personality
        # self.llm = ChatAnthropic(model="claude-3-haiku-20240307")
        
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=1000,
            return_messages=True
        )
```

### Week 2: Web Interface & Production Deployment

#### Day 7-8: Build Production-Ready Web Interface
**Goal: Clean, deployable chat interface**

**Recommended Approach - FastAPI + Static Frontend:**

```python
# src/api/main.py - Enhanced with production features
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import redis
from typing import Optional

app = FastAPI(title="YonEarth Gaia Chat API")

# Redis for caching (Render provides Redis)
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yonearth.org", "*.yonearth.org", "localhost"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yonearth.org"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def chat(message: str, session_id: Optional[str] = None):
    # Check cache first
    cache_key = f"response:{hash(message)}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Process with Gaia
    response = await process_with_gaia(message, session_id)
    
    # Cache common queries for 1 hour
    redis_client.setex(cache_key, 3600, json.dumps(response))
    
    return response
```

#### Day 9-10: Render Deployment Configuration
**Goal: One-click deployment for client**

```yaml
# render.yaml - Blueprint for easy deployment
services:
  - type: web
    name: yonearth-gaia-chat
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /health
    envVars:
      - key: OPENAI_API_KEY
        sync: false  # Client enters their own
      - key: PINECONE_API_KEY
        sync: false
      - key: PINECONE_ENVIRONMENT
        value: gcp-starter
      - key: REDIS_URL
        fromService:
          name: yonearth-redis
          type: redis
          property: connectionString

  - type: redis
    name: yonearth-redis
    plan: starter  # $7/month includes Redis
```

#### Day 11: WordPress Integration with Options
**Goal: Flexible WordPress integration**

```php
<?php
/**
 * Plugin Name: YonEarth Gaia Chat
 * Description: Chat with Gaia, the spirit of Earth
 * Version: 1.0
 */

// Admin settings page for API configuration
add_action('admin_menu', 'yonearth_chat_menu');
function yonearth_chat_menu() {
    add_options_page(
        'YonEarth Chat Settings',
        'YonEarth Chat',
        'manage_options',
        'yonearth-chat',
        'yonearth_chat_settings_page'
    );
}

// Shortcode for embedding
add_shortcode('yonearth_chat', 'yonearth_chat_shortcode');
function yonearth_chat_shortcode($atts) {
    $atts = shortcode_atts(array(
        'height' => '500px',
        'width' => '100%',
        'theme' => 'earth'  // earth, sky, forest themes
    ), $atts);
    
    $api_url = get_option('yonearth_api_url', 'https://yonearth-gaia-chat.onrender.com');
    
    return sprintf(
        '<div id="yonearth-chat" data-api="%s" data-theme="%s" style="height:%s;width:%s;"></div>
        <script src="%s/wp-content/plugins/yonearth-gaia-chat/assets/chat-widget.js"></script>',
        esc_attr($api_url),
        esc_attr($atts['theme']),
        esc_attr($atts['height']),
        esc_attr($atts['width']),
        plugins_url()
    );
}
```

#### Day 12: Voice Demo with Cost-Effective Approach
**Goal: Voice proof-of-concept**

```javascript
// Option 1: Browser TTS for MVP (Free)
const gaiaVoice = {
    speak: function(text) {
        const utterance = new SpeechSynthesisUtterance(text);
        const voices = speechSynthesis.getVoices();
        
        // Find best voice for Gaia
        utterance.voice = voices.find(v => 
            v.name.includes('Female') && 
            v.lang.includes('en')
        ) || voices[0];
        
        utterance.rate = 0.9;
        utterance.pitch = 1.1;
        speechSynthesis.speak(utterance);
    }
};

// Option 2: Pre-recorded samples for demo
// Record 10 common responses with ElevenLabs ($5 one-time)
```

#### Day 13-14: Production Testing & Launch
**Goal: Bulletproof deployment**

```python
# tests/test_production.py
import pytest
from locust import HttpUser, task, between

class YonEarthUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def chat_with_gaia(self):
        self.client.post("/chat", json={
            "message": "Tell me about regenerative agriculture"
        })

# Run: locust -f tests/test_production.py --host=https://your-api.onrender.com
```

## Post-MVP Roadmap: Enhanced Features

### Month 2: Scaling & Enhancement

**Week 3-4: Scale to Full Content**
- Process all 170+ episodes (Pinecone free tier handles 100K vectors)
- Implement semantic caching with Redis
- Add episode recommendation engine
- Cost impact: +$15/month for more OpenAI calls

**Week 5-6: Voice & Advanced Features**
- Integrate ElevenLabs for Gaia voice ($5/month starter)
- Add conversation export/sharing
- Implement topic clustering visualization
- A/B test personality variants at scale

### Month 3: Enterprise Features

**Week 7-8: Advanced Integrations**
```python
# Advanced RAG with re-ranking
from sentence_transformers import CrossEncoder

class AdvancedRAG:
    def __init__(self):
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
    def retrieve_and_rerank(self, query, k=20, top_n=5):
        # Get more candidates
        candidates = self.vectorstore.similarity_search(query, k=k)
        
        # Re-rank for better relevance
        pairs = [[query, doc.page_content] for doc in candidates]
        scores = self.reranker.predict(pairs)
        
        # Return top N
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_n]
```

## Critical Success Metrics

1. **Response latency**: < 2 seconds (achieved with caching)
2. **Citation accuracy**: > 95% correct episode references
3. **Monthly cost**: < $50 predictable pricing
4. **Uptime**: 99.9% with Render's infrastructure
5. **User satisfaction**: > 80% helpful ratings

## Risk Mitigation Updates

**Cost overruns:**
- Implement spending alerts in OpenAI dashboard
- Use Redis caching aggressively
- Set up daily cost monitoring

**Technical failures:**
- Render provides automatic rollbacks
- Keep ChromaDB local backup option
- Implement circuit breaker pattern

**Client accessibility:**
- Render dashboard is non-technical friendly
- Create video walkthrough for common tasks
- Document environment variable setup clearly

## Quick Start Checklist

1. **Sign up for services** (30 minutes):
   - [ ] OpenAI API key
   - [ ] Pinecone free account
   - [ ] Render account
   - [ ] Vercel account

2. **Clone and configure** (20 minutes):
   ```bash
   git clone https://github.com/yonearth/gaia-chat
   cp .env.example .env
   # Add your API keys
   ```

3. **Deploy to Render** (10 minutes):
   - Connect GitHub repo
   - Use render.yaml blueprint
   - Add environment variables

4. **Test the deployment** (20 minutes):
   - Run included test suite
   - Try sample queries
   - Check WordPress embed
