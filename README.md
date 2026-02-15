# Textbook AI Summarizer & Tutor Roadmap

## Table of Contents
1. [Project Overview](#project-overview)
2. [Goals & Stretch Goals](#goals--stretch-goals)
3. [Architecture Overview](#architecture-overview)
4. [PDF Parsing](#pdf-parsing)
5. [Summarization](#summarization)
6. [Quiz & Flashcard Generation](#quiz--flashcard-generation)
7. [RAG-Based Tutor LLM](#rag-based-tutor-llm)
8. [Flask Web UI](#flask-web-ui)
9. [Text-to-Speech (TTS) / Speech-to-Text (STT)](#text-to-speech-tts--speech-to-text-stt)
10. [Development Notes](#development-notes)
11. [Next Steps](#next-steps)

---

## Project Overview

This project is an end-to-end AI pipeline for processing educational textbooks. The goal is to create a **summarization and tutoring system** that:

- Reads PDFs of textbooks
- Generates detailed summaries for review
- Extracts or generates quiz questions and flashcards
- Supports interactive Q&A via a retrieval-augmented generation (RAG) pipeline
- Optionally provides voice-based interaction using TTS/STT
- Runs on local hardware with potential lightweight deployment on embedded devices

The system is modular, allowing incremental development and experimentation with LLMs, embeddings, and AI tutoring techniques.

---

## Goals & Stretch Goals

**Core Goals:**

- Summarize textbooks by chapter and section
- Keep verbatim quotes for reference
- Extract existing example questions
- Produce structured summaries for later RAG indexing
- Generate quizzes and flashcards automatically

**Stretch Goals:**

- Interactive tutoring with probing questions
- Use LoRA/QLoRA to fine-tune LLM to adopt the tutor persona
- Use LoRA/QLoRA to fine-tune LLM to be better at Summarization
- Use RAG to gain info from the textbook
- Voice-based tutoring using TTS/STT

---

## Architecture Overview

i have a chat where i am starting to have multiple questions per chat. i am splitting that off to another chat. the context is i am learning about AI concepts
I asked it to tell me about RAG
this is it's response:

RAG and How it Fits with Tutoring

RAG = Retrieval-Augmented Generation

Instead of teaching the model new facts via weights, you give it the information at inference time.

Ideal for tutoring with textbooks:

Embed textbook chunks

At runtime, retrieve relevant chunks for the student’s question

Feed them as context to the LLM

This allows small models to answer questions about large textbooks without needing the model to memorize everything.

Pros for tutoring:

Can dynamically use multiple textbooks or updates

Keeps model “lightweight”

Works with smaller VRAM models

Cons:

Model’s behavior/personality still comes from the base model; you can shape style with prompts

💡 Best combination:

Use RAG for knowledge retrieval

Use prompt engineering (or LoRA) for tutor persona

Optional: LoRA to bias model toward being Socratic / explanatory

answer questions i have from there.