# YonEarth Podcast RAG Chatbot Implementation Plan

## Overview
Build a sophisticated RAG (Retrieval-Augmented Generation) chatbot that can answer questions using content from 172 YonEarth podcast episodes while directing users to relevant episodes. **The chatbot will be integrated into the YonEarth WordPress website** as an embedded widget accessible to website visitors.

## Phase 1: Data Preparation & Enhancement

### 1.1 Speaker Diarization for All Episodes
- **Identify episodes without speaker separation** (majority of the 172)
- **Use Whisper + pyannote.audio** to re-process audio for speaker separation
- **Map generic speakers to actual names** using episode metadata and patterns
- **Standardize format**: Use consistent timestamp + speaker name format

### 1.2 Data Enrichment
- **Extract key entities**: Guest names, organizations, topics, locations
- **Create episode summaries** using LLM if not present
- **Build topic taxonomy** from episode content
- **Extract quotable moments** with speaker attribution

## Phase 2: Vector Database Architecture

### 2.1 Multi-Level Chunking Strategy
```python
# Chunk hierarchy:
1. Episode-level chunks (full episode context)
2. Topic-segment chunks (5-10 minute segments)
3. Speaker-turn chunks (individual responses)
4. Semantic chunks (300-500 tokens with overlap)
```

### 2.2 Embedding Strategy
- **Primary embeddings**: OpenAI text-embedding-3-large
- **Hybrid search**: Combine dense vectors with BM25 sparse retrieval
- **Metadata filtering**: Enable filtering by speaker, date, topic

### 2.3 Vector Database Selection
- **Recommended**: Pinecone or Weaviate for production
- **Alternative**: ChromaDB or Qdrant for development
- **Index structure**: Separate indexes for different chunk types

## Phase 3: RAG Pipeline Implementation

### 3.1 Retrieval Strategy
```python
# Multi-stage retrieval:
1. Initial broad search (50-100 chunks)
2. Re-ranking using cross-encoder
3. Diversity filtering (ensure multiple episodes)
4. Context window optimization (8K tokens)
```

### 3.2 Query Enhancement
- **Query expansion**: Add synonyms and related terms
- **Intent classification**: Q&A vs. episode recommendation
- **Temporal awareness**: Handle time-based queries

### 3.3 Response Generation
- **LLM**: GPT-4 or Claude 3 for generation
- **Citation format**: Always include episode number, guest name, timestamp
- **Episode recommendations**: Top 3-5 relevant episodes with reasons

## Phase 4: Advanced Features

### 4.1 Speaker-Aware Responses
- **Quote attribution**: "As [Guest Name] explained in Episode X..."
- **Perspective tracking**: Distinguish host vs. guest viewpoints
- **Expert aggregation**: Synthesize views from multiple guests

### 4.2 Conversation Memory
- **Session management**: Track conversation context
- **Follow-up handling**: Reference previous queries
- **User preferences**: Learn interests over time

### 4.3 Specialized Capabilities
- **Topic deep-dives**: Generate comprehensive topic summaries
- **Guest profiles**: Create expert profiles from appearances
- **Trend analysis**: Track evolving discussions over time

## Phase 5: Technical Implementation

### 5.1 Backend Architecture
```python
# Core components:
- FastAPI web service
- LangChain for RAG orchestration
- Redis for caching
- PostgreSQL for metadata
- Vector DB for embeddings
```

### 5.2 Processing Pipeline
```python
# Ingestion pipeline:
1. Load JSON episodes
2. Process speaker separation
3. Generate embeddings
4. Create metadata indices
5. Build knowledge graph
```

### 5.3 Frontend Development Strategy
- **Phase 1 - Testing Web App**: Simple HTML/CSS/JS interface for development
  - Local development with FastAPI backend
  - Basic chat interface for testing RAG functionality
  - Easy deployment to simple hosting (Vercel, Netlify, VPS)
- **Phase 2 - WordPress Integration**: 
  - Backend API: Hosted separately (cloud/VPS) with CORS enabled
  - WordPress Plugin: Custom plugin for easy integration
  - Embeddable Widget: JavaScript widget that can be added via shortcode
  - WordPress Integration Options:
    - Shortcode: `[yonearth_chatbot]` for pages/posts
    - Widget: Add to sidebars or footer
    - Floating chat button: Site-wide persistent chat

## Phase 6: Optimization & Quality

