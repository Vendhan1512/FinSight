# FinSight NLP Methodology

## 1. Document Processing
- Text is normalized (HTML stripped, unicode standardized).
- Stop words and standard financial disclaimers are scrubbed to reduce noise.

## 2. Entity Extraction
- Utilizes Named Entity Recognition (NER) to map articles to specific tickers and companies.
- Resolves aliases (e.g., "Apple", "AAPL", "Apple Inc.") to a single canonical `entity_id`.

## 3. Sentiment Analysis
- Uses financial-specific sentiment dictionaries (e.g., Loughran-McDonald) or specialized financial LLM embeddings (FinBERT).
- Avoids generic sentiment analyzers (like VADER) which misclassify financial terms (e.g., "liability", "tax", "vice").

## 4. Topic Extraction
- Generates topic clusters using TF-IDF or LDA to classify articles into broader themes (e.g., "M&A", "Earnings", "Regulatory").
