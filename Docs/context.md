# Project Context: AI-Powered Restaurant Recommendation System (Zomato Use Case)

## Overview

Build an AI-powered restaurant recommendation service inspired by Zomato. The system combines structured restaurant data with a Large Language Model (LLM) to deliver personalized, human-like restaurant suggestions based on user preferences.

## Objective

Design and implement an application that:

1. Accepts user preferences (location, budget, cuisine, ratings, and more)
2. Uses a real-world restaurant dataset
3. Leverages an LLM to generate personalized, human-like recommendations
4. Displays clear, useful results to the user

## Data Source

| Item | Detail |
|------|--------|
| **Dataset** | Zomato Restaurant Recommendation |
| **Source** | [Hugging Face — ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) |
| **Key fields** | Restaurant name, location, cuisine, cost, rating, and related metadata |

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract relevant fields: restaurant name, location, cuisine, cost, rating, etc.

### 2. User Input

Collect the following preferences from the user:

| Preference | Examples |
|------------|----------|
| **Location** | Delhi, Bangalore |
| **Budget** | Low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional preferences** | Family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter and prepare restaurant data based on user input
- Pass structured, filtered results into an LLM prompt
- Design a prompt that helps the LLM reason over and rank options

### 4. Recommendation Engine (LLM)

The LLM should:

- **Rank** restaurants by fit to user preferences
- **Explain** why each recommendation matches the user
- **Optionally summarize** the overall set of choices

### 5. Output Display

Present top recommendations in a user-friendly format. Note: Restaurant images are excluded (only the text name and other details are displayed to keep the UI lightweight and avoid duplicate generic images). Each result includes:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation

## Architecture Summary

```
User Preferences
      ↓
Data Ingestion (Hugging Face Zomato dataset)
      ↓
Filter & Prepare (structured data matching user input)
      ↓
LLM Prompt (rank, explain, summarize)
      ↓
Formatted Recommendations (name, cuisine, rating, cost, explanation)
```

## Key Technical Considerations

- **Hybrid approach**: Structured filtering first, then LLM for ranking and natural-language explanations
- **Prompt design**: Critical for quality — the LLM must reason over filtered candidates, not raw full dataset
- **User experience**: Output must be readable and actionable, not just raw model text
- **Dataset preprocessing**: Normalize location, cuisine, cost, and rating fields for reliable filtering

## Success Criteria

- [ ] Dataset loads and preprocesses correctly from Hugging Face
- [ ] User can specify location, budget, cuisine, minimum rating, and extra preferences
- [ ] System filters restaurants before sending context to the LLM
- [ ] LLM returns ranked recommendations with clear explanations
- [ ] Results are displayed in a clean, user-friendly format (without redundant/generic restaurant images)