### 6.1 Retrieval Optimization
- **A/B testing**: Different chunking strategies
- **Relevance tuning**: Adjust similarity thresholds
- **Cache warming**: Pre-compute common queries

### 6.2 Response Quality
- **Hallucination prevention**: Strict source attribution
- **Fact verification**: Cross-reference multiple episodes
- **Answer confidence**: Indicate certainty levels

### 6.3 Performance Metrics
- **Retrieval accuracy**: MRR, NDCG metrics
- **Response quality**: Human evaluation rubric
- **System performance**: Latency, throughput

## Phase 7: WordPress Integration & Deployment

### 7.1 WordPress Plugin Development
- **Admin Interface**: Settings page for API configuration
- **Shortcode System**: `[yonearth_chatbot]` with customizable parameters
- **Widget Support**: WordPress widget for sidebars/footers
- **Theme Integration**: CSS that adapts to active WordPress theme
- **Security**: Nonce validation, sanitized inputs

### 7.2 Deployment Architecture
- **Separated Backend**: API hosted on cloud service (AWS/GCP/DigitalOcean)
- **WordPress Plugin**: Distributed via WordPress.org or private installation
- **CDN Integration**: Static assets cached via WordPress CDN
- **CORS Configuration**: Proper cross-origin setup for security

### 7.3 Monitoring & Analytics
- **WordPress Analytics**: Integration with existing WP analytics
- **Chat Analytics**: Custom dashboard for chat metrics
- **Performance Monitoring**: API response times, error rates
- **User Feedback**: Rating system within chat interface

## Data Analysis Findings

### Current State
- **172 total episodes** with complete transcripts (avg. 38,731 characters each)
- **Mixed transcript formats**: Some with speaker separation (like Episode 170), most without
- **Rich metadata**: Episode descriptions, guest bios, related episodes
- **Speaker patterns identified**: 
  - Format like "5:45 – elizabethmorris" in Episode 170
  - "Aaron Perry" as consistent host
  - Need to process majority of episodes for speaker separation

### Key Insights
1. **Speaker separation is critical** for attribution and context
2. **Episode 170 format** should be the target for all episodes
3. **Existing audio transcription capability** can be leveraged
4. **Rich guest information** enables expert profiling

## Key Design Decisions

1. **Speaker separation is critical** - Invest in processing all episodes with Whisper + pyannote
2. **Hybrid retrieval** - Combine semantic and keyword search
3. **Multi-level chunking** - Capture different granularities (episode, segment, turn, semantic)
4. **Episode attribution** - Always cite sources with episode number, guest, timestamp
5. **Conversation memory** - Maintain context across queries
6. **Expert profiling** - Create knowledge base of guest expertise

## WordPress-Specific Implementation Details

### WordPress Plugin Structure
```
yonearth-chatbot/
├── yonearth-chatbot.php          # Main plugin file
├── admin/
│   ├── admin-settings.php        # Settings page
│   └── admin-styles.css          # Admin CSS
├── public/
│   ├── chatbot-widget.js         # Frontend JavaScript
│   ├── chatbot-styles.css        # Widget CSS
│   └── shortcode-handler.php     # Shortcode processing
├── includes/
│   ├── api-connector.php         # Backend API communication
│   ├── security.php              # Nonce and validation
│   └── widget-class.php          # WordPress widget class
└── assets/
    ├── chat-icon.svg             # Chat button icon
    └── loading-spinner.gif       # Loading animation
```

### Integration Options
1. **Shortcode Integration**: `[yonearth_chatbot height="600px" theme="light"]`
2. **WordPress Widget**: Drag-and-drop in Appearance > Widgets
3. **Floating Chat Button**: Site-wide persistent chat bubble
4. **Page Template**: Dedicated chatbot page template

### WordPress Compatibility
- **WordPress Version**: 5.0+ (Gutenberg compatible)
- **PHP Requirements**: 7.4+ (matches WordPress requirements)
- **Theme Compatibility**: Responsive design adapts to any theme
- **Plugin Conflicts**: Tested with popular plugins (Yoast, WooCommerce, etc.)

## Implementation Priority

### High Priority (MVP - Testing Phase)
1. Process all episodes for speaker separation
2. Implement basic RAG with episode-level chunking  
3. Create simple web app for testing RAG functionality
4. Deploy testing web app to simple hosting (Vercel/Netlify)
5. Add episode recommendation capability
6. Test and iterate on user experience

### Medium Priority (WordPress Integration Phase)
1. Develop WordPress plugin with shortcode support
2. Create WordPress widget version of chat interface  
3. WordPress admin dashboard for analytics
4. Multi-level chunking optimization
5. Speaker-aware responses
6. Guest expertise profiles

### Low Priority (Future Enhancements)
1. Conversation memory across sessions
2. WordPress user integration (logged-in user context)
3. Real-time updates for new episodes
4. Advanced analytics dashboard
5. WooCommerce integration for premium features

## Estimated Timeline
- **Phase 1-2**: 3-4 weeks (data preparation & vector DB setup)
- **Phase 3-4**: 4-6 weeks (core RAG implementation & advanced features)
- **Phase 5-6**: 3-4 weeks (optimization & quality improvements)
- **Phase 7**: 2 weeks (deployment & monitoring)

**Total**: 12-16 weeks for full implementation

## Technical Stack Recommendations

### Core Technologies
- **Vector DB**: Pinecone (production) or ChromaDB (development)
- **Embeddings**: OpenAI text-embedding-3-large
- **LLM**: GPT-4 or Claude 3.5 Sonnet
- **Framework**: LangChain or LlamaIndex
- **Backend**: FastAPI with Python
- **Database**: PostgreSQL for metadata
- **Cache**: Redis for response caching

### Audio Processing
- **Speech Recognition**: OpenAI Whisper (already integrated)
- **Speaker Diarization**: pyannote.audio (already integrated)
- **Audio Processing**: librosa, pydub

### Testing Web App
- **Frontend**: Simple HTML/CSS/JavaScript (no framework dependencies)
- **Styling**: Clean, responsive design with CSS Grid/Flexbox
- **Chat UI**: Real-time chat interface with WebSocket or polling
- **Deployment**: Static hosting (Vercel/Netlify) + API server

### WordPress Integration (Phase 2)
- **WordPress Plugin**: PHP plugin for admin integration
- **Frontend Widget**: Reuse testing web app JavaScript code
- **Styling**: CSS that respects WordPress themes
- **Chat UI**: Same interface as testing app, WordPress-themed
- **WordPress APIs**: Integration with WP REST API if needed

## Next Steps

### Phase 1: Testing Web App (Weeks 1-8)
1. **Week 1-2**: Process all 172 episodes for speaker separation using existing audio transcription pipeline
2. **Week 3-4**: Set up vector database and implement basic chunking
3. **Week 5-6**: Build core RAG pipeline with retrieval and generation
4. **Week 7-8**: Create simple testing web app and deploy to hosting

### Phase 2: WordPress Integration (Weeks 9-12)
5. **Week 9-10**: Develop WordPress plugin and chat widget  
6. **Week 11-12**: WordPress integration testing and optimization
7. **Week 13+**: Deploy to production WordPress site and monitor performance

### Testing Web App Development
1. **Simple HTML/CSS/JS**: Clean chat interface with no framework dependencies
2. **FastAPI Backend**: Python API server for RAG functionality
3. **Local Testing**: Run both frontend and backend locally for development
4. **Simple Deployment**: Frontend to Vercel/Netlify, backend to Railway/Render
5. **User Testing**: Gather feedback before WordPress integration

### WordPress Development Phases (Phase 2)
1. **Plugin Foundation**: Basic WordPress plugin structure with admin settings
2. **Chat Widget**: Reuse testing app JavaScript with WordPress theming
3. **Shortcode System**: Enable `[yonearth_chatbot]` shortcode functionality
4. **Theme Integration**: CSS styling that adapts to WordPress themes
5. **Testing & Deployment**: Cross-browser testing and WordPress site integration

## Success Metrics

### Technical Metrics
- **Retrieval accuracy**: >90% relevant chunks in top-10
- **Response latency**: <3 seconds for complex queries
- **Citation accuracy**: 100% of responses include valid episode references

### User Experience Metrics
- **Answer quality**: 4.5+ stars on 5-point scale
- **Episode discovery**: Users explore 3+ recommended episodes per session
- **Engagement**: 60%+ users ask follow-up questions

### Business Metrics
- **Usage growth**: 20% month-over-month increase
- **Episode engagement**: 25% increase in full episode listens
- **Community building**: Enhanced listener connection to content

This plan leverages the rich YonEarth podcast dataset to create a best-in-class RAG chatbot that not only answers questions but actively guides users to discover relevant episodes, creating a deeper connection with the podcast content and community.